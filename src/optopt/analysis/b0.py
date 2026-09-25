"""Track B · B0 go/no-go: is there headroom in switching SCIP's settings mid-solve?

Costs per (instance, arm, seed): normalised primal integral P(T) (time-to-good-solution) and primal-dual
integral PDI(T) (closing the gap, i.e. also the bound). Reference: MIPLIB published value.

Every "oracle" is chosen on one seed and scored on the OTHER seed (held-out), then averaged over the two
directions, so run-to-run noise cannot inflate the headroom (Track A showed single-seed oracles look ~15 % better
than they realise).

  best static      : the single static setting with the lowest mean cost (chosen on the other seed)
  best arm         : the single arm (static or schedule) with the lowest mean cost — a universal schedule
  static oracle    : per-instance best static setting (Track-A-style selection inside SCIP)
  full oracle      : per-instance best over all arms — the headroom an in-solver controller restricted to these
                     schedules could reach at most
Gate (spec §22): full oracle vs best static > 15–20 %.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from optopt.paths import WORK as ROOT  # the workspace (cwd or $OPTOPT_HOME)
from optopt.analysis.build_runs import solu, stem  # noqa: E402
from optopt.analysis.metrics import primal_dual_integral, primal_integral  # noqa: E402
from optopt.portfolio.strategies import B0_ARMS, B0_STATIC  # noqa: E402

ARMS = [a for a in B0_ARMS if a != "B:NOC>D@50"]  # the 13th arm was added later for B1 and never run in B0


def load():
    ref = solu()
    rows = []
    for f in (ROOT / "traces/raw/b0_scip").glob("*.json"):
        t = json.loads(f.read_text())
        name = stem(t["instance"])
        T = float(t["budget"])
        err = bool(t.get("error"))
        rows.append(dict(name=name, arm=t["strategy"], seed=t["seed"],
                         P=1.0 if err else primal_integral(t, ref.get(name), T),
                         PDI=1.0 if err else primal_dual_integral(t, T),
                         switch_t=(t.get("extra") or {}).get("switch_t"), err=err))
    return pd.DataFrame(rows)


def gate(df, metric):
    piv = {s: df[df.seed == s].pivot_table(index="name", columns="arm", values=metric).reindex(columns=ARMS) for s in (0, 1)}
    common = piv[0].dropna().index.intersection(piv[1].dropna().index)
    A, B = piv[0].loc[common], piv[1].loc[common]
    out = {}
    for choose, score in ((A, B), (B, A)):
        st = choose[B0_STATIC].mean().idxmin()
        arm = choose.mean().idxmin()
        so = choose[B0_STATIC].to_numpy().argmin(1)
        fo = choose.to_numpy().argmin(1)
        idx = np.arange(len(score))
        res = dict(best_static=score[st].mean(), best_static_name=st, best_arm=score[arm].mean(), best_arm_name=arm,
                   static_oracle=score[B0_STATIC].to_numpy()[idx, so].mean(), full_oracle=score.to_numpy()[idx, fo].mean(),
                   static_oracle_same_seed=choose[B0_STATIC].min(axis=1).mean(), full_oracle_same_seed=choose.min(axis=1).mean(),
                   default=score["B:D"].mean())
        for k, v in res.items():
            out.setdefault(k, []).append(v)
    agg = {k: (v[0] if isinstance(v[0], str) else float(np.mean(v))) for k, v in out.items()}
    bs = agg["best_static"]
    for k in ("best_arm", "static_oracle", "full_oracle", "default"):
        agg[f"{k}_vs_best_static_pct"] = 100 * (bs - agg[k]) / bs
    agg["n"] = len(common)
    agg["names_chosen"] = f"{out['best_static_name']} / {out['best_arm_name']}"
    return agg, (A + B) / 2


def main():
    df = load()
    print(f"{len(df)} runs, {df.err.sum()} errors, {df.name.nunique()} instances")
    res = {}
    for metric in ("P", "PDI"):
        agg, mean = gate(df, metric)
        res[metric] = agg
        print(f"\n== {metric} (n={agg['n']}) ==")
        print(mean.mean().round(4).sort_values().to_string())
        for k in ("default", "best_static", "best_arm", "static_oracle", "full_oracle"):
            print(f"  {k:15s} {agg[k]:.4f}  ({agg.get(k + '_vs_best_static_pct', 0):+.1f}% vs best static)")
        print("  chosen:", agg["names_chosen"], " same-seed full oracle", round(agg["full_oracle_same_seed"], 4))
    # which arm wins per instance (seed-averaged), P
    _, meanP = gate(df, "P")
    wins = meanP.idxmin(axis=1).value_counts()
    res["wins_P"] = wins.to_dict()
    print("\nper-instance winner (seed-mean P):", wins.to_dict())
    json.dump(res, open(ROOT / "datasets/b0_gate.json", "w"), indent=1, default=str)
    meanP.to_csv(ROOT / "datasets/b0_meanP.csv")
    # LaTeX table
    names = {"default": "SCIP default", "best_static": "best static setting", "best_arm": "best single schedule",
             "static_oracle": "per-instance best static (oracle)", "full_oracle": "per-instance best incl. schedules (oracle)"}
    lines = [r"\begin{table}[t]\centering\small", r"\begin{tabular}{lrrrr}", r"\toprule",
             r"policy & $P(30)$ & vs best static & PDI$(30)$ & vs best static \\", r"\midrule"]
    for k, nm in names.items():
        p, q = res["P"], res["PDI"]
        lines.append(f"{nm} & {p[k]:.3f} & {p.get(k + '_vs_best_static_pct', 0):+.1f}\\% & {q[k]:.3f} & "
                     f"{q.get(k + '_vs_best_static_pct', 0):+.1f}\\% \\\\")
    lines += [r"\bottomrule", r"\end{tabular}",
              rf"\caption{{Track B go/no-go (B0): SCIP 10 with five static settings and seven fixed mid-solve schedules on "
              rf"{res['P']['n']} non-trivial MIPLIB instances, 30\,s, two seeds. Every choice is made on one seed and scored "
              rf"on the other. PDI: primal-dual integral. Positive = better than the best static setting.}}"
              r"\label{tab:b0}", r"\end{table}"]
    (ROOT / "paper/generated/table_b0.tex").write_text("\n".join(lines))


if __name__ == "__main__":
    main()
