"""Example 4 — static setting vs a mid-solve switch in SCIP (the paper's 'choose, don't switch' test in miniature).

  python tutorials/examples/ex04_switching.py
"""
import json

from common import set_cover_mps

from optopt.analysis.metrics import primal_integral
from optopt.solvers import scip

T = 20
arms = {"default": ("D", "D", 2.0), "separation off": ("NOC", "D", 2.0),
        "separation off, then default at 25%": ("NOC", "D", 0.25), "default, then restart at 25%": ("D", "RESTART", 0.25)}
for seed_inst in (1, 2, 3):
    inst = set_cover_mps(f"/tmp/tut_setcover_{seed_inst}.mps", seed=seed_inst)
    res = {k: json.loads(scip.run(inst, k, {}, T, 0, schedule=v).to_json()) for k, v in arms.items()}
    ref = min(e["primal"] for t in res.values() for e in t["events"] if e["primal"] is not None)
    print(f"instance {seed_inst}: " + "  ".join(f"{k} P={primal_integral(t, ref, T):.3f}" for k, t in res.items()))
