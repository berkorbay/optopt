"""Example 2 — turn a trajectory into the primal integral, and compare two SCIP settings.

  python tutorials/examples/ex02_primal_integral.py
"""
import json

from common import set_cover_mps

from optopt.analysis.metrics import primal_dual_integral, primal_integral, time_to_target
from optopt.solvers import scip

inst = set_cover_mps("/tmp/tut_setcover.mps", seed=1)
T = 20
runs = {"default": scip.run(inst, "D", {}, T, 0),
        "aggressive heuristics": scip.run(inst, "HEU", {}, T, 0, schedule=("HEU", "D", 2.0))}
ref = min(e.primal for tr in runs.values() for e in tr.events if e.primal is not None)  # best value seen by any run
print(f"reference (best found by either run): {ref}")
for name, tr in runs.items():
    t = json.loads(tr.to_json())
    print(f"{name:22s} P({T}) = {primal_integral(t, ref, T):.3f}   PDI({T}) = {primal_dual_integral(t, T):.3f}   "
          f"time to 1% = {time_to_target(t, ref, T):.1f} s")
