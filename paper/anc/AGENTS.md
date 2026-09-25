# AGENTS.md — companion for AI agents (and humans)

Companion to the paper **"Optimizing the Optimizers: Measuring Learned Control of MIP Solvers on a Single DGX
Spark"** by Berk Orbay (berk.orbay@tideseed.com). Repository: https://github.com/berkorbay/optopt . The same file is
shipped with the arXiv submission as an ancillary file. Paths are relative to the repository root; the code is the Python package `optopt` under `src/`.

## Setting
- Machine: NVIDIA DGX Spark — GB10 (10 × Cortex-X925 @ 3.9 GHz, 10 × Cortex-A725 @ 2.8 GHz), Blackwell GPU, 121 GiB unified memory.
- Solvers: HiGHS 1.15.1, SCIP 10.0 (PySCIPOpt 6.2.1), NVIDIA cuOpt 26.08. Decision model: Laya (`convaiinnovations/laya`, 421.3 M parameters).
- Instances: 80 MIPLIB 2017 benchmark instances, ML4CO item placement and load balancing (official train/test), 56 PGLib-UC cases.
- Metric: normalised primal integral **P(T)** ∈ [0, 1] (Berthold 2013) — mean over the wall-clock budget of the relative gap
  to the best known value, 1 before the first incumbent; lower is better. Secondary: primal-dual integral **PDI(T)**. Code: `src/optopt/analysis/metrics.py`.
