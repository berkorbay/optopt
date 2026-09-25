# D-002 Two tracks — in-solver control is the primary question (2026-09-23, morning)

**Context.** The night-1 experiment (D-001) was built around the brief's stated primary question — one policy
*across* HiGHS, SCIP and cuOpt (solver/strategy selection). Berk clarified after reading the results: the
question he cares about is whether **Laya can make a single solver better by adjusting its parameters and search
strategy on the fly** (node selection depth-first / best-first / …, heuristic and cut effort, restarts) during the
solve.

**Decision.**
- **Track A — cross-solver strategy selection** (night 1). Kept as its own research track, frozen at git tag
  `track-a-night1`. Its results stay in the paper as a section (baseline study + CPU‖GPU finding), not deleted
  or rewritten. Issues labelled `track-A`.
- **Track B — in-solver dynamic control** is the primary question from now on. Plan:
  [[Track B — in-solver dynamic control]]. Issues labelled `track-B`.

**What Track A contributes to Track B.** Harness, trajectory format and metrics; the evidence that settings
matter within one solver (H0 vs H1, S0 vs S1 swing individual instances by up to ~30 %) and that the best setting
changes with budget and difficulty; Laya's cost (23–32 ms/decision, no measurable interference at ≤ 1 call / 5 s).

**What it does not settle.** Static, t=0 selection failed; Track B gives the policy live solver state, a
different and richer input. No Track B claim may be made from Track A numbers.
