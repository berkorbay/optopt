# B2 — restarts, branching rule, heuristic scheduling (10:24–13:31) — NEGATIVE for switching

> **Correction 2026-09-24:** PDI (primal-dual integral) values in this note were computed with an integration error (times rounded before lookup) and are superseded; the primal integral P is unaffected. Corrected numbers: paper and AGENTS.md; details in [[2026-09-24 repository review — response and plan]].


**Design:** 45 MIPLIB × 12 arms × 2 seeds, 120 s, pinned, 9 GiB cap, sequential gate in blocks of 5 instances.
Static: D, NOC, PSC (pseudo-cost branching), INF (inference branching), HOFF, HEU. Dynamic: restart at 25 %, restart after 20 % stall,
PSC→D@25, D→PSC@25, HEU→HOFF@25 (burst), HOFF→HEU after stall. Script `experiments/b2_gate.py`.
**Result (decomposed, held-out):** static choice per instance +10.8 % (P) / +7.1 % (PDI); **switching on top +2.8 % [−0.4, +7.9] /
+1.7 % [−1.2, +5.5]**; run-level (hindsight) +5.5 / +12.3 pts. The coded gate measured the *total* and said INCONCLUSIVE — a design flaw
(it could have said GO on static selection alone); the verdict was re-scored on the switching increment.
**B2s (5 seeds, 20 instances):** instance-level static oracle +7.7 % (P) / +14.0 % (PDI); per-seed winner = mean winner 75 % / 64 %;
seed s.d. 0.032 / 0.064 vs between-setting 0.095 / 0.103. Parallel copies of NOC k = 2/3/5: +7.1 / +9.4 / +11.5 % (P).
All B2 incumbents checked (`datasets/solcheck_b2_scip.csv`).

> **SCIP recording correction (19:10, see [[Mistakes and incidents]]).** After correction: static choice +11.8 % (P) / +7.6 % (PDI); switching on top +2.1 % [−0.4, +7.3] / +2.4 % [−0.3, +6.8]; run-level 5.0 / 10.1 pts; best static INF (P) / PSC (PDI). 5 seeds: instance-level oracle +9.8 % / +12.1 %, winner stable 71 % / 62 %, parallel copies k = 2/3/5: P +7.2/+9.3/+11.2 %, PDI +6.3/+9.8/+16.1 %. Conclusion unchanged.
