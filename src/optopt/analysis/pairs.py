"""Offline: CPU||GPU parallel pairs and a sequential switch, computed exactly from recorded trajectories.

On a DGX Spark a CPU solver and cuOpt can run at the same time. Every trace was recorded under that kind of
concurrency (12 CPU lanes + 2 cuOpt lanes), so the combined incumbent of a pair (min over both trajectories at
each t) is what running the pair would have produced, up to the contention level of our runs.

  pair A||B   : incumbent(t) = best of A(t), B(t)                              (uses 1 CPU thread + the GPU)
  switch A→B@k: A for k s, then B restarted from scratch for T-k s, best incumbent kept (no solution transfer)

Output: datasets/pairs.csv and paper/generated/table_pairs.tex
"""
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from optopt.paths import WORK as ROOT  # the workspace (cwd or $OPTOPT_HOME)
from optopt.analysis.build_runs import solu, stem  # noqa: E402
from optopt.analysis.metrics import incumbent_steps, primal_gap  # noqa: E402
from optopt.portfolio.strategies import MILESTONE as S  # noqa: E402


def pi_of_steps(steps, ref, T, sense):
    area, t_prev, g_prev, best = 0.0, 0.0, 1.0, None
    for t, v in sorted(steps):
        if t >= T:
            break
        if best is None or sense * v < sense * best:
            best = v
            area += g_prev * (t - t_prev)
            t_prev, g_prev = t, primal_gap(best, ref, sense)
    return (area + g_prev * (T - t_prev)) / T


def main():
    ref_pub = solu()
    rows = []
    for fam_dir in sorted((ROOT / "traces/raw").iterdir()):
        if fam_dir.name not in ("miplib", "ml4co_item_placement", "ml4co_load_balancing", "pglib_uc") or not fam_dir.is_dir():
            continue  # cross-solver (Track A) sets only
        by_inst = {}
        for f in fam_dir.glob("*__s0.json"):
            t = json.loads(f.read_text())
            by_inst.setdefault(t["instance"], {})[t["strategy"]] = t
        for inst, d in by_inst.items():
            if len(d) < len(S):
                continue
            T = float(next(iter(d.values()))["budget"])
            sense = next(iter(d.values())).get("sense", 1) or 1
            steps = {s: ([] if d[s].get("error") else incumbent_steps(d[s])) for s in S}
            allv = [v for st in steps.values() for _, v in st]
            ref = ref_pub.get(stem(inst), (min(allv) if sense == 1 else max(allv)) if allv else None)
            if ref is None:
                continue
            r = dict(set=fam_dir.name, instance=stem(inst))
            for s in S:
                r[s] = pi_of_steps(steps[s], ref, T, sense)
            for a, b in itertools.product(["H0", "H1", "S0", "S1"], ["C0", "C1"]):
                r[f"{a}||{b}"] = pi_of_steps(steps[a] + steps[b], ref, T, sense)
            for a, b in (("H1", "C0"), ("C0", "H1")):
                for frac in (0.25, 0.5):
                    k = frac * T
                    sw = [(t, v) for t, v in steps[a] if t < k] + [(t + k, v) for t, v in steps[b] if t + k < T]
                    r[f"{a}->{b}@{int(100 * frac)}%"] = pi_of_steps(sw, ref, T, sense)
            rows.append(r)
    df = pd.DataFrame(rows)
    df.to_csv(ROOT / "datasets/pairs.csv", index=False)
    cols = [c for c in df.columns if c not in ("set", "instance")]
    out = []
    for fam in sorted(df["set"].unique()) + ["ALL"]:
        g = df if fam == "ALL" else df[df["set"] == fam]
        m = g[cols].mean()
        single_best = m[S].idxmin()
        pair_best = m[[c for c in cols if "||" in c]].idxmin()
        sw_best = m[[c for c in cols if "->" in c]].idxmin()
        out.append(dict(family=fam, n=len(g), sbs=single_best, sbs_cost=m[single_best], oracle=g[S].min(axis=1).mean(),
                        best_pair=pair_best, pair_cost=m[pair_best], best_switch=sw_best, switch_cost=m[sw_best]))
    o = pd.DataFrame(out)
    print(o.round(3).to_string(index=False))
    names = {"miplib": "MIPLIB 2017", "ml4co_item_placement": "ML4CO item placement",
             "ml4co_load_balancing": "ML4CO load balancing", "pglib_uc": "PGLib-UC", "ALL": "All"}
    lines = [r"\begin{table}[t]\centering\small", r"\resizebox{\linewidth}{!}{\begin{tabular}{lrlrrlrlr}", r"\toprule",
             r"family & $n$ & SBS & $P$ & oracle & best CPU$\|$GPU pair & $P$ & best switch & $P$ \\", r"\midrule"]
    for _, r in o.iterrows():
        lines.append(f"{names.get(r['family'], r['family'])} & {r['n']} & {r['sbs']} & {r['sbs_cost']:.3f} & "
                     f"{r['oracle']:.3f} & {r['best_pair'].replace('||', r'$\|$')} & {r['pair_cost']:.3f} & "
                     f"{r['best_switch'].replace('->', r'$\to$').replace('%', r'\%')} & {r['switch_cost']:.3f} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}}",
              r"\caption{Offline portfolios from the recorded trajectories (seed 0, full budget). CPU$\|$GPU: one CPU "
              r"strategy and one cuOpt strategy run at the same time, best incumbent of the two. Switch A$\to$B@$x$: A "
              r"for $x$ of the budget, then B from scratch (no solution transfer). The pair uses one CPU thread plus the "
              r"GPU, so it is not a free lunch; it is the concurrency the DGX Spark offers.}\label{tab:pairs}",
              r"\end{table}"]
    (ROOT / "paper/generated/table_pairs.tex").write_text("\n".join(lines))


if __name__ == "__main__":
    main()
