"""Offline on-the-fly controller simulation (Track B): at a decision time tau, continue the current run or restart
into another setting — decided from the run's OWN state so far. Costs are exact from recorded trajectories.

Why: B2 showed the best setting for the bound depends mostly on the run (same winner on both seeds for only 35 %
of instances), which an up-front choice cannot capture but a controller watching the run might.

Simulation of "restart into setting b at tau": the base run's events up to tau, then b's recorded run (same seed)
shifted by tau and cut at T. Best incumbent and best (valid, global) bound are carried across the restart. This is
conservative: a real SCIP restart also keeps presolve reductions and learned information.

Policies (grouped 5-fold CV by instance, both seeds pooled):
  continue        always keep the base run
  restart-best    always restart into the best static setting learned on the training folds
  lightgbm        per-action cost regressors on the state at tau -> argmin
  oracle          per (instance, seed) best action in hindsight
Reported: mean cost and closed gap (0 = continue, 1 = oracle).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from optopt.paths import WORK as ROOT  # the workspace (cwd or $OPTOPT_HOME)
from optopt.analysis.build_runs import solu, stem  # noqa: E402
from optopt.analysis.metrics import dual_steps, incumbent_steps, primal_dual_integral, primal_integral  # noqa: E402
from optopt.portfolio.strategies import B2_STATIC  # noqa: E402

SET = "b2_scip"


def load():
    runs = {}
    for f in (ROOT / "traces/raw" / SET).glob("*.json"):
        t = json.loads(f.read_text())
        if "instance" not in t:
            continue
        runs[(stem(t["instance"]), t["strategy"], t["seed"])] = t
    return runs


def splice(base, other, tau, T):
    ev = [e for e in base.get("events", []) if e["t"] <= tau]
    ev += [dict(e, t=e["t"] + tau) for e in other.get("events", []) if e["t"] + tau < T]
    return {"sense": base.get("sense", 1), "events": ev}


def state(tr, tau, feats):
    ev = [e for e in tr.get("events", []) if e["t"] <= tau]
    ps, ds = incumbent_steps({"sense": tr.get("sense", 1), "events": ev}), dual_steps({"sense": tr.get("sense", 1), "events": ev})
    p = ps[-1][1] if ps else None
    d = ds[-1][1] if ds else None
    d5 = [v for t, v in ds if t <= tau - 5]
    nodes = [e.get("nodes") for e in ev if e.get("nodes") is not None]
    lps = [e.get("lp_iters") for e in ev if e.get("lp_iters") is not None]
    gap = abs(p - d) / max(abs(p), abs(d), 1e-9) if p is not None and d is not None else 1.0
    return dict(has_inc=float(p is not None), pd_gap=min(1.0, gap), n_inc=len(ps),
                inc_age=(tau - ps[-1][0]) / tau if ps else 1.0, first_inc=(ps[0][0] / tau) if ps else 1.0,
                bound_move_5s=(abs(d - d5[-1]) / max(abs(d), 1e-9)) if d is not None and d5 else 0.0,
                log_nodes=np.log10(1 + (nodes[-1] if nodes else 0)), log_lp=np.log10(1 + (lps[-1] if lps else 0)),
                **{k: feats.get(k, 0.0) for k in ("log_rows", "log_cols", "log_nnz", "frac_bin", "frac_cont", "frac_eq")})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="C:D")
    ap.add_argument("--tau", type=float, default=20)
    ap.add_argument("--T", type=float, default=120)
    ap.add_argument("--metric", default="PDI")
    a = ap.parse_args()
    runs = load()
    ref = solu()
    F = pd.read_parquet(ROOT / "datasets/features.parquet").assign(name=lambda d: d["instance"].map(stem)).set_index("name")
    actions = ["continue"] + [b for b in B2_STATIC if b != a.base]
    rows = []
    names = sorted({k[0] for k in runs})
    for n in names:
        for s in (0, 1):
            base = runs.get((n, a.base, s))
            if base is None or base.get("error"):
                continue
            costs = {}
            for act in actions:
                if act == "continue":
                    tr = base
                else:
                    other = runs.get((n, act, s))
                    if other is None:
                        break
                    tr = splice(base, other, a.tau, a.T)
                costs[act] = primal_dual_integral(tr, a.T) if a.metric == "PDI" else primal_integral(tr, ref.get(n), a.T)
            if len(costs) != len(actions) or any(np.isnan(v) for v in costs.values()):
                continue
            f = F.loc[n].to_dict() if n in F.index else {}
            rows.append(dict(name=n, seed=s, **{f"c:{k}": v for k, v in costs.items()}, **state(base, a.tau, f)))
    df = pd.DataFrame(rows)
    C = df[[f"c:{k}" for k in actions]].to_numpy()
    X = df.drop(columns=["name", "seed"] + [f"c:{k}" for k in actions]).to_numpy(float)
    inst = df["name"].unique()
    fold = {n: i % 5 for i, n in enumerate(np.random.default_rng(3).permutation(inst))}
    fid = df["name"].map(fold).to_numpy()
    pick = {"continue": np.zeros(len(df), int), "restart-best": np.zeros(len(df), int), "lightgbm": np.zeros(len(df), int)}
    import lightgbm as lgb
    for k in range(5):
        tr, te = fid != k, fid == k
        if te.sum() == 0:
            continue
        pick["restart-best"][te] = 1 + int(np.argmin(C[tr, 1:].mean(0)))
        preds = []
        for j in range(C.shape[1]):
            m = lgb.LGBMRegressor(n_estimators=200, learning_rate=0.05, num_leaves=7, min_child_samples=4, verbose=-1,
                                  random_state=j, n_jobs=1)
            m.fit(X[tr], C[tr, j])
            preds.append(m.predict(X[te]))
        pick["lightgbm"][te] = np.argmin(np.stack(preds, 1), 1)
    pick["oracle"] = C.argmin(1)
    idx = np.arange(len(df))
    cont, orc = C[:, 0].mean(), C.min(1).mean()
    out = {}
    print(f"{a.metric}, base {a.base}, tau {a.tau:.0f}s of {a.T:.0f}s, {len(df)} runs on {len(inst)} instances")
    for k, p in pick.items():
        c = C[idx, p].mean()
        cg = (cont - c) / (cont - orc) if cont > orc else float("nan")
        out[k] = dict(cost=float(c), closed_gap=float(cg), vs_continue_pct=float(100 * (cont - c) / cont),
                      actions=dict(zip(*np.unique(np.array(actions)[p], return_counts=True))))
        print(f"  {k:13s} cost {c:.4f}  {100 * (cont - c) / cont:+.1f}% vs continue  closed gap {cg:+.2f}  "
              f"{ {str(x): int(y) for x, y in out[k]['actions'].items()} }")
    json.dump({"args": vars(a), "n_runs": len(df), "n_instances": int(len(inst)), "results": out},
              open(ROOT / f"datasets/switch_sim_{a.metric}_{a.base.replace(':', '')}_tau{int(a.tau)}.json", "w"),
              indent=1, default=lambda x: int(x) if isinstance(x, np.integer) else str(x))


if __name__ == "__main__":
    main()
