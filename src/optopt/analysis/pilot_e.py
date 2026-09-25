"""Main-experiment pilot (D-004): agents that start from SCIP's defaults inside a fixed slice (1 X925 core, 9 GiB,
120 s wall clock including every agent decision). Arms: default (no agent), online bandit, rules agent; plus a
resource-doubled reference — two default runs (seeds 0 and 1) in parallel, best incumbent/bound of the two (2 cores).

Costs: primal integral P and primal-dual integral PDI at 30 / 60 / 120 s (views of the same runs). Per arm: mean
over (instance, seed), paired Wilcoxon against default, split by family (ML4CO test instances vs MIPLIB).
Reference for P: MIPLIB published value, else the best value found by any run on that instance.
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

ARMS = ["A:default", "A:bandit", "A:rules"]
SET = "pilot_e"


def main():
    ref = solu()
    runs = {}
    for f in (ROOT / "traces/raw" / SET).glob("*.json"):
        t = json.loads(f.read_text())
        if "instance" in t:
            runs[(stem(t["instance"]), t["strategy"], t["seed"])] = t
    best = {}
    for (n, _, _), t in runs.items():
        s = t.get("sense", 1) or 1
        for e in t.get("events", []):
            p = e.get("primal")
            if p is not None and (n not in best or s * p < s * best[n]):
                best[n] = p
    names = sorted({k[0] for k in runs})
    rows = []
    for n in names:
        fam = "ML4CO" if n.startswith(("item_placement", "load_balancing")) else "MIPLIB"
        r = ref.get(n, best.get(n))
        for T in (30, 60, 120):
            for s in (0, 1):
                for a in ARMS:
                    t = runs.get((n, a, s))
                    if t is None:
                        continue
                    err = bool(t.get("error"))
                    rows.append(dict(name=n, fam=fam, T=T, seed=s, arm=a,
                                     P=1.0 if err else primal_integral(t, r, T), PDI=1.0 if err else primal_dual_integral(t, T),
                                     decisions=len((t.get("extra") or {}).get("agent_log", []))))
            d0, d1 = runs.get((n, "A:default", 0)), runs.get((n, "A:default", 1))
            if d0 and d1 and not d0.get("error") and not d1.get("error"):
                par = {"sense": d0.get("sense", 1), "events": d0["events"] + d1["events"]}
                for s in (0, 1):  # same value for both seeds so paired tests line up
                    rows.append(dict(name=n, fam=fam, T=T, seed=s, arm="2x default (2 cores)",
                                     P=primal_integral(par, r, T), PDI=primal_dual_integral(par, T), decisions=0))
    df = pd.DataFrame(rows)
    out = {}
    arms = ARMS + ["2x default (2 cores)"]
    for T in (30, 60, 120):
        for metric in ("P", "PDI"):
            for fam in ("ALL", "ML4CO", "MIPLIB"):
                sub = df[(df["T"] == T) & ((df["fam"] == fam) if fam != "ALL" else True)]
                piv = sub.pivot_table(index=["name", "seed"], columns="arm", values=metric).reindex(columns=arms).dropna()
                if piv.empty:
                    continue
                res = {"n": int(len(piv)), "means": piv.mean().round(4).to_dict()}
                for a in arms[1:]:
                    d = piv[a] - piv["A:default"]
                    d = by_instance(d)  # instance-level paired differences (review 2026-09-24)
                    p = stats.wilcoxon(d).pvalue if (d != 0).any() else 1.0
                    res[a] = dict(vs_default_pct=float(100 * (piv["A:default"].mean() - piv[a].mean()) / piv["A:default"].mean()),
                                  p=float(p), wins=int((d < 0).sum()), losses=int((d > 0).sum()))
                out[f"{metric}@{T}|{fam}"] = res
    json.dump(out, open(ROOT / "datasets/pilot_e.json", "w"), indent=1)
    for k in ("P@120|ALL", "PDI@120|ALL", "P@120|ML4CO", "P@120|MIPLIB", "PDI@120|ML4CO", "PDI@120|MIPLIB", "P@30|ALL"):
        if k not in out:
            continue
        r = out[k]
        print(f"{k:16s} n={r['n']:3d} default {r['means']['A:default']:.4f} | " + " | ".join(
            f"{a.replace('A:', '')} {r[a]['vs_default_pct']:+.1f}% (p={r[a]['p']:.2g}, {r[a]['wins']}W/{r[a]['losses']}L)"
            for a in arms[1:]))
    L = [r"\begin{table}[t]\centering\small", r"\begin{tabular}{llrrrr}", r"\toprule",
         r"metric & instances & default & bandit agent & rules agent & 2$\times$ default (2 cores) \\", r"\midrule"]
    for m in ("P", "PDI"):
        for fam in ("ML4CO", "MIPLIB", "ALL"):
            k = f"{m}@120|{fam}"
            if k not in out:
                continue
            r = out[k]
            cells = [f"{r['means']['A:default']:.3f}"] + [
                f"{r['means'][a]:.3f} ({r[a]['vs_default_pct']:+.0f}\\%{'*' if r[a]['p'] < 0.05 else ''})" for a in arms[1:]]
            L.append(f"{'$P$' if m == 'P' else 'PDI'} & {fam} (n={r['n']}) & " + " & ".join(cells) + r" \\")
    L += [r"\bottomrule", r"\end{tabular}", r"\caption{Main-experiment pilot: agents start from SCIP's defaults in a fixed slice "
          r"(one Cortex-X925 core, 9\,GiB, 120\,s wall clock including every agent decision). Mean over (instance, seed); "
          r"percentages vs default, * paired Wilcoxon $p<0.05$. The last column uses twice the compute and is a reference, "
          r"not a competitor.}\label{tab:pilot}", r"\end{table}"]
    (ROOT / "paper/generated/table_pilot.tex").write_text("\n".join(L))


if __name__ == "__main__":
    main()
