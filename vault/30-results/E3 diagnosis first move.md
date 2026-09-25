# E3 — diagnosis first move: predict the setting at t = 0 (17:57–19:58)

> **Correction 2026-09-24:** PDI (primal-dual integral) values in this note were computed with an integration error (times rounded before lookup) and are superseded; the primal integral P is unaffected. Corrected numbers: paper and AGENTS.md; details in [[2026-09-24 repository review — response and plan]].


**Question:** can a model reading the instance pick the right SCIP setting before the solve and beat the online bandit?
**Design:** train 6 static settings × 60 ML4CO *training* instances (30 item placement, 30 load balancing; 120 s, seed 0,
pinned, 9 GiB cap, agents stopped); LightGBM cost regressors on the 62 static features; scored exactly on the 30 E2 test
instances × 2 seeds (all 6 settings recorded there) against default, best fixed (learned on training), family majority,
bandit, static oracle; plus a **diagnose-then-bandit** agent (predicted setting first with an optimistic prior, bandit after).
Chain `experiments/diag_chain.sh`, analysis `analysis/diag.py`, data `datasets/diag_results.json`. SCIP traces corrected.

**Result — P(120), vs SCIP default (n = 60):**
| policy | P | vs default |
|---|---|---|
| default | 0.196 | — |
| best fixed from training (aggressive heuristics) | 0.140 | +28.5 % (p = 3e-6) |
| family majority | 0.141 | +28.3 % |
| LightGBM per-instance diagnosis | 0.150 | +23.4 % |
| bandit, 10 s / 5 s | 0.156 / 0.144 | +20.3 % / +26.5 % |
| **diagnose-then-bandit** | **0.139** | **+29.1 % (p = 0.001)** |
| static oracle per run (hindsight) | 0.128 | +34.8 % |
PDI: best fixed +6.0 %, LightGBM +1.8 %, bandit5 +3.8 %, diagnose-then-bandit +1.0 %.

**Reading:** on a known family, the best setting learned from training instances beats a per-instance prediction
(LightGBM spread its picks and lost ~5 points). The diagnose-then-bandit agent is the best agent and ties the best fixed
setting — prior knowledge plus online correction — but does not beat it. Same lesson as every other experiment: the
value is in choosing the right configuration early; within a family, "the right one" is mostly one setting.
**Incident:** the chain's final restore step stopped its own unit and died; agents came back 4 minutes late by hand.
