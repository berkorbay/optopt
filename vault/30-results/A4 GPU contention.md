# A4 GPU contention — does Laya slow cuOpt? (05:28–06:01)

**Question** (spec §15): can the decision model share the GPU with cuOpt?
**Design:** cuOpt C0, 30 s, 5 MIPLIB instances (CMS750_4, exp-1-500-5-5, neos17, tr12-30, timtab1) × 2 reps × 4 conditions,
Latin-square order, nothing else on the machine; nvidia-smi sampled every 0.5 s. Script `experiments/contention.py`.
**Result:** P(30) alone 0.226 · Laya loaded idle 0.240 (+0.014, median paired −0.004) · one call per 5 s 0.235 (+0.009) ·
continuous inference **0.452 (worse in 10/10)**. SM clock unchanged (2.39–2.41 GHz) → bandwidth contention, not power.
Laya latency beside cuOpt 30 ms median / 50 ms p90. **Rule: sequential or low duty cycle only.**
**First attempt failed** (05:14): the script crashed on a duplicate key when writing results; fixed and re-run.
