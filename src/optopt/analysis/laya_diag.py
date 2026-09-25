"""Laya as the diagnosis agent (D-004 cell "Laya as agent", first move only): choose SCIP's static setting at t = 0.

Same data and scoring as analysis/diag.py (E3): train on `diag_train` (6 settings x 60 ML4CO training instances, 120 s),
test on the 30 held-out ML4CO instances (validation split) recorded in `pilot_e2` (all 6 static settings, 2 seeds), so every policy
is scored exactly from recorded runs. Laya gets the same instance-feature text as in Track A and a six-option choice
over SCIP settings; zero-shot and fine-tuned (soft targets P ~ exp(-beta * cost), 3 training seeds, majority vote).

  python analysis/laya_diag.py     -> datasets/laya_diag.json
"""
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from optopt.paths import WORK as ROOT  # the workspace (cwd or $OPTOPT_HOME)
from optopt.analysis.build_runs import stem  # noqa: E402
from optopt.analysis.diag import S6, T, costs  # noqa: E402
from optopt.policies.laya import Laya, state_text  # noqa: E402
from optopt.analysis.stats import by_instance  # noqa: E402

OPTIONS = {
    "D": "SCIP default settings",
    "NOC": "SCIP with cutting-plane separation switched off",
    "PSC": "SCIP with pseudo-cost branching",
    "INF": "SCIP with inference branching",
    "HOFF": "SCIP with primal heuristics switched off",
    "HEU": "SCIP with aggressive primal heuristics",
}
INSTR = "Which SCIP setting will reach the best solution fastest within the time budget for this problem?"


def score(te, choice):
    idx = te.index
    base = te["D"]
    c = pd.Series([te.loc[i, choice[i[0]]] for i in idx], index=idx)
    d = c - base
    d = by_instance(d)  # instance-level paired differences (review 2026-09-24)
    return dict(cost=float(c.mean()), vs_default_pct=float(100 * (base.mean() - c.mean()) / base.mean()),
                p=float(stats.wilcoxon(d).pvalue) if (d != 0).any() else 1.0,
                picks=dict(Counter(choice[n] for n in sorted(set(idx.get_level_values(0))))))


def main(beta=20.0, epochs=8, seeds=(0, 1, 2)):
    F = pd.read_parquet(ROOT / "datasets/features.parquet").assign(name=lambda d: d["instance"].map(stem)).set_index("name")
    out = {}
    lg = json.load(open(ROOT / "datasets/diag_results.json"))
    for metric in ("P", "PDI"):
        tr = costs("diag_train", metric).pivot_table(index="name", columns="arm", values="c").reindex(columns=S6).dropna()
        tr = tr.loc[tr.index.intersection(F.index)]
        te_all = costs("pilot_e2", metric)
        te = te_all[te_all.arm.isin(S6)].pivot_table(index=["name", "seed"], columns="arm", values="c").reindex(columns=S6).dropna()
        names = sorted(set(te.index.get_level_values(0)))
        txt_tr = [state_text(F.loc[n].to_dict(), T) for n in tr.index]
        txt_te = [state_text(F.loc[n].to_dict(), T) for n in names]
        C = tr.to_numpy()
        soft = np.exp(-beta * (C - C.min(1, keepdims=True)))
        soft /= soft.sum(1, keepdims=True)
        lay = Laya(options=OPTIONS, instructions=INSTR)
        zs = lay.predict(txt_te)
        res = {"Laya zero-shot": score(te, dict(zip(names, np.array(S6)[zs.argmax(1)])))}
        votes, probs = [], []
        for sd in seeds:
            lay.reset()
            lay.finetune(txt_tr, soft, epochs=epochs, seed=sd, log=print)
            pr = lay.predict(txt_te)
            probs.append(pr)
            votes.append(np.array(S6)[pr.argmax(1)])
            res[f"Laya fine-tuned (seed {sd})"] = score(te, dict(zip(names, votes[-1])))
        mean = np.mean(probs, 0)
        res["Laya fine-tuned (mean of 3)"] = score(te, dict(zip(names, np.array(S6)[mean.argmax(1)])))
        for k in ("default", "LightGBM diagnosis", "oracle (static, per run)"):
            if k in lg[metric]:
                res[k] = lg[metric][k]
        bf = [k for k in lg[metric] if k.startswith("best fixed")]
        if bf:
            res[bf[0]] = lg[metric][bf[0]]
        out[metric] = res
        print(f"== {metric}@{T} ==")
        for k, v in res.items():
            print(f"  {k:30s} {v['cost']:.4f} {v['vs_default_pct']:+.1f}%" + (f" p={v['p']:.2g}" if "p" in v else "")
                  + (f" picks={v['picks']}" if "picks" in v else ""))
    json.dump(out, open(ROOT / "datasets/laya_diag.json", "w"), indent=1)


if __name__ == "__main__":
    main()
