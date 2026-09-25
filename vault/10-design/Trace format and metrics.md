# Trace format and metrics

**Trace** (`solvers/common.py`): per run, a list of events `{t, primal, dual, nodes, lp_iters, kind}` with
`kind ∈ {incumbent, sample, final}`, t = seconds since the solve call (model reading excluded and recorded
separately as `read_time`). Every incumbent is kept; plain samples are throttled to one per 0.5 s.
- HiGHS: `cbMipImprovingSolution` (incumbents), `cbMipInterrupt` + `cbMipLogging` (samples).
- SCIP: event handler on `BESTSOLFOUND` (incumbents) and `NODESOLVED` (samples, throttled).
- cuOpt: `GetSolutionCallback` gives incumbent cost **and** current bound; no periodic samples exist, so between
  incumbents the bound is only known at the next incumbent or the end.

**Metrics** (`analysis/metrics.py`, tests in `tests/test_metrics.py`):
- primal gap γ(t) (Berthold 2013), primal integral P(T)/T ∈ [0,1], primal-dual integral;
- time to first incumbent, time to target (γ ≤ 1 % and ≤ 5 %), gap at 5/10/15/30/60 s;
- all cut at the budget T, so cuOpt's 2–3 s overrun earns nothing.

**Reward** for selection: cost = P(T)/T. Soft targets: P(a) ∝ exp(−β·cost), β = 20 (a 0.05 difference in
normalised integral ≈ factor e).

**Not measured tonight** (spec §7): memory bandwidth (no counter exposed on GB10 via nvidia-smi), GPU memory
per process (nvidia-smi reports N/A for memory.used on this unified-memory part).
