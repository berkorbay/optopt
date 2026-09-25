# Future research — extensions of this study (2026-09-24, at wrap-up)

Each item starts from a result or a limitation of this study. Grouped by kind; within a group, roughly in order of
expected value per unit of effort.

## A. Sharpen what this study found
1. **A fresh confirmation cohort with real heterogeneity.** Pick families where, on *training* data, no single setting
   dominates (the LLM agents and Laya only matched the obvious family rule on ML4CO). Freeze the protocol and the arms
   (best fixed from training, family rule, LightGBM, bandit, Laya, LLM agent, timing-matched controls) before touching the
   test instances; one primary contrast, the rest exploratory.
2. **The value of a short diagnostic probe.** Spend a charged observation window (a few seconds of the default run, or
   root LP statistics), then choose once; compare with the same total budget run statically. Measure the gain against the
   probe's cost and add an abstention rule that keeps the training-selected setting when the predicted gain is small.
3. **Richer state for learned selectors.** Laya saw only a text rendering of 62 static features. Root LP statistics,
   early incumbents and bound movement are where a text encoder could differ from gradient-boosted trees — and where the
   run-level part of the headroom (the part static features cannot predict) might become predictable.
4. **Longer budgets.** Budgets here stop at 300 s. Test a small pre-declared set of schedules at 600 s to hours, on both
   the primal and the primal-dual integral, on a fixed confirmation sample; the corrected 300 s result (switching adds
   ≤ 1.5 % to the bound) is the prior to beat.
5. **Deployment-level timing.** Charge feature extraction, model loading and inference to the budget (a cold-start
   benchmark from the input file), next to the warm setting used here; matters most at 10 s budgets.

## B. Agents
6. **Language-model agents with a latency budget.** More seeds and families; hosted models at higher reasoning effort
   with an explicit thinking-time budget; calling policies that decide *when* to ask (key moments: first incumbent,
   stall) instead of fixed intervals; the timing-matched controls as the baseline every agent result reports.
7. **LLM + learned model as System 2 / System 1.** The tool design tried here (Laya's probabilities in the prompt) did
   not help; alternatives are the LLM choosing *which* diagnostic to run, or Laya screening moves the LLM only confirms.
8. **Agent benchmark.** Package the harness as a benchmark: fixed instance cohorts, the slice, the charged clock, the
   noise-floor controls, and a results table others can add to.

## C. Portfolios and cooperation
9. **Portfolio composition under a compute budget.** Which pair (or triple) of solvers and settings to race, given cores,
   a GPU and memory; learned selection of the *pair* rather than one configuration; resource accounting (CPU threads
   including cuOpt's host threads, GPU occupancy, peak memory, energy where measured reliably).
10. **Cooperation beyond one direction.** cuOpt → SCIP through SCIP's heuristic interface paid (+14 % on SCIP's own
    trajectory); the reverse costs cuOpt its presolve. Next: HiGHS as the CPU partner (its user-solution callback),
    longer budgets, and exchanging bounds or reduced problems, not only incumbents.
11. **The GPU inside MILP** — see [[Future research — GPU inside MILP]]: PDLP-type GPU LP solvers for relaxations inside
    a CPU branch-and-bound; continuous GPU heuristic populations; scheduling several GPU consumers.

## D. Scope
12. **More solvers and a larger portfolio.** Tuned configurations (e.g. SMAC) and a ~20-configuration portfolio instead
    of six hand-picked ones; commercial solvers as reference points where licences allow.
13. **Energy and market problems.** Unit commitment was one family here; public energy-market problems (scheduling,
    dispatch, bidding MIPs) are a natural domain where time-to-good-solution under a fixed budget is the operational
    requirement. Public data only.
14. **Hardware transfer.** Repeat the headline measurements on other machines (x86 with a discrete GPU, a larger
    DGX) to separate conclusions from GB10 specifics.

## E. Method and verification
15. **Pre-registration and a generated claim registry.** Each claim tied to a metric version, cohort, reference
    manifest, command and result file, generated rather than hand-kept.
16. **Certificates.** VIPR certificates for optimality claims and a formally verified solution checker (issue #27).
17. **Upstream contributions** from the findings (the HiGHS time-limit issue is filed as ERGO-Code/HiGHS#3314; others
    await the author's decision).
