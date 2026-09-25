# S1 — restarting unpromising runs, offline (12:10) — NEGATIVE

> **Correction 2026-09-24:** PDI (primal-dual integral) values in this note were computed with an integration error (times rounded before lookup) and are superseded; the primal integral P is unaffected. Corrected numbers: paper and AGENTS.md; details in [[2026-09-24 repository review — response and plan]].


**Design:** from B2 traces, at τ continue the run or restart into another static setting (base events ≤ τ + other run shifted by τ;
incumbent and bound carried). 24 instances / 48 runs at the time. LightGBM on run state at τ (gap, bound movement, node rate,
incumbent age, static features), grouped 5-fold. Script `analysis/switch_sim.py`.
**Result:** hindsight oracle vs continue: +18 % (PDI, τ = 10 s) → +5 % (20 s) → +3 % (30 s); from NOC +14 % (PDI) / +12 % (P).
**Learned policy −1.5 … −16 % (worse than never restarting).** Conservative simulation (real restarts keep presolve info); small data.

> **SCIP recording correction (19:10, see [[Mistakes and incidents]]).** After correction, on all 45 instances (90 runs): oracle +11 % (PDI, τ = 10 s) → +4 % → +3 %; LightGBM ≈ −5 to −6 % vs continue (still worse than never restarting); from NOC on P: LightGBM +0.1 % (neutral), oracle +10 %.
