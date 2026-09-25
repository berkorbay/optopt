"""Example 1 — solve one MIP with two solvers and watch the incumbent and the bound move.

  python tutorials/examples/ex01_first_mip.py
"""
from common import set_cover_mps

from optopt.solvers import highs, scip

inst = set_cover_mps("/tmp/tut_setcover.mps", seed=1)
for mod, name in ((scip, "SCIP"), (highs, "HiGHS")):
    tr = mod.run(inst, name, {}, budget=20, seed=0)
    print(f"\n{name}: status={tr.status}, final incumbent={tr.final_primal}, bound={tr.final_dual}")
    print("  time(s)   incumbent      bound")
    for e in tr.events:
        if e.kind == "incumbent":
            fmt = lambda v: f"{v:10.1f}" if v is not None else "         -"  # noqa: E731
            print(f"  {e.t:7.2f}  {fmt(e.primal)}  {fmt(e.dual)}")
