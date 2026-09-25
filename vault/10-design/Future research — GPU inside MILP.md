# Future research — the GPU inside MILP (Berk, 2026-09-24: "not in this research, but note it")

In this study the GPU is used as a separate solver (NVIDIA cuOpt) that races a CPU solver or feeds it solutions
(SCIP‖cuOpt +26 % over SCIP alone; cuOpt's solutions into SCIP through the heuristic plugin +14 % on SCIP's own
trajectory). Directions that go further:

1. **GPU LP inside CPU branch-and-bound.** PDLP-type first-order LP solvers (cuOpt's, cuPDLP) for relaxations —
   e.g. the root LP of large instances — with crossover or a warm start for the dual simplex that branch-and-bound needs.
   Accuracy of first-order solutions is the known limit for proofs.
2. **Continuous GPU heuristics feeding a CPU solver.** A GPU population (feasibility jump, local search, recombination)
   exchanging solutions with SCIP or HiGHS through their supported interfaces, at longer budgets and with HiGHS as the
   CPU partner; cuOpt's own presolve is lost when it accepts outside solutions, so the direction GPU → CPU is the one
   that paid here.
3. **GPU sharing.** Two GPU jobs at once slowed each other (continuous Laya inference doubled cuOpt's primal integral);
   any design with several GPU consumers needs scheduling, not just capacity.

These are solver-engineering projects rather than configuration experiments. Related notes: [[Track B — in-solver dynamic control]],
[[Prior art]] (cuOpt, CHAP, ReXi).
