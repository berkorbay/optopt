"""The strategy portfolio (spec §10, reduced to the §26 first-milestone set).

Each strategy is a solver plus a small dict of parameter overrides. "Tuned" here means *primal-focused*: the
milestone metric is time-to-good-solution, so the non-default arm of each solver shifts effort from bound
proving to finding incumbents. The dict is the extension point toward the ~20-strategy portfolio.
"""
from pathlib import Path

STRATEGIES: dict[str, dict] = {
    # HiGHS 1.15
    "H0": {"solver": "highs", "params": {}},
    "H1": {
        "solver": "highs",
        "params": {
            "mip_heuristic_effort": 0.3,  # default 0.05
        },
    },
    # SCIP 10
    "S0": {"solver": "scip", "params": {}},
    "S1": {"solver": "scip", "emphasis": "heuristics_aggressive", "params": {}},
    # cuOpt 26.08 (GPU heuristics + CPU branch-and-bound)
    "C0": {"solver": "cuopt", "params": {}},
    "C1": {
        "solver": "cuopt",
        "params": {
            # primal-focused: skip cut rounds (default 10), more RINS time
            "mip_cut_passes": 0,
            "mip_hyper_heuristic_rins_time_limit": 10.0,  # default 3.0
        },
    },
}

MILESTONE = ["H0", "H1", "S0", "S1", "C0", "C1"]


# Track B · B0: SCIP in-solver settings and fixed mid-solve schedules (first, then, when)
# when = "inc": switch at the first incumbent; a float: switch at that fraction of the budget.
B0_ARMS = {
    "B:D": ("D", None, None), "B:DFS": ("DFS", None, None), "B:BFS": ("BFS", None, None),
    "B:HEU": ("HEU", None, None), "B:NOC": ("NOC", None, None),
    "B:DFS>D@inc": ("DFS", "D", "inc"), "B:DFS>BFS@inc": ("DFS", "BFS", "inc"),
    "B:HEU>D@25": ("HEU", "D", 0.25), "B:NOC>D@25": ("NOC", "D", 0.25), "B:NOC>D@50": ("NOC", "D", 0.5),
    "B:D>BFS@50": ("D", "BFS", 0.5), "B:D>DFS@50": ("D", "DFS", 0.5), "B:D>HEU@50": ("D", "HEU", 0.5),
}
B0_STATIC = ["B:D", "B:DFS", "B:BFS", "B:HEU", "B:NOC"]
for _k, (_a, _b, _w) in B0_ARMS.items():
    STRATEGIES[_k] = {"solver": "scip", "params": {}, "schedule": (_a, _b, _w) if _b else (_a, "D", 2.0)}


# Track B · B2: wider action space (restart, branching rule, heuristic scheduling), 2026-09-23 day
B2_ARMS = {
    "C:D": ("D", None, None), "C:NOC": ("NOC", None, None), "C:PSC": ("PSC", None, None),
    "C:INF": ("INF", None, None), "C:HOFF": ("HOFF", None, None), "C:HEU": ("HEU", None, None),
    "C:D+RST@25": ("D", "RESTART", 0.25), "C:D+RST@stall20": ("D", "RESTART", "stall20"),
    "C:PSC>D@25": ("PSC", "D", 0.25), "C:D>PSC@25": ("D", "PSC", 0.25),
    "C:HEU>HOFF@25": ("HEU", "HOFF", 0.25), "C:HOFF>HEU@stall20": ("HOFF", "HEU", "stall20"),
}
B2_STATIC = ["C:D", "C:NOC", "C:PSC", "C:INF", "C:HOFF", "C:HEU"]
for _k, (_a, _b, _w) in B2_ARMS.items():
    STRATEGIES[_k] = {"solver": "scip", "params": {}, "schedule": (_a, _b, _w) if _b else (_a, "D", 2.0)}


# Main experiment (D-004) agents on SCIP — every agent starts from default settings
AGENT_ARMS = {
    "A:default": {"solver": "scip", "params": {}},
    "A:bandit": {"solver": "scip", "params": {}, "agent": "bandit:BanditAgent", "agent_kw": {"interval": 10.0}},
    "A:rules": {"solver": "scip", "params": {}, "agent": "rules:RulesAgent", "agent_kw": {"interval": 5.0}},
    "A:bandit5": {"solver": "scip", "params": {}, "agent": "bandit:BanditAgent", "agent_kw": {"interval": 5.0}},
    # diagnosis first move (LightGBM prediction from instance features, datasets/diag_pred.json) + bandit fallback
    "A:diagbandit": {"solver": "scip", "params": {}, "agent": "bandit:BanditAgent",
                     "agent_kw": {"interval": 5.0, "prior_file": "datasets/diag_pred.json"}},
}
# D-004 2x2 (2026-09-24): Laya as agent / LLM agent / LLM with Laya as a tool; hosted LLM arm
AGENT_ARMS.update({
    "A:laya": {"solver": "scip", "params": {}, "agent": "llm:LayaAgent", "agent_kw": {}},
    "A:llm": {"solver": "scip", "params": {}, "agent": "llm:LLMAgent", "agent_kw": {"backend": "local", "interval": 20.0}},
    "A:llm+laya": {"solver": "scip", "params": {}, "agent": "llm:LLMAgent",
                   "agent_kw": {"backend": "local", "laya_tool": True, "interval": 20.0}},
    "A:gpt6luna": {"solver": "scip", "params": {}, "agent": "llm:LLMAgent", "agent_kw": {"backend": "gpt", "interval": 30.0}},
    # timing-matched controls (review 2026-09-24)
    "A:heu_cb": {"solver": "scip", "params": {}, "agent": "llm:FixedAgent", "agent_kw": {"setting": "HEU"}},
    "A:heu_10": {"solver": "scip", "params": {}, "agent": "llm:FixedAgent", "agent_kw": {"setting": "HEU", "at": 10}},
    "A:llm_first": {"solver": "scip", "params": {}, "agent": "llm:LLMAgent", "agent_kw": {"backend": "local", "first_only": True}},
})
STRATEGIES.update(AGENT_ARMS)
