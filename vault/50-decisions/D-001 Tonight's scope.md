# D-001 Tonight's scope (2026-09-23 00:20)

**Decision.** Tonight answers only the §26 first-milestone question, with a reduced run grid:
one 60 s run per (instance, strategy) on MIPLIB, 30 s on ML4CO and PGLib-UC, seed 0; a 12-instance × 4-seed
variance subset on MIPLIB. 10/30/60 s views are cut from the same trajectories; the 300 s screening is dropped.

**Why.** cuOpt is the bottleneck: it runs on the one GPU, ~2 lanes, and overruns each budget by 2–3 s.
6.5 h × 2 lanes ≈ 45k GPU-seconds covers ~80 MIPLIB × 2 × 65 s + ~250 ML4CO/UC × 2 × 35 s. CPU lanes
(12 single-thread workers) are not the constraint.

**Consequences.** ML4CO is 100 train + 25 valid per family instead of 1000 + 100. Two cuOpt lanes run
concurrently, so cuOpt timings include lane-to-lane contention; the contention experiment quantifies it.
Dynamic control, LNS, SCIP internals, UC scenario generation, the full MIPLIB set, 10-seed runs → follow-up
issues.

**Threads.** HiGHS and SCIP run single-threaded; cuOpt gets the GPU plus 3 CPU threads. This is not a
"fair" comparison of solvers and is not meant to be: the question is which *available* strategy to choose on
this box under a fixed wall-clock budget.
