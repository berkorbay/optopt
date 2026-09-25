"""Independent feasibility check of stored incumbents (issue #25).

For every stored solution: re-read the model with HiGHS (not the solver that produced it), then check
bounds, integrality and the objective in exact rational arithmetic (fractions.Fraction of the parsed coefficients),
and every row by a float pass followed by an exact re-check of any row that could be near the tolerance:
  - variable bounds and integrality (|x - round(x)| <= tol for integer columns),
  - every row: lhs - tol_r <= a·x <= rhs + tol_r with tol_r = tol * max(1, |rhs|)   (MIPLIB-checker style),
  - the objective recomputed from the solution vs the objective the solver reported (relative 1e-6).
The tolerance is the solvers' own feasibility tolerance (1e-6); exact arithmetic removes float summation error
from the *check*, not from the solver's answer.

  python analysis/check_solutions.py traces/sol/<set> [--workers 8]   -> datasets/solcheck_<set>.csv
Untimed work: run it on the efficiency cores (taskset -c 0-4,10-14).
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from fractions import Fraction
from pathlib import Path

import numpy as np

from optopt.paths import WORK as ROOT  # the workspace (cwd or $OPTOPT_HOME)

TOL = 1e-6
_MODEL_CACHE: dict = {}


def load_model(path):
    if path in _MODEL_CACHE:
        return _MODEL_CACHE[path]
    import highspy
    h = highspy.Highs()
    h.setOptionValue("output_flag", False)
    from optopt.paths import resolve  # instance paths are repository-relative
    h.readModel(str(resolve(path)))
    lp = h.getLp()
    names = list(lp.col_names_)
    integ = [int(v) > 0 for v in lp.integrality_] if len(lp.integrality_) else [False] * lp.num_col_
    a = lp.a_matrix_
    # np.array (a COPY), never np.asarray: highspy returns views into memory owned by `h`, which is freed when this
    # function returns; cached views then read freed memory and the check becomes nondeterministic (found 2026-09-24:
    # the same solution passed and failed on drayage-100-23 depending on what the worker had checked before)
    m = (names, np.array(lp.col_lower_), np.array(lp.col_upper_), integ, np.array(a.start_),
         np.array(a.index_), np.array(a.value_), np.array(lp.row_lower_), np.array(lp.row_upper_),
         np.array(lp.col_cost_), float(lp.offset_), lp.num_row_)
    _MODEL_CACHE[path] = m
    return m


def check(args):
    sol_file, trace_file = args
    tr = json.loads(Path(trace_file).read_text())
    names, lb, ub, integ, start, index, value, rl, ru, cost, offset, nrow = load_model(tr["instance"])
    if not names or nrow is None:
        raise ValueError(f"model {tr['instance']} could not be read (no columns)")
    vals = json.load(gzip.open(sol_file, "rt"))
    x = [Fraction(vals.get(n, 0.0)) for n in names]
    known = set(names)  # built once (was rebuilt per variable: O(n^2) on large models)
    unknown = [k for k in vals if k not in known]
    worst_bound = worst_int = worst_row = 0.0
    for j, xj in enumerate(x):
        if np.isfinite(lb[j]):
            worst_bound = max(worst_bound, float(Fraction(lb[j]) - xj))
        if np.isfinite(ub[j]):
            worst_bound = max(worst_bound, float(xj - Fraction(ub[j])))
        if integ[j]:
            worst_int = max(worst_int, float(abs(xj - round(xj))))
    # rows: float activity first (scipy sparse), exact Fraction re-check only for rows near the tolerance
    import scipy.sparse as sp
    xf = np.array([float(v) for v in x])
    # copy=True: scipy may sort/merge duplicate entries IN PLACE, which would rewrite the cached model arrays
    A = sp.csc_matrix((value, index, start), shape=(nrow, len(x)), copy=True)
    actf = A @ xf
    absf = abs(A) @ np.abs(xf)  # bound on float rounding error scale
    with np.errstate(invalid="ignore"):  # np.where evaluates both branches; infinite row bounds give inf/inf there
        lo_v = np.where(np.isfinite(rl), (rl - actf) / np.maximum(1.0, np.abs(rl)), -np.inf)
        up_v = np.where(np.isfinite(ru), (actf - ru) / np.maximum(1.0, np.abs(ru)), -np.inf)
    viol = np.maximum(lo_v, up_v)
    err = 1e-12 * np.maximum(1.0, absf)
    near = np.where(viol > TOL - 1e-3 * TOL - err)[0]  # anything that could possibly exceed the tolerance
    Acsr = A.tocsr()
    worst_row = float(max(0.0, viol.max(initial=0.0)))
    for i in near:  # exact rational arithmetic for these rows
        a = Fraction(0)
        for k in range(Acsr.indptr[i], Acsr.indptr[i + 1]):
            a += Fraction(Acsr.data[k]) * x[Acsr.indices[k]]
        v = -1.0
        if np.isfinite(rl[i]):
            v = max(v, float(Fraction(rl[i]) - a) / max(1.0, abs(rl[i])))
        if np.isfinite(ru[i]):
            v = max(v, float(a - Fraction(ru[i])) / max(1.0, abs(ru[i])))
        worst_row = max(worst_row, v)
    obj = float(sum(Fraction(cost[j]) * x[j] for j in range(len(x)) if x[j] != 0) + Fraction(offset))
    rep = tr.get("final_primal")
    obj_rel = abs(obj - rep) / max(1.0, abs(rep)) if rep is not None else float("nan")
    ok = worst_bound <= TOL and worst_int <= TOL and worst_row <= TOL and not unknown and (
        rep is None or obj_rel <= 1e-6)
    return dict(sol=Path(sol_file).name, instance=Path(tr["instance"]).name, strategy=tr["strategy"],
                seed=tr["seed"], feasible=ok, worst_bound=worst_bound, worst_int=worst_int, worst_row_rel=worst_row,
                obj_recomputed=obj, obj_reported=rep, obj_rel_err=obj_rel, unknown_vars=len(unknown))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sol_dir")
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    sd = Path(a.sol_dir)
    raw = ROOT / "traces/raw" / sd.name
    jobs = [(str(f), str(raw / f.name.replace(".json.gz", ".json"))) for f in sorted(sd.glob("*.json.gz"))]
    jobs = [j for j in jobs if Path(j[1]).exists()]
    import pandas as pd
    with ProcessPoolExecutor(a.workers) as ex:
        rows = list(ex.map(check, jobs, chunksize=4))
    df = pd.DataFrame(rows)
    out = ROOT / f"datasets/solcheck_{sd.name}.csv"
    df.to_csv(out, index=False)
    bad = df[~df["feasible"]]
    print(f"{len(df)} solutions checked, {len(bad)} failed -> {out.relative_to(ROOT)}")
    if len(bad):
        print(bad[["sol", "worst_bound", "worst_int", "worst_row_rel", "obj_rel_err", "unknown_vars"]].to_string())
        sys.exit(1)  # a failed check is an error, not a log line


if __name__ == "__main__":
    main()
