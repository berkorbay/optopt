# Strategy portfolio

Code: `portfolio/strategies.py`. Milestone set (spec §26): one default and one primal-focused variant per solver.

| id | solver | non-default settings | intent |
|---|---|---|---|
| H0 | HiGHS 1.15.1 | — | CPU default |
| H1 | HiGHS 1.15.1 | `mip_heuristic_effort` 0.3 (default 0.05) | more primal heuristics |
| S0 | SCIP 10.0 | — | CPU default |
| S1 | SCIP 10.0 | `setHeuristics(AGGRESSIVE)` | more primal heuristics |
| C0 | cuOpt 26.08 | — (GPU + 3 CPU threads) | GPU default |
| C1 | cuOpt 26.08 | `mip_cut_passes` 0 (default 10), `mip_hyper_heuristic_rins_time_limit` 10 (3) | primal-focused |

Chosen a priori, not tuned — the milestone asks whether *choosing* among intentionally different strategies
pays, not how good each can be made. HiGHS/SCIP single-threaded; cuOpt uses the GPU. Next step (#6): the
~20-strategy portfolio from spec §10.
