"""Static instance features (spec §13 `problem` + `coefficients`), computed from the constraint matrix.

About 70 numbers per instance, all scale-free or log-scaled so that a policy trained on one family can be applied
to another. Reading uses HiGHS (fast, handles .mps.gz). No solver effort is spent: this is what a controller can
know at t=0 before any solve.
"""
from __future__ import annotations

import math

import highspy
import numpy as np


def _stats(prefix: str, x: np.ndarray) -> dict:
    x = np.asarray(x, dtype=float)
    if x.size == 0:
        return {f"{prefix}_{k}": 0.0 for k in ("mean", "std", "min", "max", "q50", "q90")}
    return {f"{prefix}_mean": float(x.mean()), f"{prefix}_std": float(x.std()), f"{prefix}_min": float(x.min()),
            f"{prefix}_max": float(x.max()), f"{prefix}_q50": float(np.quantile(x, 0.5)),
            f"{prefix}_q90": float(np.quantile(x, 0.9))}


def _logabs(x: np.ndarray) -> np.ndarray:
    x = np.abs(np.asarray(x, dtype=float))
    x = x[(x > 0) & np.isfinite(x) & (x < 1e19)]
    return np.log10(x)


def extract(path: str) -> dict:
    h = highspy.Highs()
    h.setOptionValue("output_flag", False)
    from optopt.paths import resolve  # instance paths are repository-relative
    h.readModel(str(resolve(path)))
    lp = h.getLp()
    n, m = lp.num_col_, lp.num_row_
    a = lp.a_matrix_
    start = np.asarray(a.start_)
    index = np.asarray(a.index_)
    value = np.asarray(a.value_)
    nnz = int(start[-1]) if len(start) else 0
    integrality = np.asarray([int(v) for v in lp.integrality_]) if len(lp.integrality_) else np.zeros(n, int)
    lb, ub = np.asarray(lp.col_lower_), np.asarray(lp.col_upper_)
    rl, ru = np.asarray(lp.row_lower_), np.asarray(lp.row_upper_)
    c = np.asarray(lp.col_cost_)
    is_int = integrality > 0
    is_bin = is_int & (lb == 0) & (ub == 1)
    col_deg = np.diff(start) if n else np.zeros(0)
    row_deg = np.bincount(index, minlength=m) if m else np.zeros(0)

    eq = np.isclose(rl, ru) & np.isfinite(rl)
    le = ~np.isfinite(rl) & np.isfinite(ru)
    ge = np.isfinite(rl) & ~np.isfinite(ru)
    rng = np.isfinite(rl) & np.isfinite(ru) & ~eq
    # rows whose variables are all binary and all coefficients equal 1: set partitioning/packing/covering
    colof = np.repeat(np.arange(n), col_deg) if n else np.zeros(0, int)
    row_allbin = np.ones(m, bool)
    row_allone = np.ones(m, bool)
    if nnz:
        np.logical_and.at(row_allbin, index, is_bin[colof])
        np.logical_and.at(row_allone, index, np.isclose(value, 1.0))
    setlike = row_allbin & row_allone & (row_deg > 0)
    knap = row_allbin & ~row_allone & le
    rhs = np.where(np.isfinite(ru), ru, rl)
    rhs = rhs[np.isfinite(rhs)]

    f = {
        "log_rows": math.log10(m + 1), "log_cols": math.log10(n + 1), "log_nnz": math.log10(nnz + 1),
        "density": nnz / max(1, n * m),
        "frac_bin": float(is_bin.mean()) if n else 0.0,
        "frac_int": float((is_int & ~is_bin).mean()) if n else 0.0,
        "frac_cont": float((~is_int).mean()) if n else 0.0,
        "frac_eq": float(eq.mean()) if m else 0.0, "frac_le": float(le.mean()) if m else 0.0,
        "frac_ge": float(ge.mean()) if m else 0.0, "frac_range": float(rng.mean()) if m else 0.0,
        "frac_setlike_rows": float(setlike.mean()) if m else 0.0,
        "frac_knapsack_rows": float(knap.mean()) if m else 0.0,
        "frac_free_cols": float((~np.isfinite(lb) & ~np.isfinite(ub)).mean()) if n else 0.0,
        "frac_unbounded_ub": float((~np.isfinite(ub)).mean()) if n else 0.0,
        "frac_obj_nonzero": float((c != 0).mean()) if n else 0.0,
        "frac_obj_on_int": float(((c != 0) & is_int).sum() / max(1, (c != 0).sum())),
        "frac_neg_coef": float((value < 0).mean()) if nnz else 0.0,
        "frac_unit_coef": float(np.isclose(np.abs(value), 1).mean()) if nnz else 0.0,
        "frac_int_coef": float(np.isclose(value, np.round(value)).mean()) if nnz else 0.0,
        "rows_per_col": m / max(1, n),
        "maximize": float(lp.sense_ == highspy.ObjSense.kMaximize),
        "int_range_log": float(np.log10(1 + np.nanmax(np.where(is_int & np.isfinite(ub) & np.isfinite(lb), ub - lb, 0))))
        if n else 0.0,
    }
    f.update(_stats("coldeg", np.log10(col_deg + 1)))
    f.update(_stats("rowdeg", np.log10(row_deg + 1)))
    for name, arr in (("obj", c), ("coef", value), ("rhs", rhs)):
        la = _logabs(arr)
        f.update(_stats(f"log{name}", la))
        f[f"{name}_dynrange"] = float(la.max() - la.min()) if la.size else 0.0
    # row-wise coefficient spread (numerics) on a sample of rows
    if nnz and m:
        order = np.argsort(index, kind="stable")
        rv = np.abs(value[order])
        ri = index[order]
        bounds = np.searchsorted(ri, np.arange(m + 1))
        sample = np.linspace(0, m - 1, min(m, 2000)).astype(int)
        spread = [np.log10(rv[bounds[i]:bounds[i + 1]].max() / max(rv[bounds[i]:bounds[i + 1]].min(), 1e-12))
                  for i in sample if bounds[i + 1] > bounds[i]]
        f.update(_stats("rowspread", np.asarray(spread)))
    else:
        f.update(_stats("rowspread", np.zeros(0)))
    return f
