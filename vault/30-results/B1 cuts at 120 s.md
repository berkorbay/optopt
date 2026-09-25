# B1 — separation off vs default at 120 s, clean hardware (08:47–09:05) — NEGATIVE for switching

> **Correction 2026-09-24:** PDI (primal-dual integral) values in this note were computed with an integration error (times rounded before lookup) and are superseded; the primal integral P is unaffected. Corrected numbers: paper and AGENTS.md; details in [[2026-09-24 repository review — response and plan]].


**Design:** 30 B0 instances with the largest spread among these arms, 4 arms (D, NOC, NOC→D@25 %, NOC→D@50 %), seed 0, 120 s,
**first run pinned one per Cortex-X925 core, 8 GiB hard cap, LLM servers stopped**.
**Result:** NOC vs default on P: +27 % @30 s (Wilcoxon p = 0.002), +24 % @60 s (p = 0.02), +14 % @120 s (p = 0.08); on PDI
+12 % → +7 % → 0 %. Switching cuts back on gains nothing (±1 %, n.s.). Selection caveat: instances chosen where arms differed.
Data: `datasets/b1_results.json`. Script `analysis/b1.py`.

> **SCIP recording correction (19:10, see [[Mistakes and incidents]]).** After correction: NOC vs default on P +20 % @30 s (p = 0.009), +17 % @60 s (n.s.), +5 % @120 s (n.s.); on PDI +6 % → −5 % → −20 % (NOC worse on the bound by 120 s). Switching still gains nothing.
