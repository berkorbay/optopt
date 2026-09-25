# Research question and spec (condensed from Berk's brief, 2026-09-23)

> **Correction (2026-09-23 morning, Berk):** the primary question is **in-solver dynamic control** — can Laya
> improve a *single* solver by adjusting its parameters and search strategy (depth-first, best-first, …) on the
> fly. The cross-solver selection below was run on night 1 and is kept as Track A. See
> [[D-002 Two tracks — in-solver control is the primary question]].

**Primary question.** Can a small non-autoregressive decision model trained on optimisation traces learn a
reusable control policy across HiGHS, SCIP and cuOpt that improves time-to-good-solution over fixed solver
strategies? Correctness stays with the solvers.

**Novelty claim to test** (spec §20): not "ML helps MIP" (established) but *one small general bounded-decision
model across several solvers and tasks* instead of a specialised architecture per task.

**Baselines** (spec §5): random, best fixed solver, best fixed configuration, hand rules, LightGBM/XGBoost,
small MLP, Laya zero-shot, fine-tuned MIP-Laya, oracle. Decisive comparison: MIP-Laya vs LightGBM/MLP vs
oracle — **if LightGBM is as good, use LightGBM.**

**First milestone** (spec §26): 6 strategies (H0/H1/S0/S1/C0/C1) on ML4CO + MIPLIB + PGLib-UC; best fixed vs
per-instance oracle at 10/30/60/300 s; then LightGBM, MLP, Laya. Proceed to dynamic control only if the oracle
shows headroom and learned policies capture a meaningful part of it.

**Go/no-go** (spec §22): solver selection oracle >10 % over best fixed; configuration >10–15 %; dynamic
>15–20 % over best static; learned LNS ≥1.25× median time-to-target. Policy overhead <1 % (prefer <0.5 %).

**Roadmap** (spec §27): P0 baselines → P1 oracle selection → P2 static learned selection → P3 solver+config →
P4 MIP-Laya fine-tune → P5 dynamic allocation → P6 learned LNS → P7 neighbourhood×solver → P8 deep SCIP →
P9 energy-specific MIP-Laya.
