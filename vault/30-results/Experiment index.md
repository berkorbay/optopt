# Experiment index (every experiment, including failures)

> **Correction 2026-09-24:** PDI (primal-dual integral) values in this note were computed with an integration error (times rounded before lookup) and are superseded; the primal integral P is unaffected. Corrected numbers: paper and AGENTS.md; details in [[2026-09-24 repository review — response and plan]].


Numbers are after the 19:10 SCIP recording correction. Outcome key: **+** positive result · **−** negative / no effect · **~** inconclusive · **✗** aborted or broken run.
Times are CEST on 2026-09-23. Journals: [[2026-09-23]] (night, Track A) and [[2026-09-23-trackB]] (day).

| id | when | question | design | outcome | key numbers | note |
|---|---|---|---|---|---|---|
| A1 | 00:50–05:01 | Is there headroom across HiGHS/SCIP/cuOpt? | 6 strategies × 313 inst., 30/60 s | **+** | oracle headroom 23 % pooled, 40 % MIPLIB | [[Milestone 1 — static strategy selection]] |
| A1v | 02:15–03:39 | Is the headroom noise? | 12 MIPLIB × HiGHS/SCIP × 5 seeds | **+** | ~85 % survives held-out seeds | same |
| A1s | 02:29–03:36 | Difficulty bands (spec) | H0/S0 at 300 s, 80 MIPLIB | **+** | cuOpt best on 37 instances unsolved in 300 s | same |
| A2 | 05:01–05:28 | Can selectors predict the best strategy? | LightGBM / MLP / rules / Laya zero-shot + fine-tuned, pooled + LOFO | **−** | best closed gap +0.19 (Laya ft, 10 s), CIs include 0 | same |
| A3 | 03:45 | CPU‖GPU pair (offline) | H1‖C0 from traces | **+** | 86 % of headroom, no model | same |
| A4 | 05:28–06:01 | Does Laya disturb cuOpt on the GPU? | 4 conditions × 5 inst. × 2 reps | **+/−** | periodic OK; continuous doubles cuOpt's P | [[A4 GPU contention]] |
| B0 | 07:52–08:36 | Do mid-solve schedules help SCIP at 30 s? | 12 arms × 45 MIPLIB × 2 seeds | **−** | +3.2 % (P) over best static, ~0 from schedules (corrected) | [[B0 schedules at 30 s]] |
| B1 | 08:47–09:05 | Same at 120 s, pinned | 4 arms × 30 inst. | **−** | cuts-off advantage decays 20→5 % (corrected); switching 0 | [[B1 cuts at 120 s]] |
| B2 | 10:24–13:31 | Wider actions (restart, branching, heuristics) | 12 arms × 45 × 2 seeds, 120 s | **−** switching | switching +2.1 % [−0.4, 7.3] (corrected) | [[B2 wide actions]] |
| B2s | 13:31–14:22 | Run-level vs instance-level | 6 static × top-20 × 5 seeds | **+** (insight) | winner stable 62–71 %; parallel copies +7–11 % P (corrected) | [[B2 wide actions]] |
| S1 | 12:10 | Restart unpromising runs (offline) | switch simulation at τ = 10/20/30 s | **−** | oracle +11 % at 10 s; learned ≈ −5 % (corrected, 45 inst.) | [[S1 restart simulation]] |
| E1 | 14:23–15:03 | Agent in the loop, pilot | default / bandit / rules, 35 held-out inst. × 2 seeds | **+** vs default | bandit +8.6 % (p = 0.007); rules −2.7 % (corrected) | [[E1–E2 agent in the loop]] |
| E2 | 15:08–15:42 | Confirmation on fresh ML4CO | default / bandit 10 s / bandit 5 s | **+** vs default | +21 % / +27 % (corrected) | same |
| E2c | 15:44–16:09 | Is the bandit better than the best static? | fixed HEU / NOC on the same runs | **−** for the bandit | fixed HEU ≥ bandit | same |
| E3 | 17:57–19:58 | Diagnosis first move (instance → setting) | train 6 settings × 60 ML4CO train; test on E2 set | **−** for per-instance prediction; diagnose-then-bandit **+** vs default | best fixed +28.5 %, LightGBM +23.4 %, diagnose-then-bandit +29.1 % | [[E3 diagnosis first move]] |
| ✗ | 19:10 | SCIP recorder lag (one solution late) | found by tutorial example | corrected exactly, all re-scored | conclusions unchanged | [[Mistakes and incidents]] |
| R1 | 08:40 | Can racing cut the cost of evaluation? | replay on B0 | **+** (method) | same verdict with 65 % of runs | [[B0 schedules at 30 s]] |
| U1 | 18:30– | Upstream bug candidates | HiGHS / cuOpt reproductions | HiGHS **reproduced**; cuOpt items not | HiGHS 405.8 s for a 60 s limit | [[U1 upstream reproductions]] |
| L1 | 22:57 | Laya as diagnosis agent (t = 0 SCIP setting) | fine-tuned on 60 ML4CO train, E2 test set, offline | **=** best fixed | +28.3 % vs default; LightGBM +23.4 %, best fixed +28.5 % | [[2026-09-24-night]] |
| L2 | 23:01–23:32 | Laya selection on corrected labels | 02_laya retrain, both budgets | **+** | pooled 10 s 0.31 [0.14, 0.48] (was 0.21) | same |
| B3 | 23:45–01:50 | Switching at 300 s | B2 arms + bandit, 20 inst × 2 seeds | **−** for P; **~** for PDI | P switching −0.2 %; PDI +6.8 % [−1.1, 18.8] | same |
| X1 | 23:32–04:10 | Live SCIP‖cuOpt; incumbent exchange | race / g2c / both, 80 MIPLIB, 60 s | race **+**, exchange **−** | race +25 % vs SCIP; two-way −15 %; SCIP crashed 9/80 per exchange arm | same |
| X2 | 01:50–03:24 | SCIP + evolutionary partner (Berk's infeasible share) | solo / scip2 / ea0 / ea20, 80 MIPLIB, 60 s | **−** | no gain; loses to equal-compute SCIP‖SCIP | same |
| LLM1 | 09-24 07:36–10:23 | LLM agents in the loop (D-004 2×2) | default / best fixed / Laya agent / Ornith / Ornith+Laya / GPT-6 Luna, 30 ML4CO test × 2 seeds, 120 s | **=** | Ornith 0.115 ≈ Laya 0.116 ≈ fixed 0.126; GPT-6 Luna 0.137 (latency) | [[2026-09-24-day]] |
| ✗ | 00:27 | exchange arms: SCIP start delay (~0.7 s, cuOpt library + second parse) | found in interim analysis | fixed, re-run | — | [[Mistakes and incidents]] |
| ✗ | 02:52 | EA feasibility test too loose (summed violations) | 26/176 impossible posts | fixed, re-run; first run in `_superseded/` | — | same |
| ✗ | 02:10–02:21 | — | my analysis job loaded the CPU during runs | re-run 172 runs | effect negligible | [[Mistakes and incidents]] |
| ✗ | 05:14 | contention v1 | crashed on a key clash | fixed, re-run | — | same |
| ✗ | 08:21 | — | B0 grid drove memory to 5 GiB → the host's memory watchdog shed | recovered 08:40 | — | same |
| ✗ | 10:50 | B2 driver | crashed on my own resource json | resumed 11:00 | — | same |
