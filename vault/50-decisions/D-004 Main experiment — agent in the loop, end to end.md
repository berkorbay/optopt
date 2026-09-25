# D-004 Main experiment — agent in the loop, end to end (2026-09-23 midday, Berk)

**Berk's framing.** Hand an agent a problem and a solver, a wall-clock budget and a standardized machine slice;
it starts from default settings and is free to change settings; measure end-to-end performance. This is the
paper's main experiment. Everything before it (Track A, B0–B2, switch simulations) is a component study that sizes
the ceiling and locates the gain.

**Protocol.**
- Slice: 1 Cortex-X925 core + 8 GiB for the solver (more cores only if the agent may run parallel copies — then
  every baseline gets the same cores). Solver: SCIP first; HiGHS/cuOpt later.
- Budget T (60 / 120 / 300 s) is wall clock and includes EVERYTHING the agent does: its model calls, Laya calls,
  restarts, parameter changes.
- Agent API (to build): read solver state + log tail; set parameters; restart; (optionally) spawn parallel copies.
  Same API for every agent.
- Metrics: primal integral and primal-dual integral over wall clock, time to 1 % target, final gap; every incumbent
  checked by `analysis/check_solutions.py`.
- Instances: held-out, ideally unseen by any LLM (generated ML4CO, new PGLib-UC scenarios #13) + MIPLIB as a
  secondary set (LLMs may have memorised MIPLIB facts).

**Arms — a 2×2 plus baselines** (Berk: should Laya be a tool or an agent? → both):
| | no LLM | LLM agent |
|---|---|---|
| no Laya | default · best fixed (train) · online bandit · parallel seeds (resource-matched) | LLM alone (reads logs, sets params) |
| Laya | **Laya as the agent** (periodic controller, the original hypothesis) | **LLM + Laya as a tool** (Laya = "System 1": frequent, bounded, calibrated calls; LLM = "System 2": set-up and key moments) |

**What the components predict** (B1/B2, switch sim): most reachable gain is choosing a good static setting early
(16–21 % on P over best fixed); mid-run schedule changes ≈ +2 %; restarting unlucky runs is worth 10–18 % in
hindsight only very early and was not predicted from simple state; parallel copies +9–13 % with no prediction.

**Constraints.** Laya ≤ 1 call per few seconds (continuous inference halves a GPU solver's progress); a local LLM
(the deep-research agent (Hermes Agent with Qwen3.8-27B, UD-IQ3_XXS on llama.cpp)) contends for memory bandwidth — that cost is part of the result; hosted LLMs only on public data;
D-003 memory rules apply; Laya arms use a fine-tuned checkpoint (zero-shot is unusable, measured).
