"""SCIP wrapper: incumbent events via BESTSOLFOUND, bound samples via NODESOLVED (throttled)."""
from __future__ import annotations

from pyscipopt import SCIP_EVENTTYPE, SCIP_HEURTIMING, SCIP_PARAMEMPHASIS, SCIP_PARAMSETTING, SCIP_RESULT, Eventhdlr, Heur, Model

import os
import time

from .common import Clock, Event, Trace, finite

EMPHASIS = {
    "heuristics_aggressive": ("heur", SCIP_PARAMSETTING.AGGRESSIVE),
    "separating_aggressive": ("sepa", SCIP_PARAMSETTING.AGGRESSIVE),
    "separating_off": ("sepa", SCIP_PARAMSETTING.OFF),
    "presolving_aggressive": ("pres", SCIP_PARAMSETTING.AGGRESSIVE),
    "feasibility": ("emph", SCIP_PARAMEMPHASIS.FEASIBILITY),
    "optimality": ("emph", SCIP_PARAMEMPHASIS.OPTIMALITY),
}


def version() -> str:
    return str(Model().version())


SETTINGS = {  # Track B: named in-solver settings that can be applied at the start or mid-solve
    "D": {},
    "DFS": {"nodesel": "dfs"},
    "BFS": {"nodesel": "bfs"},
    "HEU": {"heur": SCIP_PARAMSETTING.AGGRESSIVE},
    "NOC": {"sepa": SCIP_PARAMSETTING.OFF},
    "PSC": {"branch": "pscost"},
    "INF": {"branch": "inference"},
    "HOFF": {"heur": SCIP_PARAMSETTING.OFF},
}
_NODESEL_DEFAULT = {"dfs": 0, "bfs": 100000}
_BRANCH_DEFAULT = {"pscost": 2000, "inference": 1000}


def apply_setting(m: Model, name: str, prev: str | None = None):
    """Apply a named setting; undo the previous one first (node selector priority, heuristic/separation emphasis)."""
    if prev:
        pv = SETTINGS[prev]
        if "nodesel" in pv:
            m.setParam(f"nodeselection/{pv['nodesel']}/stdpriority", _NODESEL_DEFAULT[pv["nodesel"]])
        if "branch" in pv:
            m.setParam(f"branching/{pv['branch']}/priority", _BRANCH_DEFAULT[pv["branch"]])
        if "heur" in pv:
            m.setHeuristics(SCIP_PARAMSETTING.DEFAULT)
        if "sepa" in pv:
            m.setSeparating(SCIP_PARAMSETTING.DEFAULT)
    st = SETTINGS[name]
    if "branch" in st:
        m.setParam(f"branching/{st['branch']}/priority", 1_000_000)
    if "nodesel" in st:
        m.setParam(f"nodeselection/{st['nodesel']}/stdpriority", 1_000_000)
    if "heur" in st:
        m.setHeuristics(st["heur"])
    if "sepa" in st:
        m.setSeparating(st["sepa"])


