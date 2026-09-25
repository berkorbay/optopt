"""HiGHS wrapper: one run of one strategy with a trajectory."""
from __future__ import annotations

import highspy

from .common import Clock, Event, Trace, finite


def version() -> str:
    return highspy.Highs().version()


def run(path: str, strategy: str, params: dict, budget: float, seed: int, threads: int = 1, sol_out: str | None = None,
        **_) -> Trace:
    h = highspy.Highs()
    h.setOptionValue("output_flag", False)
    h.setOptionValue("threads", threads)
    h.setOptionValue("random_seed", seed)
    h.setOptionValue("time_limit", float(budget))
    for k, v in params.items():
        h.setOptionValue(k, v)
    rd = Clock()
    from optopt.paths import resolve  # instance paths are repository-relative
    h.readModel(str(resolve(path)))
    lp = h.getLp()
    sense = -1 if lp.sense_ == highspy.ObjSense.kMaximize else 1
    tr = Trace(instance=path, solver="highs", strategy=strategy, seed=seed, budget=budget, sense=sense,
               read_time=rd())
    clk = Clock()

    def on_improve(e):
        d = e.data_out
        tr.add(Event(clk(), finite(d.mip_primal_bound), finite(d.mip_dual_bound), int(d.mip_node_count),
                     None, "incumbent"))

    def on_sample(e):
        d = e.data_out
        tr.add(Event(clk(), finite(d.mip_primal_bound), finite(d.mip_dual_bound), int(d.mip_node_count),
                     None, "sample"))

    h.cbMipImprovingSolution.subscribe(on_improve)
    h.cbMipInterrupt.subscribe(on_sample)
    h.cbMipLogging.subscribe(on_sample)
    h.run()
    tr.solve_wall = clk()
    info = h.getInfo()
    tr.status = h.modelStatusToString(h.getModelStatus())
    tr.final_primal = finite(info.objective_function_value) if info.primal_solution_status == 2 else None
    tr.final_dual = finite(info.mip_dual_bound)
    tr.nodes = int(info.mip_node_count)
    tr.lp_iters = int(info.simplex_iteration_count)
    tr.events.append(Event(tr.solve_wall, tr.final_primal, tr.final_dual, tr.nodes, tr.lp_iters, "final"))
    if tr.final_primal is not None:  # after the clock: store the final incumbent for the independent checker
        from .common import _store_solution
        _store_solution(sol_out, list(h.getLp().col_names_), list(h.getSolution().col_value), tr)
    return tr
