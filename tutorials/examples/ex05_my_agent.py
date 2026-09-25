"""Example 5 — write your own agent in a few lines and run it inside SCIP's wall-clock budget.

The agent is called every `interval` seconds with the solver state and may return None, ("set", SETTING) or
("restart",). Its own thinking time counts against the budget, exactly as in the paper's main experiment.

  python tutorials/examples/ex05_my_agent.py
"""
import json

from common import set_cover_mps

from optopt.agents.bandit import BanditAgent
from optopt.analysis.metrics import primal_integral
from optopt.solvers import scip


class StallAgent:
    """If no new incumbent for 5 s, switch to aggressive heuristics; once one is found, go back to default."""
    interval = 2.0

    def reset(self, budget):
        self.budget = budget

    def decide(self, st):
        if st["inc_age"] > 5 and st["setting"] != "HEU":
            return ("set", "HEU")
        if st["inc_age"] < 2 and st["setting"] == "HEU":
            return ("set", "D")
        return None


inst = set_cover_mps("/tmp/tut_setcover.mps", seed=1)
T = 20
res = {"default": scip.run(inst, "D", {}, T, 0),
       "stall agent": scip.run(inst, "stall", {}, T, 0, agent=StallAgent()),
       "bandit agent": scip.run(inst, "bandit", {}, T, 0, agent=BanditAgent(interval=4.0))}
ts = {k: json.loads(v.to_json()) for k, v in res.items()}
ref = min(e["primal"] for t in ts.values() for e in t["events"] if e["primal"] is not None)
for k, t in ts.items():
    log = (t.get("extra") or {}).get("agent_log", [])
    print(f"{k:13s} P({T}) = {primal_integral(t, ref, T):.3f}   decisions: {[(d[0], d[1]) for d in log if d[1]][:6]}")
