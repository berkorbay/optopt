# Track A · Milestone 1 — static strategy selection (2026-09-23 night)

> Track A (cross-solver selection), frozen at tag `track-a-night1`. The primary question is Track B — see
> [[D-002 Two tracks — in-solver control is the primary question]].

**Question** (spec §26): given an unseen MIP, can a learned policy predict which HiGHS / SCIP / cuOpt strategy
gives the best result within a fixed budget, and how much of the oracle's headroom does it capture?

**Answer: the headroom is real; static-feature selection captures little of it; a CPU‖GPU pair captures most.**

## Data
313 instances with full 6-strategy traces: MIPLIB 80 (60 s), ML4CO item placement 100 and load balancing 100
(30 s; 75 train + 25 test per family have cuOpt), PGLib-UC 33 of 56 (60 s; 23 cases got no incumbent from any
strategy). Seed 0; variance subset 12 MIPLIB × HiGHS/SCIP × 5 seeds. Tables: `datasets/*.csv`, paper
`paper/generated/`.

## Headroom (phase 1) — PASSES the 10 % go/no-go
| | SBS | P(SBS) | oracle | headroom |
|---|---|---|---|---|
| MIPLIB @60 s | H1 | 0.337 | 0.203 | 40 % |
| item placement @30 s | H1 | 0.207 | 0.177 | 14 % |
| load balancing @30 s | H1 | 0.092 | 0.064 | 30 % |
| PGLib-UC @60 s | C0 | 0.640 | 0.574 | 10 % |
| pooled @30 s | H1 | 0.278 | 0.215 | 23 % |

- ≈85 % of the headroom survives seed noise (single-seed oracle 37.1 % apparent → 31.8 % realised; true 34.8 %, after the clean re-runs).
- SBS depends on budget: C0 at 10 s on MIPLIB / load balancing, H1 at 30–60 s.
- By difficulty (300 s screening bands): H1 best on everything HiGHS/SCIP can solve; **cuOpt C0 best on the 37
  instances neither solves in 300 s** (P(60) 0.426 vs 0.532).

## Learned selection (phases 2 + 4) — closed gap, 0 = SBS, 1 = oracle
| policy | pooled 10 s | pooled 30 s | LOFO 10 s | LOFO 30 s |
|---|---|---|---|---|
| best fixed (train) | 0.00 | 0.00 | −1.22 | 0.00 |
| hand rules (pre-registered) | −0.21 | −0.23 | −0.41 | −0.51 |
| LightGBM | +0.17 [−0.16, 0.43] | −0.13 | −0.10 | −0.58 |
| MLP | −0.02 | −0.05 | −0.27 | −0.68 |
| Laya zero-shot | −0.73 | −0.97 | −1.49 | −1.79 |
| **MIP-Laya (fine-tuned)** | **+0.19 [−0.02, 0.37]** | −0.06 | **+0.04 [−0.05, 0.13]** | −0.38 |

Reading: at 10 s MIP-Laya ≈ LightGBM, and MIP-Laya is the only policy not below SBS out of family; at 30 s
nobody beats "always H1". One fine-tuning seed; intervals touch 0. **Spec rule "if LightGBM is as good, use
LightGBM" → no case yet for Laya on static selection.**

## Not choosing: CPU‖GPU pair (offline, exact from traces)
H1‖C0 (1 HiGHS thread + cuOpt on GPU, best incumbent of the two) is the best pair in every family:
pooled 0.254 → **0.199** vs oracle 0.190 (≈86 % of headroom); MIPLIB 0.220 (oracle 0.203); load balancing 0.062
(< single-strategy oracle 0.064); UC 0.568 (oracle 0.574). Restart-switching is much weaker. → issue #16.

## Overhead
Laya decision 22.5–31.6 ms median (two measurements, idle GPU, batch 1) → 0.1 % of 30 s. Static features: median 16–431 ms
for MIPLIB/ML4CO, ~2 s on UC — dominated by MPS parsing, which the solver repeats.

## GPU contention (spec §15)
cuOpt C0 30 s, 5 MIPLIB × 2 reps: A alone 0.226 · B Laya idle-loaded +0.014 · C one decision / 5 s +0.009 ·
**D continuous inference +0.226 (P doubles)**. SM clock unchanged. Use sequential / low-duty-cycle calls.

---
See also the Track B results (B0–B2, main-experiment pilot) in `20-journal/2026-09-23-trackB.md` and the checkpoint.
