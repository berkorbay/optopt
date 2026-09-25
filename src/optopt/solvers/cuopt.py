"""cuOpt wrapper. Incumbents arrive through a GetSolutionCallback that also carries the current bound.

cuOpt reports no periodic bound samples, so between incumbents the dual bound is only known at the next
incumbent and at the end. `time_limit` is measured by cuOpt from its own start; our clock includes GPU setup,
which is the honest wall-clock cost of choosing this solver.
"""
from __future__ import annotations

from cuopt.linear_programming import ParseMps, Solve, SolverSettings
import time

import numpy as np
from cuopt.linear_programming.internals import GetSolutionCallback, SetSolutionCallback

from .common import Clock, Event, Trace, finite

# cuOpt 26.08 MILPTerminationStatus (verified 2026-09-23; an earlier mapping mislabelled 8 as TimeLimit and missed 5 —
# labels only, metrics are computed from the incumbent trajectory)
_STATUS = {0: "NoTermination", 1: "Optimal", 2: "Infeasible", 3: "Unbounded", 5: "TimeLimit(no solution)",
           8: "FeasibleFound", 11: "UnboundedOrInfeasible"}


def version() -> str:
    import cuopt
    return cuopt.__version__


class _CB(GetSolutionCallback):
    def __init__(self, tr, clk, sense, xchg=None):
        super().__init__()
        self.tr, self.clk, self.sense, self.xchg = tr, clk, sense, xchg
        self.best = None

    def get_solution(self, solution, cost, bound, user_data):
        c = finite(cost[0])
        self.tr.add(Event(self.clk(), c, finite(bound[0]), None, None, "incumbent"))
        if c is not None and (self.best is None or self.sense * (c - self.best) < 0):
            self.best = c
            if self.xchg is not None and self.xchg.send and not self.xchg.echo(c):
                self.xchg.post(np.asarray(solution), c)


class _SetCB(SetSolutionCallback):
    """Hands cuOpt the partner's newest solution when it beats cuOpt's own incumbent. cuOpt decides when to ask."""
    def __init__(self, get_cb, xchg, clk, tr):
        super().__init__()
        self.g, self.xchg, self.clk, self.tr, self.calls = get_cb, xchg, clk, tr, 0

    def set_solution(self, solution, cost, bound, user_data):
        self.calls += 1
        got = self.xchg.poll()
        if got is None:
            return
        x, obj = got
        if self.g.best is not None and self.g.sense * (obj - self.g.best) >= 0:
            return
        solution[:] = x
        cost[0] = obj
        self.xchg.received.append(obj)
        self.tr.extra.setdefault("xchg_injected", []).append([round(self.clk(), 3), float(obj)])


def run(path: str, strategy: str, params: dict, budget: float, seed: int, cpu_threads: int = 3, xchg=None,
        sol_out: str | None = None, **_) -> Trace:
    rd = Clock()
    from optopt.paths import resolve  # instance paths are repository-relative
    dm = ParseMps(str(resolve(path)))
    sense = -1 if dm.get_sense() else 1
    s = SolverSettings()
    s.set_parameter("time_limit", float(budget))
    s.set_parameter("log_to_console", False)
    s.set_parameter("random_seed", int(seed))
    s.set_parameter("num_cpu_threads", int(cpu_threads))
    for k, v in params.items():
        s.set_parameter(k, v)
    tr = Trace(instance=path, solver="cuopt", strategy=strategy, seed=seed, budget=budget, sense=sense,
               read_time=rd())
    if xchg is not None:
        xchg.names = [str(n) for n in dm.get_variable_names()]
    clk = Clock()
    tr.extra["t0_epoch"] = time.time()
    cb = _CB(tr, clk, sense, xchg)
    s.set_mip_callback(cb, None)
    scb = None
    if xchg is not None and xchg.recv:  # NB: registering a SetSolutionCallback disables cuOpt's presolve
        xchg.received = []
        scb = _SetCB(cb, xchg, clk, tr)
        s.set_mip_callback(scb, None)
    sol = Solve(dm, s)
    tr.solve_wall = clk()
    st = sol.get_termination_status()
    tr.status = _STATUS.get(int(st), str(st))
    stats = sol.get_milp_stats() or {}
    # only statuses that carry a solution; otherwise the best incumbent seen (cuOpt returns a placeholder 0.0 objective
    # on error statuses — found on dano3_3, 2026-09-23)
    incs = [e.primal for e in tr.events if e.kind == "incumbent" and e.primal is not None]
    if tr.status in ("Optimal", "FeasibleFound"):
        tr.final_primal = finite(sol.get_primal_objective())
    else:
        tr.final_primal = (min(incs) if sense == 1 else max(incs)) if incs else None
    tr.final_dual = finite(stats.get("solution_bound"))
    tr.nodes = stats.get("num_nodes")
    tr.lp_iters = stats.get("num_simplex_iterations")
    tr.extra.update({"presolve_time": stats.get("presolve_time"), "max_constraint_violation":
                     stats.get("max_constraint_violation")})
    if scb is not None:
        tr.extra["set_callback_calls"] = scb.calls
    tr.events.append(Event(tr.solve_wall, tr.final_primal, tr.final_dual, tr.nodes, tr.lp_iters, "final"))
    if tr.status in ("Optimal", "FeasibleFound"):  # after the clock: store the final incumbent for the checker
        from .common import _store_solution
        _store_solution(sol_out, [str(n) for n in dm.get_variable_names()], list(sol.get_primal_solution()), tr)
    return tr
