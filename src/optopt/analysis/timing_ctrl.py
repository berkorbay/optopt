"""Timing-matched controls (review 2026-09-24): separate WHEN a setting is applied from WHICH setting an agent picks.

Same 30 held-out ML4CO instances (validation split), 2 seeds, 120 s, one Cortex-X925 core + 8 GiB, all arms in one session:
  A:default    SCIP defaults, no agent
  C:HEU        aggressive heuristics configured before presolve (the best fixed setting learned on training data)
  A:heu_cb     aggressive heuristics applied through the agent callback at the first eligible solver event
  A:llm_first  Ornith-1.5-35B-A3B: its first decision only
  A:llm        Ornith-1.5-35B-A3B: first decision and one call every 20 s
Contrasts (instance-level, seeds averaged): timing = A:heu_cb vs C:HEU; judgement = A:llm vs A:heu_cb; steering =
A:llm vs A:llm_first; plus every arm vs the defaults. Reference per instance: best incumbent of any run in this set.
Writes datasets/timing_ctrl.json and paper/generated/table_timing.tex.
"""
import json
from collections import Counter

import numpy as np
import pandas as pd

from optopt.analysis.build_runs import stem
from optopt.analysis.metrics import primal_dual_integral, primal_integral
from optopt.analysis.stats import paired_instance
from optopt.paths import WORK as ROOT

SET, T = "timing_ctrl", 120
ARMS = ["A:default", "C:HEU", "A:heu_cb", "A:llm_first", "A:llm"]
CONTRASTS = [("A:heu_cb", "C:HEU", "timing: same setting via the callback vs before presolve"),
             ("A:llm", "A:heu_cb", "judgement: LLM vs the fixed setting applied at the same moment"),
             ("A:llm", "A:llm_first", "steering: LLM every 20 s vs its first decision only"),
             ("A:llm_first", "A:heu_cb", "first move: LLM's first decision vs the fixed setting at the same moment"),
             ("A:llm", "C:HEU", "replication of the earlier LLM vs fixed-setting comparison")]


def main():
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
    rows, dec = [], []
    for (n, a, sd), t in runs.items():
        err = bool(t.get("error"))
        rows.append(dict(name=n, arm=a, seed=sd, P=1.0 if err else primal_integral(t, best.get(n), T),
                         PDI=1.0 if err else primal_dual_integral(t, T), err=err))
        for r in (t.get("extra") or {}).get("agent_log", []):
            dec.append(dict(arm=a, t=r[0], action=(r[1][1] if r[1] and r[1][0] == "set" else "keep"), ms=r[2]))
    df = pd.DataFrame(rows)
    out = {"n": df.groupby("arm").size().to_dict(), "errors": int(df.err.sum())}
    for m in ("P", "PDI"):
        piv = df.pivot_table(index=["name", "seed"], columns="arm", values=m)
        out[m] = {"means": {a: float(piv[a].mean()) for a in ARMS if a in piv},
                  "vs_default": {a: paired_instance(piv, a, "A:default") for a in ARMS[1:] if a in piv},
                  "contrasts": {label: paired_instance(piv, a, b) for a, b, label in CONTRASTS if a in piv and b in piv}}
        for a, b, label in CONTRASTS:  # median per-instance relative gain, next to the mean (review 2026-09-24, M5)
            if label in out[m]["contrasts"]:
                inst = piv[[a, b]].dropna().groupby(level=0).mean()
                out[m]["contrasts"][label]["median_pct"] = float((100 * (inst[b] - inst[a]) / inst[b]).median())
    if dec:
        D = pd.DataFrame(dec)
        out["first_moves"] = {a: dict(Counter(g.sort_values("t").groupby(level=0).head(1)["action"]))
                              for a, g in D.groupby("arm")}
        out["actions"] = {a: dict(Counter(g["action"])) for a, g in D.groupby("arm")}
        out["decision_ms_median"] = D.groupby("arm")["ms"].median().round(1).to_dict()
    json.dump(out, open(ROOT / "datasets/timing_ctrl.json", "w"), indent=1, default=str)
    names = {"A:default": "SCIP defaults", "C:HEU": "aggressive heuristics, set before presolve",
             "A:heu_cb": "aggressive heuristics, set at the first solver event",
             "A:llm_first": "LLM agent, first decision only", "A:llm": "LLM agent, every 20\\,s"}
    short = {"A:default": "defaults", "C:HEU": "heuristics before presolve", "A:heu_cb": "heuristics at first event",
             "A:llm_first": "LLM first decision", "A:llm": "LLM every 20\\,s"}
    L = [r"\begin{table}[t]\centering\small", r"\begin{tabular}{@{}>{\raggedright\arraybackslash}p{0.50\linewidth}rr@{}}", r"\toprule",
         r"arm & $P(120)$ & vs defaults, 95\,\% interval \\", r"\midrule"]
    for a in ARMS:
        if a not in out["P"]["means"]:
            continue
        v = out["P"]["vs_default"].get(a)
        L.append(f"{names[a]} & {out['P']['means'][a]:.3f} & " +
                 ("--" if v is None else f"${v['gain_pct']:+.1f}$\\,\\% $[{v['ci95'][0]:+.1f}, {v['ci95'][1]:+.1f}]$") + r" \\")
    L += [r"\midrule", r"\emph{contrast} (first vs second arm) & mean (median) & 95\,\% interval, $p$ \\", r"\midrule"]
    for a, b, label in CONTRASTS:
        c = out["P"]["contrasts"].get(label)
        if c:
            kind = label.split(':')[0].replace("replication of the earlier LLM vs fixed-setting comparison", "replication")
            pv = f"p={c['p']:.2g}" if c['p'] >= 1e-3 else f"p<10^{{{int(np.floor(np.log10(c['p']))) + 1}}}"
            L.append(f"{kind}: {short[a]} vs {short[b]} & ${c['gain_pct']:+.1f}$\\,\\% (${c['median_pct']:+.1f}$) & "
                     f"$[{c['ci95'][0]:+.1f}, {c['ci95'][1]:+.1f}]$, ${pv}$ \\\\")
    L += [r"\bottomrule", r"\end{tabular}", r"\caption{Timing-matched controls, the primary agent comparison: 30 held-out ML4CO instances (validation split), two seeds, "
          r"120\,s, all arms in one session. Gains in primal integral, positive when the first arm is better: the gain in the mean, and in parentheses the median per-instance gain. Intervals: instance-level bootstrap of the mean gain; $p$: Wilcoxon signed-rank over instances. ``Heuristics'': the aggressive-heuristics setting; ``first event'': the first eligible solver event, where the agents first act.}\label{tab:timing}",
          r"\end{table}"]
    (ROOT / "paper/generated/table_timing.tex").write_text("\n".join(L))
    print(json.dumps({m: {"means": out[m]["means"], "contrasts": {k: (round(v["gain_pct"], 1), [round(x, 1) for x in v["ci95"]], round(v["p"], 3))
                                                                  for k, v in out[m]["contrasts"].items()}} for m in ("P", "PDI")}, indent=1))


if __name__ == "__main__":
    main()