class _Hdlr(Eventhdlr):
    def __init__(self, tr: Trace, clk: Clock, schedule=None, budget=0.0, agent=None, setting="D", xchg=None):
        self.tr, self.clk, self.last = tr, clk, -1.0
        self.xchg, self.xvars, self.injecting = xchg, None, False  # solution exchange (solvers/xchg.py)
        self.schedule, self.budget, self.switched = schedule, budget, False
        self.last_inc_t = 0.0
        self.agent, self.setting, self.n_inc = agent, setting, 0
        self.next_decision = getattr(agent, "first_at", agent.interval) if agent else None  # LLM/Laya agents: first call at start
        self.last_nodes, self.last_dec_t, self.history = 0, 0.0, []

    def eventinit(self):
        self.model.catchEvent(SCIP_EVENTTYPE.BESTSOLFOUND, self)
        self.model.catchEvent(SCIP_EVENTTYPE.NODESOLVED, self)

    def eventexit(self):
        self.model.dropEvent(SCIP_EVENTTYPE.BESTSOLFOUND, self)
        self.model.dropEvent(SCIP_EVENTTYPE.NODESOLVED, self)

    def eventexec(self, event):
        m, t = self.model, self.clk()
        inc = event.getType() == SCIP_EVENTTYPE.BESTSOLFOUND
        if inc:
            self.last_inc_t = t
            self.n_inc += 1
        if self.agent is not None and t >= self.next_decision:
            self._agent_step(m, t)
        if self.schedule and not self.switched:
            first, then, when = self.schedule
            if when == "inc":
                due = m.getNSols() > 0
            elif isinstance(when, str) and when.startswith("stall"):  # no incumbent improvement for frac*budget
                frac = float(when[5:]) / 100
                due = t >= frac * self.budget and t - self.last_inc_t >= frac * self.budget
            else:
                due = t >= when * self.budget
            if due:
                if then == "RESTART":
                    m.restartSolve()
                else:
                    apply_setting(m, then, prev=first)
                self.switched = True
                self.tr.extra["switch_t"] = t
        if self.xchg is not None and not self.injecting:
            self._exchange(m, inc, node=bool(int(event.getType()) & int(SCIP_EVENTTYPE.NODESOLVED)))
        if not inc and t - self.last < 0.5:
            return
        self.last = t
        if inc:  # at BESTSOLFOUND getPrimalbound() still holds the PREVIOUS incumbent — read the new solution itself
            sol = m.getBestSol()
            pv = finite(m.getSolObjVal(sol)) if sol is not None else finite(m.getPrimalbound())
        else:
            pv = finite(m.getPrimalbound())
        self.tr.add(Event(t, pv, finite(m.getDualbound()), int(m.getNNodes()),
                          int(m.getNLPIterations()), "incumbent" if inc else "sample"))


def _agent_step(self, m, t):
    # at BESTSOLFOUND getPrimalbound() still holds the previous incumbent (same lag as the recorder) — read the best
    # solution itself so the agent sees the solution it is being told about (review 2026-09-24)
    sol = m.getBestSol() if m.getNSols() > 0 else None
    p = finite(m.getSolObjVal(sol)) if sol is not None else None
    d = finite(m.getDualbound())
    gap = abs(p - d) / max(abs(p), abs(d), 1e-9) if p is not None and d is not None else 1.0
    nodes = int(m.getNNodes())
    st = dict(t=t, budget=self.budget, primal=p, dual=d, pd_gap=min(1.0, gap), n_inc=self.n_inc,
              inc_age=t - self.last_inc_t if self.n_inc else t, nodes=nodes,
              node_rate=(nodes - self.last_nodes) / max(t - self.last_dec_t, 1e-9) if nodes >= self.last_nodes else 0.0,
              lp_iters=int(m.getNLPIterations()), setting=self.setting, history=list(self.history))
    self.tr.extra.setdefault("agent_ctx", []).append(  # solver state at the call: where in the solve the agent acts
        dict(t=round(t, 3), stage=m.getStageName(), nodes=nodes, lp_iters=st["lp_iters"], n_sols=int(m.getNSols()),
             presolve_s=round(m.getPresolvingTime(), 3)))
    t0 = self.clk()
    act = self.agent.decide(st)
    think = self.clk() - t0
    if act:
        if act[0] == "set" and act[1] != self.setting:
            apply_setting(m, act[1], prev=self.setting)
            self.setting = act[1]
        elif act[0] == "restart":
            m.restartSolve()
    self.history.append((round(t, 2), act, round(st["pd_gap"], 6)))
    self.tr.extra.setdefault("agent_log", []).append([round(t, 2), act, round(think * 1000, 2)]
                                                   + ([self.agent.note] if getattr(self.agent, "note", None) else []))
    if hasattr(self.agent, "note"):
        self.agent.note = None
    self.last_nodes, self.last_dec_t = nodes, t
    self.next_decision = t + self.agent.interval


