"""Track B · B1: does a mid-solve switch (separation off early, default later) beat both static settings once the
budget is long enough for cuts to pay? SCIP, 120 s, pinned X925 cores, one seed → paired per-instance tests.

Views at 30 / 60 / 120 s are cut from the same trajectories. Costs: P (primal integral) and PDI (primal-dual).
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

from optopt.paths import WORK as ROOT  # the workspace (cwd or $OPTOPT_HOME)
from optopt.analysis.build_runs import solu, stem  # noqa: E402
from optopt.analysis.metrics import primal_dual_integral, primal_integral  # noqa: E402
from optopt.analysis.stats import by_instance  # noqa: E402

ARMS = ["B:D", "B:NOC", "B:NOC>D@25", "B:NOC>D@50"]
NAMES = {"B:D": "SCIP default", "B:NOC": "separation off", "B:NOC>D@25": "off $\\to$ default at 25\\,\\%",
         "B:NOC>D@50": "off $\\to$ default at 50\\,\\%"}


def main():
    ref = solu()
    rows = []
    for f in (ROOT / "traces/raw/b1_scip120").glob("*__s0.json"):
        t = json.loads(f.read_text())
        n = stem(t["instance"])
        for T in (30, 60, 120):
            err = bool(t.get("error"))
            rows.append(dict(name=n, arm=t["strategy"], T=T, P=1.0 if err else primal_integral(t, ref.get(n), T),
                             PDI=1.0 if err else primal_dual_integral(t, T), err=err))
    df = pd.DataFrame(rows)
    out, lines = {}, []
    for T in (30, 60, 120):
        for metric in ("P", "PDI"):
            piv = df[df["T"] == T].pivot_table(index="name", columns="arm", values=metric).reindex(columns=ARMS).dropna()
            means = piv.mean()
            res = dict(n=len(piv), means=means.round(4).to_dict(), wins=piv.idxmin(axis=1).value_counts().to_dict())
            for a, b in (("B:NOC", "B:D"), ("B:NOC>D@25", "B:NOC"), ("B:NOC>D@50", "B:NOC"), ("B:NOC>D@25", "B:D")):
                d = piv[a] - piv[b]
                d = by_instance(d)  # instance-level paired differences (review 2026-09-24)
                p = stats.wilcoxon(d).pvalue if (d != 0).any() else 1.0
                res[f"{a} vs {b}"] = dict(rel_pct=float(100 * (means[b] - means[a]) / means[b]), p=float(p))
            out[f"{metric}@{T}"] = res
            print(f"{metric}@{T} n={len(piv)} " + " ".join(f"{k}={v:.4f}" for k, v in means.items()))
            for k, v in res.items():
                if " vs " in k:
                    print(f"    {k}: {v['rel_pct']:+.1f}% (p={v['p']:.3g})")
    json.dump(out, open(ROOT / "datasets/b1_results.json", "w"), indent=1)
    L = [r"\begin{table}[t]\centering\small", r"\begin{tabular}{lrrrrrr}", r"\toprule",
         r"& \multicolumn{3}{c}{$P(T)$} & \multicolumn{3}{c}{PDI$(T)$} \\", r"arm & 30\,s & 60\,s & 120\,s & 30\,s & 60\,s & 120\,s \\",
         r"\midrule"]
    for a in ARMS:
        cells = [f"{out[f'{m}@{T}']['means'][a]:.3f}" for m in ("P", "PDI") for T in (30, 60, 120)]
        L.append(f"{NAMES[a]} & " + " & ".join(cells) + r" \\")
    n = out["P@120"]["n"]
    L += [r"\bottomrule", r"\end{tabular}",
          rf"\caption{{Track B, B1: SCIP~10 at 120\,s on the {n} B0 instances where these arms differed most, one run per "
          r"Cortex-X925 core, 8\,GiB per run, no other load; 30/60\,s views cut from the same runs. Paired Wilcoxon tests "
          r"in the text.}\label{tab:b1}", r"\end{table}"]
    (ROOT / "paper/generated/table_b1.tex").write_text("\n".join(L))


if __name__ == "__main__":
    main()
