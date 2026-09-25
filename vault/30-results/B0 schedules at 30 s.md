# B0 — node-selection / heuristic / cut schedules in SCIP at 30 s (07:52–08:36) — NEGATIVE

> **Correction 2026-09-24:** PDI (primal-dual integral) values in this note were computed with an integration error (times rounded before lookup) and are superseded; the primal integral P is unaffected. Corrected numbers: paper and AGENTS.md; details in [[2026-09-24 repository review — response and plan]].


**Question:** is there headroom in switching SCIP settings mid-solve? (go/no-go gate 15–20 %)
**Design:** 45 non-trivial MIPLIB instances × 12 arms × seeds 0/1, 30 s. Static: default, DFS, BFS, aggressive heuristics (HEU),
separation off (NOC). Schedules: DFS→D / DFS→BFS at first incumbent, HEU→D and NOC→D at 25 %, D→BFS / D→DFS / D→HEU at 50 %.
Held-out-seed scoring. Runs unpinned, both LLM servers resident (see [[Mistakes and incidents]]).
**Result:** best static = NOC (−17 % P vs default). Full oracle over all arms vs NOC: **+0.8 % (P), +4.7 % (PDI)**; same-seed oracle
would claim 6–12 % (noise). No schedule beats NOC universally. **Gate fails.**
**R1 racing replay:** ordering instances by Track A discriminativeness reaches the same verdict with 65 % of runs (random 92 %).
Racing is for picking the best single arm — it is the wrong tool for a headroom gate (see B2 design).
Data: `datasets/b0_gate.json`, `traces/raw/b0_scip/`. Script: `analysis/b0.py`, `experiments/race.py`.

> **SCIP recording correction (19:10, see [[Mistakes and incidents]]).** After correction: best static still NOC (9.4 % better than default on P, was 17 %); held-out oracle over all arms +3.2 % (P) / +2.3 % (PDI) over NOC, almost none of it from the schedules. Gate still fails.
