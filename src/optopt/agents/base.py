"""Agent interface for the main experiment (D-004, issue #28).

The agent runs INSIDE the solver's wall-clock budget: SCIP calls `decide(state)` from an event handler every
`interval` seconds, and SCIP's time limit is wall clock (timing/clocktype=2, verified), so every millisecond the
agent spends thinking is charged to the run.

state: dict with t, budget, primal, dual, pd_gap (relative, 1 if missing), n_inc, inc_age (s since last incumbent,
       = t if none), nodes, node_rate (nodes/s over the last interval), lp_iters, setting (current), history
       (list of (t, action, pd_gap_before)).
return: None (continue) | ("set", "<SETTING>") | ("restart",)
"""


class Agent:
    name = "base"
    interval = 10.0

    def reset(self, budget: float):
        self.budget = budget

    def decide(self, state: dict):
        return None
