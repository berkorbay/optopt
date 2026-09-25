# Techniques we use — lineage ("shoulders of giants")

Keys are in `paper/refs.bib`. Written 2026-09-23 after Berk asked which established techniques the project uses.

## Already in use (Track A, reused in B)
| technique | where | source |
|---|---|---|
| per-instance algorithm selection, SBS vs VBS | Track A design | [rice1976algorithm] [xu2008satzilla] [xu2011hydramip] |
| closed gap (SBS→VBS fraction) | all selection tables | ASlib [bischl2016aslib] |
| primal integral | main cost | [berthold2013primal]; ML4CO primal task [gasse2022ml4co] |
| shifted geometric mean | time-to-target | MIPLIB benchmarking [gleixner2021miplib] |
| PAR2 censoring | time-to-target | algorithm-selection practice [kerschke2019survey] |
| multiple seeds / held-out-seed oracle | noise checks, B0 gate | performance variability [lodi2013variability] |
| matrix features | 62 static features | [hutter2014runtime] |
| soft targets ∝ exp(−β·cost), proper scoring | MLP/Laya training | [gneiting2007scoring]; Laya RLCD [laya2026] |
| parallel portfolio (run both, keep best) | H1‖C0 pair | **[gomes2001portfolios]** — the idea is theirs; ours is the CPU+GPU measurement |
| benchmarks | data | [gleixner2021miplib] [gasse2022ml4co] [pglibuc] [knueven2020uc] |

## To build Track B on
- when to run primal heuristics inside B&B: [khalil2017heuristics], heuristic scheduling [chmiela2021learning]
- **online bandit control during the solve (no offline training): adaptive LNS [hendel2022alns] — the baseline Laya
  must beat in Track B**; bandit-based adaptive behaviour in SCIP [hendel2019bandits]; online learning for
  scheduling MIP heuristics [chmiela2023online] — both adapt within one instance, no offline training
- learned node selection (depth-first vs best-first is exactly this): [he2014learning] [labassi2022nodes] [mattick2024node] — all
  per-node policies, finer-grained than switching SCIP's existing strategies
- imitation of an expert via look-ahead labels: [gasse2019exact] — our action-rollout labels follow the same pattern
- separator / cut configuration: [li2023separators] [tang2020rl] [paulus2022learning] [wang2023learning]
- instance-specific configuration: BenLOC [li2025benloc], [valentin2022instance] — tree models hard to beat
- restarts: clairvoyant restarts via tree-size estimation [anderson2019restarts] (hand-set threshold);
  no well-cited *learned* restart policy found. None of these controls cut effort mid-solve.
- tooling: Ecole [prouvost2020ecole] — SCIP-as-RL-environment reference design

## Consequence for the novelty claim
Not "learning to control a solver mid-search" (covered by the works above). Defensible: **one small, general,
calibrated decision model answering several control questions (node selection, heuristics, cuts, restart) inside
one solver**, compared against per-question specialists, LightGBM and an online bandit.
