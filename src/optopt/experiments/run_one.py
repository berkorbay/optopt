"""Run one (instance, strategy, seed, budget) in this process and write its trace JSON. Invoked by the pool."""
from __future__ import annotations

import argparse
import json
import os
import sys
import traceback
from pathlib import Path


from optopt.portfolio.strategies import STRATEGIES  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("instance")
    ap.add_argument("strategy")
    ap.add_argument("--budget", type=float, required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--xchg-dir", default=None, help="solution exchange mailbox directory (experiments/xchg_pair.py)")
    ap.add_argument("--xchg", default="", help="'send', 'recv' or 'send,recv' for this side")
    a = ap.parse_args()
    st = STRATEGIES[a.strategy]
    if st["solver"] == "highs":
        from optopt.solvers import highs as mod
    elif st["solver"] == "scip":
        from optopt.solvers import scip as mod
    else:
        from optopt.solvers import cuopt as mod
    try:
        sol_out = None
        if True:  # every solver stores its final incumbent (SCIP only until 2026-09-24; review)
            sd = Path(a.out).parent.parent.parent / "sol" / Path(a.out).parent.name
            sd.mkdir(parents=True, exist_ok=True)
            sol_out = str(sd / (Path(a.out).stem + ".json.gz"))
        agent = None
        if st.get("agent"):
            import importlib
            mod_name, cls = st["agent"].split(":")
            agent = getattr(importlib.import_module(f"optopt.agents.{mod_name}"), cls)(**st.get("agent_kw", {}))
            agent.instance = Path(a.instance).name.replace(".mps.gz", "")
        xchg = None
        if a.xchg_dir:
            from optopt.solvers.xchg import Mailbox
            me = "scip" if st["solver"] == "scip" else "cuopt"
            xchg = Mailbox(a.xchg_dir, me, "cuopt" if me == "scip" else "scip",
                           send="send" in a.xchg, recv="recv" in a.xchg)
        tr = mod.run(a.instance, a.strategy, st["params"], a.budget, a.seed, emphasis=st.get("emphasis"),
                     schedule=st.get("schedule"), sol_out=sol_out, agent=agent, xchg=xchg)
        if xchg is not None:
            tr.extra["xchg_mode"] = a.xchg
            tr.extra["xchg_log"] = [[round(t, 3), k, o] for t, k, o in xchg.log]
        from optopt.experiments.identity import config_hash, version
        tr.extra["config_hash"] = config_hash(a.instance, a.strategy, a.budget, a.seed)
        tr.extra["optopt_version"] = version()
        txt = tr.to_json()
    except Exception as e:  # recorded, not raised: a crash is a result for this strategy
        txt = json.dumps({"instance": a.instance, "solver": st["solver"], "strategy": a.strategy,
                          "seed": a.seed, "budget": a.budget, "error": f"{type(e).__name__}: {e}",
                          "tb": traceback.format_exc()[-2000:], "events": []})
    tmp = a.out + ".tmp"
    with open(tmp, "w") as f:
        f.write(txt)
    os.replace(tmp, a.out)


if __name__ == "__main__":
    main()