def _exchange(self, m, inc, node=False):
    """Post our new incumbent. Receiving is done by _XchgHeur (a SCIP heuristic plugin, the supported interface for
    adding solutions); the event-handler injection below is kept only for xchg.inject == "event" (2026-09-23 night,
    where it crashed SCIP on 9 of 80 instances per arm)."""
    xb, (names, idx) = self.xchg, self.xvars
    if inc and xb.send:
        sol = m.getBestSol()
        if sol is not None:
            ov = m.getVars(transformed=False)
            x = [0.0] * len(names)
            for v, j in zip(ov, idx):
                x[j] = m.getSolVal(sol, v)
            xb.post(x, m.getSolObjVal(sol))
    # Inject only between nodes: inside a heuristic (probing, diving) adding a solution corrupts the solve
    # (found 2026-09-23 on h80x6320d). A long root phase therefore cannot take outside solutions.
    if getattr(xb, "inject", "heur") != "event" or not node or m.inProbing():
        return
    self.tr.extra["xchg_polls"] = self.tr.extra.get("xchg_polls", 0) + 1
    got = xb.poll()
    if got is None:
        return
    x, obj = got
    sense = self.tr.sense
    if m.getNSols() > 0 and sense * (obj - m.getPrimalbound()) >= -1e-9 * max(1.0, abs(obj)):
        return  # not better than ours
    s = m.createOrigSol()
    for v, j in zip(m.getVars(transformed=False), idx):
        m.setSolVal(s, v, float(x[j]))
    self.injecting = True  # trySol fires BESTSOLFOUND re-entrantly; do not echo the partner's solution back
    try:
        ok = m.trySol(s, free=True)
    finally:
        self.injecting = False
    self.tr.extra.setdefault("xchg_injected", []).append([round(self.clk(), 3), float(obj), bool(ok)])


_Hdlr._agent_step = _agent_step
_Hdlr._exchange = _exchange


class _XchgHeur(Heur):
    """Receives the partner's solutions as a SCIP primal heuristic: called before each node and during the root LP
    loop; when the partner has posted something better than SCIP's incumbent, hand it to SCIP with trySol and report
    FOUNDSOL. Cheap when idle (one stat of the mailbox file)."""

    def __init__(self, hdlr):
        super().__init__()
        self.h = hdlr

    def heurexec(self, heurtiming, nodeinfeasible):
        h, m = self.h, self.model
        h.tr.extra["xchg_polls"] = h.tr.extra.get("xchg_polls", 0) + 1
        got = h.xchg.poll()
        if got is None:
            return {"result": SCIP_RESULT.DIDNOTRUN}
        x, obj = got
        if m.getNSols() > 0 and h.tr.sense * (obj - m.getPrimalbound()) >= -1e-9 * max(1.0, abs(obj)):
            return {"result": SCIP_RESULT.DIDNOTFIND}
        names, idx = h.xvars
        s = m.createOrigSol()
        for v, j in zip(m.getVars(transformed=False), idx):
            m.setSolVal(s, v, float(x[j]))
        h.injecting = True  # trySol fires BESTSOLFOUND; do not echo the partner's solution back
        try:
            ok = m.trySol(s, free=True)
        finally:
            h.injecting = False
        h.tr.extra.setdefault("xchg_injected", []).append([round(h.clk(), 3), float(obj), bool(ok)])
        return {"result": SCIP_RESULT.FOUNDSOL if ok else SCIP_RESULT.DIDNOTFIND}


