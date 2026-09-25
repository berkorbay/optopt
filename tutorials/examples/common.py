"""Shared helpers for the tutorial examples: a random set-cover generator (no downloads needed) and repo imports."""
import sys
from pathlib import Path

import numpy as np

from optopt.paths import WORK as ROOT  # the workspace (cwd or $OPTOPT_HOME)


def set_cover_mps(path, rows=600, cols=1200, density=0.05, seed=0):
    """Write a random weighted set-cover MIP (Balas & Ho style) as MPS: min c·x, every row covered at least once."""
    rng = np.random.default_rng(seed)
    from pyscipopt import Model, quicksum
    m = Model("setcover")
    x = [m.addVar(vtype="B", obj=float(rng.integers(1, 101)), name=f"x{j}") for j in range(cols)]
    for i in range(rows):
        cover = rng.choice(cols, size=max(2, int(density * cols)), replace=False)
        m.addCons(quicksum(x[j] for j in cover) >= 1, name=f"r{i}")
    m.writeProblem(str(path))
    return str(path)