- Protocol: oracles scored on a held-out seed; selectors by grouped cross-validation and leave-one-family-out; timed runs
  pinned one per Cortex-X925 core with a hard memory cap (SCIP experiments from B1 on; Track A and B0 were not pinned); the final
  incumbent of every SCIP run is stored and checked independently (`datasets/solcheck_coverage.csv` lists coverage). Paired tests are
  over instances (seeds averaged within an instance) and exploratory unless stated. PDI is integrated on exact event times since
  2026-09-24 (an earlier rounding error is described in the paper's appendix "Corrections after an external review").

## Claims, numbers, evidence
**C1 — Choosing the configuration matters.** Per-instance oracle over six HiGHS/SCIP/cuOpt strategies vs the best fixed
strategy (single-seed oracle): 19 % pooled over all 336 attempted instances, 25 % on the 313 where some strategy finds a solution (30 s);
41 % MIPLIB (60 s), 16 % / 15 % ML4CO item placement / load balancing, PGLib-UC 5 % all 56 / 11 % on 33 (23 FERC cases: no strategy
finds a solution in 60 s, P = 1 for all). `tab:headroom`, `tab:flow`. Selectors are evaluated on the 313 (conditional cohort). On a
12-instance MIPLIB subset with five seeds and the four CPU strategies, a held-out oracle realises 26.3 % of an apparent 31.8 % (83 %); cuOpt was not re-run with extra seeds. Evidence: paper Tables `tab:headroom`, `tab:portfolio-results`, `tab:variance`; `datasets/portfolio_table.csv`;
scripts `src/optopt/analysis/build_runs.py`, `src/optopt/analysis/reports.py`. Caveats: one seed for the main grid; these runs were not pinned to one core type.

**C2 — The right choice is hard to predict before the solve.** Closed gap (0 = best fixed strategy, 1 = oracle), pooled:
10 s — Laya fine-tuned +0.31 (only interval excluding zero: [0.14, 0.48]), LightGBM +0.24, MLP +0.07, Laya zero-shot −0.37;
30 s — Laya fine-tuned +0.10, LightGBM +0.03, MLP 0.00 (all intervals include zero). Unseen family: Laya fine-tuned +0.09 (10 s) /
−0.02 (30 s), LightGBM −0.03 / −0.40. Evidence: `tab:selection`,
`datasets/selection_results.csv`, `src/optopt/experiments/selection.py`, `src/optopt/experiments/laya_select.py`. Paired Laya vs
LightGBM (`datasets/selection_paired.json`): pooled no superiority (10 s +0.07 [−0.13, 0.34], p 0.67; 30 s p 0.09); unseen family
at 30 s Laya +0.37 [0.16, 0.68], p 3e-5. Intervals hold fitted models fixed (no retraining/fold variation); conditional cohort. Caveats: one fine-tuning seed per fold; retrained on corrected labels 2026-09-23 night (was +0.21 / −0.05).

**C3 — Choosing, not switching.** Inside SCIP (45 MIPLIB instances, 12 arms, 2 seeds, 120 s): static choice per instance +11.8 % (P),
+6.5 % (PDI); switching settings during the solve adds +2.1 % [−0.4, +7.3] (P) and +1.6 % [−0.1, +3.8] (PDI). Evidence: `tab:b2`
(and appendix `tab:b0`, `tab:b1`); `datasets/b2_decomposition.json`; `src/optopt/experiments/b2_gate.py`. **At 300 s (B3, 20 top-headroom instances):** static +20.4 %
[1.6, 35.9], switching −0.2 % [−1.8, 1.0] on P; on PDI static +11.3 %, switching +1.5 % [−0.2, 4.3] (an earlier +6.8 % was a
PDI integration error and is withdrawn) — `datasets/b3_results.json`, `src/optopt/analysis/b3.py`. Decomposition code:
`src/optopt/analysis/decomp.py` (shared by the B2 gate, B2 and B3). Caveat: hand-picked actions; scope is
whole-setting switches in SCIP scored by time to good solutions. DASH (Di Liberto et al. 2016) switches only the branching
rule at nodes, measures time to optimality and finds the opposite; Balans finds value in switching LNS operators.

**C4 — Run-level variation; parallel copies.** Per-seed winner = seed-averaged winner in 71 % (P) / 69 % (PDI) of runs. SCIP copies of
the best setting: 2 / 3 / 5 copies → +7 / +9 / +11 % (P), +5.5 / +7.5 / +9.4 % (PDI). HiGHS (1 thread) ‖ cuOpt (GPU): 22 % pooled, 80 % of the
oracle headroom. Evidence: `tab:parallel`, `tab:pairs`; `datasets/b2_seeds_analysis.json`, `datasets/pairs.csv`; `src/optopt/analysis/pairs.py`.
Live HiGHS‖cuOpt (80 MIPLIB, 60 s, one session): +30.4 % over HiGHS alone (61/13; `datasets/xhighs_results.json`) — the headline pair.
Live SCIP‖cuOpt (MIPLIB, 60 s, launched together, both arms in one session): +21.5 % over SCIP alone (the first 44 instances in
job-file order, 28/13, p 4e-5; the run stopped at the end of its window; `datasets/xsame_results.json`). The earlier +26.4 % (71/2) compared against SCIP alone from another session, which ran
3.9 % slower on the same instances — session drift, not the pair.
Passing cuOpt's solutions into SCIP through a SCIP heuristic plugin (`_XchgHeur`): SCIP's own trajectory +14.1 %
(p 2e-4, 47/24), pair value unchanged (+1.1 %, n.s.), no failures; two-way exchange −14.7 % (cuOpt's presolve is
disabled once it accepts solutions). Injecting from an event handler instead crashed SCIP on 9/80 instances per arm. `datasets/xchg_results.json`, `src/optopt/analysis/xchg.py`, `src/optopt/experiments/xchg_pair.py`.
Caveat: more compute than one run. Racing copies is established (ReXi, ParBalans, Carvajal et al. 2014); this is a
measurement, not a method.

**C5 — Agent in the loop.** Agents start from SCIP's defaults, one core + 9 GiB (8 GiB for the LLM-agent and control runs),
120 s wall clock including every decision; agents are called at solver events (first eligible event after the start, then the first
event after each interval); instance features are computed before the clock (median 0.3 s, max 5.2 s, not charged).
Online bandit vs default: +8.6 % (P, p = 0.016 over instances) on 35 held-out instances; +20.8 % (10 s interval) and +27.1 % (5 s) on 30 fresh ML4CO
test instances. Item placement P(120): default 0.356, bandit 0.250, fixed "aggressive heuristics" 0.245 (the bandit finds the right
static setting online; it is 12.5 % worse than that fixed setting at 60 s). Rules agent: −2.7 % (n.s.). Diagnosis at t = 0 (LightGBM, trained on 60 ML4CO training instances): per-instance prediction +23.4 %
vs best fixed setting from training +28.5 % and diagnose-then-bandit +29.1 % (`src/optopt/analysis/diag.py`, `datasets/diag_results.json`); Laya fine-tuned for the same t = 0 choice +28.3 % (learns the family
rule; = best fixed, > LightGBM; `src/optopt/analysis/laya_diag.py`, `datasets/laya_diag.json`). **LLM agents (2026-09-24, same 30
test instances, 2 seeds, 120 s):** Ornith-1.5-35B-A3B (local, NVFP4/vLLM, thinking off, every 20 s) P 0.115 = Laya agent
0.116 ≈ best fixed 0.126 (+8.5 % vs fixed, [−7.1, 21.0], p 0.09 over instances — not significant). **Timing-matched controls (one session, same 60 runs,
`tab:timing`, `datasets/timing_ctrl.json`, `src/optopt/analysis/timing_ctrl.py`):** the fixed setting applied at the first
callback beats the same setting configured before presolve by 10.9 % (24/30 instances, Wilcoxon p 0.005; median per-instance gain +12.7 %; bootstrap 95 % interval of the mean −3.9…+22.3 %, a few instances lose heavily).
Per family: load balancing 15/15 better (p 6e-5, P 0.037→0.032; before presolve equals the defaults), item placement 9/6 (p 0.25). First call: median 0.35 s,
max 1.1 s, during the root node, after presolve (~0.25 s). Mechanism (`tab:timingmech`, `datasets/timing_mech.json`, one seed,
90 runs): on load balancing SCIP stays at the root (1 node) and spends ~96 s in heuristics (RENS) in every arm; set before
presolve, HEU also runs the zero-objective heuristic (0.59 s), delaying the first solution 0.73 → 1.25 s ≈ the whole P gap
(0.035 vs 0.031); first call 15/15 again, 10 s arm 14/15; item placement n.s. (11/4, p 0.36). Specific, not general; against that control the LLM
agent is −10.6 % [−18.9, −4.0] (median −3.4 %; worse on 22/30, p 0.004; item placement 12/15 worse, p 0.03); its later decisions add +3.6 % (n.s.) over its first move; the earlier 8.5 % margin does
not replicate (+1.5 %, n.s.). The LLM's apparent edge was timing, not judgement; + Laya as a tool 0.121; OpenAI GPT-6 Luna (ChatGPT Plus, reasoning low, every 30 s)
0.137 with 10 % of the budget spent waiting (one seed; seed-0-only comparisons in `datasets/llm_agents.json`). PDI all within 3 %. `tab:llm`, `datasets/llm_agents.json`,
`src/optopt/analysis/agents_llm.py`, `src/optopt/agents/llm.py`, `src/optopt/agents/laya_service.py`, `src/optopt/agents/gpt_bridge.py`. Evidence: `tab:agent`, `tab:pilot`;
`datasets/pilot_e.json`, `datasets/pilot_e2_static.json`; `src/optopt/analysis/pilot_e.py`, `src/optopt/agents/`. Caveat: no gain on MIPLIB or PDI; LLM agents tested on two ML4CO families only.

**C6 — Cost of the decision model.** Laya: 23–32 ms per decision. cuOpt P(30): alone 0.226, Laya loaded but idle 0.240, one call per 5 s
0.235, continuous inference 0.452. Evidence: `tab:contention`; `datasets/contention.jsonl`; `src/optopt/experiments/contention.py`.

## Prior art and novelty
Structured search of about 180 works (`vault/40-literature/prior-art/`, sweeps A–E, synthesis in `Prior art.md`).
Learned per-instance configuration of one solver, mid-solve switching of one component, online bandits in SCIP, LLM
configuration (Lawless 2025, GRIMIP 2026), racing, and learned selection AMONG MIP solvers (ASlib MIP-2016: CBC,
CPLEX, Gurobi, SCIP, Xpress; OASC 2017; ZeroFolio 2026) all exist. Not found: a GPU MIP solver in a selection
portfolio, selection scored by the primal integral, a pretrained encoder fine-tuned to choose MIP settings, and the
static-vs-switching split for MIP (done for black-box optimisation by Vermetten et al. 2020). Negative search results
— **do not claim "first"**. Re-check: `vault/40-literature/prior-art/E novelty re-check 2026-09-23.md`. Paywalled works without a legal copy live only in
`vault/40-literature/Paywalled research.md` and are
cited only in the paper appendix subsection `app:paywalled`, with a disclaimer.

## Measurement note
SCIP incumbent values recorded before 2026-09-23 19:30 lagged by one solution (SCIP's primal bound is not yet updated
at the BESTSOLFOUND event). All affected traces were corrected exactly by `src/optopt/analysis/fix_scip_traces.py` (original values
kept as `primal_recorded`); the recorder is fixed. Every number above uses corrected traces.

## Map
| path | what |
|---|---|
| `src/optopt/solvers/` | HiGHS / SCIP / cuOpt wrappers with incumbent callbacks; SCIP also takes schedules and agents |
| `src/optopt/agents/` | agent interface (`base.py`), online bandit, rules agent — called inside SCIP's wall-clock budget |
| `src/optopt/portfolio/strategies.py` | every strategy, setting, schedule and agent arm used in the paper |
| `src/optopt/experiments/` | runners (`run_one`, pinned and memory-capped `pool`, `xchg_pair`), job builders, selection |
| `jobs/` | job files (instance paths relative to the workspace) |
| `src/optopt/analysis/` | metrics, table builders, solution checker `check_solutions.py` |
| `datasets/` | derived tables behind every number |
| `traces/raw/<set>/` | one JSON trajectory per run and `traces/sol/` incumbents — written by runs, not committed; `traces/resources/` resource records (committed) |
| `paper/` | LaTeX source; `paper/generated/` is written by the analysis modules (the paper is what `main.tex` inputs; a few extra tables there, e.g. `table_selection_*_60.tex`, are regenerated but not used) |
| `vault/` | research journal, design notes, decision records, failures |

AgentRA (Agent Research Assistant) — the AI agent that designed with the author and executed these experiments — is mainly Claude Opus 5.5.
The study was reviewed, with suggestions for improvement, by Claude Fable 5.1 (Anthropic) and OpenAI GPT-6 Astra (ChatGPT); see `vault/80-reviews/`.

## Reproduce
```bash
uv venv && source .venv/bin/activate && uv pip install -e ".[dev,plots]"
optopt reproduce      # re-derives every table in datasets/ and paper/generated/ from traces/ (re-run the jobs first), lists any change
pytest -q
```
Re-running solvers needs the public instances in `data/` (see `vault/10-design/Datasets.md`) and, for cuOpt, a CUDA 13
GPU (`uv pip install -e ".[gpu]"`): `optopt pool jobs/<job>.jsonl --pin <cores> --mem-cap-gb 9`.

## Rules for new experiments
- Pin one timed run per fast core; never run analysis with default thread counts beside timed runs.
- Give every solver run a hard memory cap (runner `--mem-cap-gb`).
- Score oracles on a held-out seed and separate *static choice* from *switching* before claiming a dynamic gain.
- Check every reported incumbent with `src/optopt/analysis/check_solutions.py`.

## Tried without effect
Evolutionary partner beside SCIP (crossover + repair + LP decoding; with or without ≤ 20 % super-optimal infeasible
individuals ranked by infeasibility): no gain at 60 s on MIPLIB, loses to an equal-compute second SCIP
(`src/optopt/solvers/ea.py`, `datasets/xchg_results.json`). Schedules at 30/120/300 s for P; rule agent; learned restarts.

## Open (and future research)
Full agenda with reasons: `vault/10-design/Future research.md`. In short: a fresh confirmation cohort where no single
setting dominates (pre-registered, timing-matched controls as baselines); a charged diagnostic probe before one choice;
richer state for learned selectors; longer budgets for switching (the corrected 300 s bound result is ≤ 1.5 %); LLM
agents with a thinking-time budget deciding when to act; portfolio composition under a compute budget and two-way
cooperation incl. HiGHS; the GPU inside MILP (PDLP-type LP relaxations in CPU branch-and-bound, GPU heuristic
populations); more solvers and a larger tuned portfolio; energy/market MIPs (public data); hardware transfer;
certificates (VIPR, verified checker).
