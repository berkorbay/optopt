"""Hand-written selection rules (spec §5 baseline 4).

Written and committed at 00:52 on 2026-09-23, BEFORE any portfolio result was seen, from general knowledge only:
- very large instances favour cuOpt's GPU primal heuristics (scale is where the GPU pays off);
- pure-binary set-partitioning/packing structure favours SCIP with aggressive heuristics;
- instances with many general integers or continuous variables favour HiGHS default (strong LP, cheap nodes);
- otherwise SCIP default.
"""


def choose(f: dict) -> str:
    if f["log_nnz"] >= 6.0:
        return "C0"
    if f["frac_bin"] >= 0.95 and f["frac_setlike_rows"] >= 0.5:
        return "S1"
    if f["frac_int"] >= 0.2 or f["frac_cont"] >= 0.5:
        return "H0"
    return "S0"
