"""D-004 main experiment, LLM-agent arms (2026-09-24): 30 held-out ML4CO instances (validation split), SCIP from defaults, 120 s wall
clock including every decision, one Cortex-X925 core + 8 GiB, seeds 0 and 1 (hosted LLM: seed 0 only).

Arms: A:default, C:HEU (best fixed setting learned on training instances), A:laya (Laya as the agent, t = 0 choice),
A:llm (Ornith-1.5-35B-A3B, NVFP4 on vLLM, thinking off, every 20 s), A:llm+laya (same, with Laya's probabilities as a
tool result), A:gpt6luna (OpenAI GPT-6 Luna via ChatGPT Plus, reasoning low, every 30 s).
Reference value per instance: best incumbent over every run of the instance in this set (as analysis/diag.py).
Writes datasets/llm_agents.json.
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
from optopt.analysis.metrics import primal_dual_integral, primal_integral  # noqa: E402
from optopt.analysis.stats import paired_instance  # noqa: E402

SET, T = "llm_agents", 120
ARMS = ["A:default", "C:HEU", "A:laya", "A:llm", "A:llm+laya", "A:gpt6luna"]


def main():
    runs = {}
    for f in (ROOT / "traces/raw" / SET).glob("*.json"):
        t = json.loads(f.read_text())
        runs[(stem(t["instance"]), t["strategy"], t["seed"])] = t
    best = {}
    for (n, _, _), t in runs.items():
        for e in t.get("events", []):
            p = e.get("primal")
            if p is not None:
                s = t.get("sense", 1) or 1
                if n not in best or s * p < s * best[n]:
                    best[n] = p
    rows, dec = [], []
    for (n, a, s), t in runs.items():
        err = bool(t.get("error"))
        rows.append(dict(name=n, arm=a, seed=s, fam="item" if n.startswith("item") else "load",
                         P=1.0 if err else primal_integral(t, best.get(n), T),
                         PDI=1.0 if err else primal_dual_integral(t, T), err=err))
        for r in (t.get("extra") or {}).get("agent_log", []):
            dec.append(dict(arm=a, t=r[0], action=(r[1][1] if r[1] and r[1][0] == "set" else (r[1][0] if r[1] else "keep")),
                            ms=r[2], note=(r[3] if len(r) > 3 else "")))
    df, D = pd.DataFrame(rows), pd.DataFrame(dec)
    out = {"n": df.groupby("arm").size().to_dict(), "errors": df.groupby("arm")["err"].sum().astype(int).to_dict()}
    for m in ("P", "PDI"):
        piv = df.pivot_table(index=["name", "seed"], columns="arm", values=m)
        res = {}
        for a in ARMS:
            if a not in piv:
                continue
            r = {"mean": float(piv[a].mean()), "n": int(piv[a].notna().sum()),
                 "mean_seed0": float(piv[a].xs(0, level="seed").mean())}
            for base in ("A:default", "C:HEU"):
                if a == base or base not in piv:
                    continue
                r[f"vs {base}"] = paired_instance(piv, a, base)
                r[f"vs {base} (seed 0 only)"] = paired_instance(piv.xs(0, level="seed", drop_level=False), a, base)
            for fam in ("item", "load"):
                sub = df[(df.arm == a) & (df.fam == fam)][m]
                r[f"mean_{fam}"] = float(sub.mean()) if len(sub) else None
            res[a] = r
        out[m] = res
    if len(D):
        lat = D.groupby("arm")["ms"].agg(["count", "median", lambda x: float(np.percentile(x, 95))])
        lat.columns = ["decisions", "median_ms", "p95_ms"]
        out["latency"] = lat.round(1).to_dict(orient="index")
        out["think_share_pct"] = {a: float(100 * D[D.arm == a]["ms"].sum() / 1000 / (out["n"][a] * T)) for a in D.arm.unique()}
        first = D.sort_values("t").groupby(["arm"]).apply(lambda g: Counter(g[g.t < 1]["action"])).to_dict()
        out["first_moves"] = {a: dict(c) for a, c in first.items()}
        out["actions"] = {a: dict(Counter(D[D.arm == a]["action"])) for a in D.arm.unique()}
        out["unparsed_or_error"] = {a: int(((D.arm == a) & D.note.str.startswith("error")).sum()) for a in D.arm.unique()}
    json.dump(out, open(ROOT / "datasets/llm_agents.json", "w"), indent=1, default=str)
    print(json.dumps(out, indent=1, default=str))


if __name__ == "__main__" and len(sys.argv) == 1:
    main()


def latex():
    d = json.load(open(ROOT / "datasets/llm_agents.json"))
    names = {"A:default": "SCIP defaults (no agent)", "C:HEU": "best fixed setting from training",
             "A:laya": "Laya as the agent (fine-tuned, $t=0$)",
             "A:llm": "LLM agent: Ornith-1.5-35B-A3B",
             "A:llm+laya": "LLM agent + Laya as a tool",
             "A:gpt6luna": "LLM agent: GPT-6 Luna (hosted)"}
    L = [r"\begin{table}[t]\centering\small", r"\begin{tabular}{lrrrrr}", r"\toprule",
         r"arm & runs & $P(120)$ & vs default & vs best fixed & thinking \\", r"\midrule"]
    for a, nm in names.items():
        r = d["P"].get(a)
        if not r:
            continue
        def g(k):
            v = r.get(k)
            return "--" if not v else f"{v['gain_pct']:+.1f}\\,\\%" + ("$^{*}$" if v["p"] < 0.05 else "")
        th = d.get("think_share_pct", {}).get(a)
        L.append(f"{nm} & {r['n']} & {r['mean']:.3f} & {g('vs A:default')} & {g('vs C:HEU')} & "
                 + ("--" if th is None else f"{th:.1f}\\,\\%") + r" \\")
    L += [r"\bottomrule", r"\end{tabular}",
          r"\caption{The end-to-end agent experiment with LLM agents: 30 held-out ML4CO instances (validation split), SCIP starting from its "
          r"defaults, one Cortex-X925 core and 8\,GiB, 120\,s of wall clock that includes every model call; two seeds (the hosted "
          r"model one). Ornith-1.5-35B-A3B runs locally (NVFP4 on vLLM, thinking off) and is asked every 20\,s; GPT-6 Luna "
          r"(ChatGPT Plus, reasoning effort low) every 30\,s. Gains in primal integral; $^{*}$ paired Wilcoxon $p<0.05$. "
          r"\emph{Thinking}: share of the budget spent waiting for the agent.}\label{tab:llm}", r"\end{table}"]
    (ROOT / "paper/generated/table_llm.tex").write_text("\n".join(L))


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "--latex":
    latex()