def run(path: str, strategy: str, params: dict, budget: float, seed: int, emphasis: str | None = None,
        mem_mb: int | None = None, schedule=None, sol_out: str | None = None, agent=None, xchg=None, **_) -> Trace:
    """schedule: None, or (first, then, when) with when = "inc" (first incumbent) or a budget fraction."""
    m = Model()
    m.hideOutput()
    m.setParam("limits/time", float(budget))
    import os
    m.setParam("limits/memory", float(mem_mb or int(os.environ.get("OPTOPT_SCIP_MEM_MB", "2000"))))
    m.setParam("randomization/randomseedshift", int(seed))
    m.setParam("parallel/maxnthreads", 1)
    if emphasis:
        kind, val = EMPHASIS[emphasis]
        {"heur": m.setHeuristics, "sepa": m.setSeparating, "pres": m.setPresolve,
         "emph": m.setEmphasis}[kind](val)
    for k, v in params.items():
        m.setParam(k, v)
    if schedule:
        apply_setting(m, schedule[0])
    rd = Clock()
    from optopt.paths import resolve  # instance paths are repository-relative
    m.readProblem(str(resolve(path)))
    sense = -1 if m.getObjectiveSense() == "maximize" else 1
    tr = Trace(instance=path, solver="scip", strategy=strategy, seed=seed, budget=budget, sense=sense,
               read_time=rd())
    tr.extra["incumbent_values_exact"] = True  # recorder fixed 2026-09-23 19:30 (see analysis/fix_scip_traces.py)
    xvars = None
    if xchg is not None:  # exchange in SCIP's own variable order; publish it once, before the clock starts
        ov = m.getVars(transformed=False)
        xchg.write_order([v.name for v in ov])
        xvars = ([v.name for v in ov], list(range(len(ov))))
    clk = Clock()
    tr.extra["t0_epoch"] = time.time()
    if agent is not None:
        agent.reset(float(budget))
    h = _Hdlr(tr, clk, schedule, float(budget), agent=agent, setting=schedule[0] if schedule else "D", xchg=xchg)
    h.xvars = xvars
    m.includeEventhdlr(h, "trace", "trajectory recorder")
    if xchg is not None and xchg.recv and getattr(xchg, "inject", "heur") == "heur":
        m.includeHeur(_XchgHeur(h), "xchg", "solutions from a partner solver", "Y", priority=1_000_000, freq=1,
                      freqofs=0, maxdepth=-1,
                      timingmask=SCIP_HEURTIMING.BEFORENODE | SCIP_HEURTIMING.DURINGLPLOOP, usessubscip=False)
        tr.extra["xchg_inject"] = "heur"
    m.optimize()
    tr.solve_wall = clk()
    tr.status = m.getStatus()
    tr.final_primal = finite(m.getPrimalbound()) if m.getNSols() > 0 else None
    tr.final_dual = finite(m.getDualbound())
    tr.nodes = int(m.getNNodes())
    tr.lp_iters = int(m.getNLPIterations())
    tr.events.append(Event(tr.solve_wall, tr.final_primal, tr.final_dual, tr.nodes, tr.lp_iters, "final"))
    if os.environ.get("OPTOPT_SCIP_STATS"):  # after the clock: per-heuristic statistics for mechanism checks
        import json as _json
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            f = os.path.join(td, "stats.json")
            m.writeStatisticsJson(f)
            d = _json.load(open(f))
        tr.extra["scip_stats"] = {
            "presolve_s": m.getPresolvingTime(),
            "heuristics": {k: {x: v.get(x) for x in ("time", "calls", "solutions_found", "best_solutions_found")}
                           for k, v in d.get("heuristics", {}).get("plugins", {}).items()
                           if v.get("calls") or v.get("solutions_found")},
            "root": d.get("root")}
    if sol_out and m.getNSols() > 0:  # issue #25: keep the incumbent so it can be checked independently
        import gzip
        import json as _json
        sol = m.getBestSol()
        vals = {v.name: m.getSolVal(sol, v) for v in m.getVars()}
        with gzip.open(sol_out, "wt") as fh:
            _json.dump({k: v for k, v in vals.items() if v != 0.0}, fh)
        from optopt.paths import rel
        tr.extra["sol_file"] = rel(sol_out)
    return tr
