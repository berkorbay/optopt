# E1–E2 — agent in the loop, end to end (14:23–16:09)

**Design (D-004):** agent starts from SCIP defaults; 1 Cortex-X925 core + 9 GiB; 120 s wall clock including every decision
(agent called from SCIP's event handler; clocktype = wall, verified). Agents: online bandit (UCB1 over 6 static settings, reward =
gap progress per interval + new incumbent), rules agent (from component results).
**E1** (35 held-out: 20 ML4CO test + 15 MIPLIB not used for rules; 2 seeds): bandit **+8.2 % P (p = 0.003)**, ML4CO +20.4 %
(p = 0.0005), MIPLIB +1.6 % n.s.; rules **−2.6 % n.s.** (rules from MIPLIB averages do not transfer); 2× default on 2 cores +10.9 %.
**E2** (30 fresh ML4CO test, 2 seeds): bandit 10 s +21.3 % (p = 2e-5), 5 s **+27.8 %**; item placement ~+30 % (28/30 better); load
balancing no gain.
**E2c control:** fixed HEU from t = 0 on item placement 0.240 vs bandit 0.247 (n.s.), 13 % better at 60 s → **the bandit finds the
right static setting online and pays for exploring; it never beats the best static setting for the family.**
All 483 agent/static incumbents verified. Data `datasets/pilot_e.json`, `datasets/pilot_e2_static.json`.

> **SCIP recording correction (19:10, see [[Mistakes and incidents]]).** After correction: E1 bandit +8.6 % (p = 0.007), ML4CO +21.4 %, MIPLIB +1.8 % n.s., rules −2.7 %. E2 bandit 10 s +20.8 %, 5 s +27.1 %; item placement default 0.350 / bandit5 0.244 / fixed HEU 0.238 (bandit −2.5 % vs HEU, n.s.; −12.5 % at 60 s, p = 0.047). Conclusion unchanged.
