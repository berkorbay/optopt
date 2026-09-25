"""Why does a setting applied at the agents' first call beat the same setting applied before presolve?

    python -m optopt.analysis.timing_mech      -> datasets/timing_mech.json, paper/generated/table_timing_mech.tex

Runs (jobs/timing_mech.jsonl, one seed, SCIP statistics recorded after the clock): aggressive heuristics set before
presolve (C:HEU), at the first eligible solver event (A:heu_cb), and at the first event after 10 s (A:heu_10). Per
family: primal integral, where in the solve the setting was applied, and time spent in primal heuristics and the
solutions they found.
"""
import json

import numpy as np
import pandas as pd
from scipy import stats

from optopt.analysis.build_runs import stem
from optopt.analysis.metrics import incumbent_steps, primal_integral
from optopt.paths import WORK as ROOT

SET, T = "timing_mech", 120
ARMS = {"C:HEU": "before presolve", "A:heu_cb": "at first call", "A:heu_10": "after 10\\,s"}


def main():
    runs = {}
    for f in (ROOT / "traces/raw" / SET).glob("*.json"):
        t = json.loads(f.read_text())
        if "instance" in t:
            runs[(stem(t["instance"]), t["strategy"])] = t
    best = {}
    for (n, _), t in runs.items():
        s = t.get("sense", 1) or 1
        for e in t.get("events", []):
            p = e.get("primal")
            if p is not None and (n not in best or s * p < s * best[n]):
                best[n] = p
    rows = []
    for (n, a), t in runs.items():
        ctx = (t.get("extra") or {}).get("agent_ctx") or [{}]
        st = (t.get("extra") or {}).get("scip_stats") or {}
        heur = st.get("heuristics", {})
        rows.append(dict(name=n, family=n.rsplit("_", 1)[0], arm=a,
                         P=1.0 if t.get("error") else primal_integral(t, best.get(n), T),
                         call_t=ctx[0].get("t"), call_nodes=ctx[0].get("nodes"), presolve_s=st.get("presolve_s"),
                         heur_time=sum((v.get("time") or 0) for v in heur.values()),
                         heur_found=sum((v.get("solutions_found") or 0) for v in heur.values()),
                         heur_best=sum((v.get("best_solutions_found") or 0) for v in heur.values()),
                         nodes=t.get("nodes"),
                         first_sol=(incumbent_steps(t) or [(T, None)])[0][0],
                         zeroobj_time=(heur.get("zeroobj") or {}).get("time") or 0.0))
    df = pd.DataFrame(rows)
    out = {"n_runs": len(df), "by_family": {}}
    for fam, g in df.groupby("family"):
        piv = g.pivot_table(index="name", columns="arm", values="P")
        fo = {"n": int(len(piv)), "means": g.groupby("arm")[["P", "first_sol", "zeroobj_time", "heur_time", "heur_found", "heur_best", "nodes"]]
              .mean().round(4).to_dict("index"),
              "call": g[g.arm != "C:HEU"].groupby("arm")[["call_t", "call_nodes"]].median().round(3).to_dict("index"),
              "presolve_s_median": float(g["presolve_s"].median())}
        for a, b in (("A:heu_cb", "C:HEU"), ("A:heu_10", "C:HEU"), ("A:heu_10", "A:heu_cb")):
            if a in piv and b in piv:
                d = (piv[b] - piv[a]).dropna()
                fo[f"{a} vs {b}"] = {"gain_pct": float(100 * d.sum() / piv[b][d.index].sum()),
                                     "better/worse": [int((d > 1e-9).sum()), int((d < -1e-9).sum())],
                                     "p": float(stats.wilcoxon(d).pvalue) if (d != 0).any() else 1.0}
        out["by_family"][fam] = fo
    (ROOT / "datasets/timing_mech.json").write_text(json.dumps(out, indent=1, default=float))
    fam_name = {"item_placement": "item placement", "load_balancing": "load balancing"}
    L = [r"\begin{table}[t]\centering\small", r"\begin{tabular}{llrrrrr}", r"\toprule",
         r"family & aggr.\ heuristics set & $P(120)$ & 1st sol.\ (s) & zero-obj.\ (s) & heur.\ (s) & nodes \\",
         r"\midrule"]
    for fam, fo in out["by_family"].items():
        for a, lab in ARMS.items():
            m = fo["means"].get(a)
            if m:
                L.append(f"{fam_name.get(fam, fam)} & {lab} & {m['P']:.3f} & {m['first_sol']:.2f} & {m['zeroobj_time']:.2f} & "
                         f"{m['heur_time']:.1f} & {m['nodes']:.0f} \\\\")
        L.append(r"\midrule")
    L[-1] = r"\bottomrule"
    L += [r"\end{tabular}", r"\caption{When aggressive heuristics are applied: 30 held-out ML4CO instances (validation split), one seed, "
          r"120\,s, all arms in one session, both LLM servers idle. Means per family. \emph{1st sol.}: time of the first "
          r"incumbent; \emph{zero-obj.}: time in SCIP's zero-objective heuristic; \emph{heur.}: time in all primal "
          r"heuristics (SCIP's statistics); \emph{after 10\,s}: at the first call after 10\,s. Nodes: branch-and-bound nodes solved.}\label{tab:timingmech}", r"\end{table}"]
    (ROOT / "paper/generated/table_timing_mech.tex").write_text("\n".join(L))
    print(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main()
