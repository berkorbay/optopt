"""Diagnosis first move (D-004 next step): predict the best static SCIP setting from instance features at t = 0.

Train: `diag_train` runs (6 static settings x 60 ML4CO *training* instances, 120 s, seed 0).
Predict: the 30 held-out ML4CO instances (validation split) of `pilot_e2` (all 6 static settings + agents recorded there, 2 seeds).
Policies scored on the test runs (exact, no extra run needed for a static choice):
  default, best fixed (train, all families), family-majority (best setting per family on train),
  LightGBM (per-setting cost regressors on the 62 static features), oracle (best static per (instance, seed)),
  bandit (10 s / 5 s), diagnose-then-bandit (if run).
Writes datasets/diag_pred.json ({instance: setting}) and datasets/diag_results.json.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from optopt.paths import WORK as ROOT  # the workspace (cwd or $OPTOPT_HOME)
from optopt.analysis.build_runs import stem  # noqa: E402
from optopt.analysis.metrics import primal_dual_integral, primal_integral  # noqa: E402
from optopt.analysis.stats import by_instance  # noqa: E402

S6 = ["D", "NOC", "PSC", "INF", "HOFF", "HEU"]
T = 120


def costs(set_name, metric):
    runs = {}
    for f in (ROOT / "traces/raw" / set_name).glob("*.json"):
        t = json.loads(f.read_text())
        if "instance" in t:
            runs[(stem(t["instance"]), t["strategy"], t["seed"])] = t
    best = {}
    for (n, _, _), t in runs.items():
        for e in t.get("events", []):
            p = e.get("primal")
            if p is not None and (n not in best or p < best[n]):
                best[n] = p
    rows = []
    for (n, a, s), t in runs.items():
        arm = {"A:default": "D"}.get(a, a.replace("C:", ""))
        c = 1.0 if t.get("error") else (primal_integral(t, best.get(n), T) if metric == "P" else primal_dual_integral(t, T))
        rows.append(dict(name=n, arm=arm, seed=s, c=c))
    return pd.DataFrame(rows)


def main():
    import lightgbm as lgb
    F = pd.read_parquet(ROOT / "datasets/features.parquet").assign(name=lambda d: d["instance"].map(stem)).set_index("name")
    fcols = [c for c in F.columns if c not in ("instance", "set", "split", "feat_time") and F[c].dtype.kind in "fi"]
    out = {}
    pred_P = None
    for metric in ("P", "PDI"):
        tr = costs("diag_train", metric).pivot_table(index="name", columns="arm", values="c").reindex(columns=S6).dropna()
        tr = tr.loc[tr.index.intersection(F.index)]
        fam = lambda idx: pd.Series(["item" if n.startswith("item") else "load" for n in idx], index=idx)  # noqa: E731
        X = F.loc[tr.index, fcols].to_numpy(float)
        models = []
        for j, s in enumerate(S6):
            m = lgb.LGBMRegressor(n_estimators=200, learning_rate=0.05, num_leaves=7, min_child_samples=4, verbose=-1,
                                  random_state=j, n_jobs=1)
            m.fit(X, tr[s].to_numpy())
            models.append(m)
        best_fixed = tr.mean().idxmin()
        fam_major = {f_: tr[fam(tr.index) == f_].mean().idxmin() for f_ in ("item", "load")}
        te_all = costs("pilot_e2", metric)
        te = te_all[te_all.arm.isin(S6)].pivot_table(index=["name", "seed"], columns="arm", values="c").reindex(columns=S6).dropna()
        names = sorted(set(te.index.get_level_values(0)))
        Xt = F.loc[names, fcols].to_numpy(float)
        pred = dict(zip(names, np.array(S6)[np.argmin(np.stack([m.predict(Xt) for m in models], 1), 1)]))
        if metric == "P":
            pred_P = pred
        idx = te.index
        choose = {
            "default": pd.Series("D", index=idx),
            f"best fixed ({best_fixed})": pd.Series(best_fixed, index=idx),
            "family majority": pd.Series([fam_major["item" if n.startswith("item") else "load"] for n, _ in idx], index=idx),
            "LightGBM diagnosis": pd.Series([pred[n] for n, _ in idx], index=idx),
        }
        res = {}
        base = te["D"]
        for k, ch in choose.items():
            c = pd.Series([te.loc[i, ch[i]] for i in idx], index=idx)
            d = c - base
            d = by_instance(d)  # instance-level paired differences (review 2026-09-24)
            res[k] = dict(cost=float(c.mean()), vs_default_pct=float(100 * (base.mean() - c.mean()) / base.mean()),
                          p=float(stats.wilcoxon(d).pvalue) if (d != 0).any() else 1.0)
        orc = te.min(axis=1)
        res["oracle (static, per run)"] = dict(cost=float(orc.mean()), vs_default_pct=float(100 * (base.mean() - orc.mean()) / base.mean()))
        for ag in ("A:bandit", "A:bandit5", "A:diagbandit"):
            a_ = te_all[te_all.arm == ag.replace("C:", "")].set_index(["name", "seed"])["c"] if False else \
                te_all[te_all.arm == ag].set_index(["name", "seed"])["c"]
            a_ = a_.reindex(idx).dropna()
            if len(a_) == 0:
                continue
            d = a_ - base.loc[a_.index]
            d = by_instance(d)  # instance-level paired differences (review 2026-09-24)
            res[ag] = dict(cost=float(a_.mean()), n=int(len(a_)),
                           vs_default_pct=float(100 * (base.loc[a_.index].mean() - a_.mean()) / base.loc[a_.index].mean()),
                           p=float(stats.wilcoxon(d).pvalue) if (d != 0).any() else 1.0)
        res["_train"] = dict(n_train=int(len(tr)), best_fixed=best_fixed, family_majority=fam_major,
                             pred_counts=pd.Series(pred).value_counts().to_dict())
        out[metric] = res
        print(f"== {metric}@{T} (test n={len(te)}; train {len(tr)} instances; family majority {fam_major}) ==")
        for k, v in res.items():
            if not k.startswith("_"):
                print(f"  {k:28s} {v['cost']:.4f}  {v['vs_default_pct']:+.1f}% vs default" + (f"  p={v['p']:.2g}" if "p" in v else ""))
        print("  LightGBM picks:", res["_train"]["pred_counts"])
    json.dump(pred_P, open(ROOT / "datasets/diag_pred.json", "w"), indent=1)
    json.dump(out, open(ROOT / "datasets/diag_results.json", "w"), indent=1, default=str)


if __name__ == "__main__":
    main()
