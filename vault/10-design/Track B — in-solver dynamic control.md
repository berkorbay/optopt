# Track B — in-solver dynamic control (primary question)

**Question.** Can Laya, called at intervals *inside* one solver's run, improve time-to-good-solution by changing
the solver's search strategy and parameters on the fly, over the solver's default and the best fixed setting?

**Solver.** SCIP first — plugins let outside code act mid-solve (event handlers, node selectors, parameter
changes between nodes, restarts). HiGHS exposes far less mid-solve control (callbacks can interrupt and read
state; few parameters take effect mid-B&B) → checked in B4, not assumed.

**Decision point.** Every N s or K nodes (N ∈ {2, 5, 10} s). Track A measured that ≤ 1 Laya call per 5 s does not
disturb a GPU solver; for SCIP (CPU) the overhead is just the ~30 ms call.

**State** (compact, spec §13): gap and its change over 1 s / 5 s, primal and dual bound slopes, incumbent age and
count, nodes and node rate, open nodes, current/max depth, LP iterations per node, elapsed fraction, previous
action and its reward, plus the Track A static features.

**Actions** (hierarchical, small choice sets — spec §18):
- node selection: depth-first / best-first (bound) / best-estimate / hybrid (SCIP default)
- primal heuristic emphasis: off / default / aggressive
- separation (cut) effort: off / default / aggressive
- restart now: yes / no

**Plan.**
- **B0 headroom first (go/no-go):** oracle over a small set of *fixed schedules* (e.g. "depth-first until first
  incumbent, then best-estimate", fixed-setting switches at 25/50 % of budget), vs default and best fixed
  setting. Continue only if > 15–20 % (spec §22 dynamic threshold) with seed-noise check.
- **B1** SCIP control plugin + state recorder (event handler at decision points; actions applied via
  node-selector priorities and parameter changes; verify each action actually takes effect mid-solve).
- **B2** training data: at each decision point branch the run over actions (replay from the same prefix with a
  fixed seed) → reward = gap/primal-integral improvement per second over the next interval. Soft targets.
- **B3** policies: default, best fixed, hand rules, **online bandit (Hendel-style, learns during the solve, no
  training data)**, LightGBM, MLP, Laya zero-shot, MIP-Laya fine-tuned, oracle. If the bandit matches Laya, the
  trained model is not justified. Lineage: [[Techniques we use — lineage]].
- **B4** HiGHS feasibility: which settings can change mid-solve.
- **Budgets/data:** MIPLIB subset + ML4CO, 60–120 s, ≥ 3 seeds, 12 CPU runs in parallel (no GPU bottleneck).
