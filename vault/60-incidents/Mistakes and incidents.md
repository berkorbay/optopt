# Mistakes and incidents (for the record — all mine unless noted)

| when | what happened | effect | fix / lesson |
|---|---|---|---|
| 00:27 | Laya download CLI treated glob patterns as filenames → pulled two extra sub-models | 36 MB wasted | stopped; explicit `--include` |
| 00:45 | two PGLib-UC converters raced on gzip | none (files re-verified) | one converter as a unit |
| 01:08, 01:57 | HiGHS on s100 and cuOpt C1 on sorrell3 ignored the time limit, killed at 150 s | scored as failures (P = 1) | U1 reproductions |
| 02:10–02:21 | my selection preview used all cores (LightGBM/torch defaults) beside 12 solver lanes | 172 CPU runs re-run; effect negligible (0.197 vs 0.195) | analysis single-threaded, on efficiency cores |
| 02:50 | GPU lanes behind plan | ML4CO train cut to 75/family, cuOpt variance seeds dropped | D-001 addendum |
| 05:14 | contention script crashed on a duplicate key | 1 lost run | fixed, re-run |
| night | Track A lanes unpinned on heterogeneous cores (X925 vs A725 ≈ 2× node rate) | extra noise in Track A / B0 | pin one run per X925 core from B1 on |
| 08:21 | B0 grid (10 SCIP × up to 6 GB) beside both LLM servers → MemAvailable 5.1 GiB → the host's memory watchdog shed the operator's remote sessions, the fast chat agent (Hermes Agent with Ornith-1.5-35B-A3B, NVFP4 on vLLM) | Berk lost control ~20 min | D-003: hard per-run caps, lane budget check, stop agents deliberately |
| 08:40 | cited ParamILS for F-Race in the paper | wrong citation | removed; placeholder until Birattari is verified |
| 10:50 | B2 driver crashed on my own resource-record json inside traces/raw | ~9 min idle | resource records moved to traces/resources |
| 11:42 | the B2 gate measured total headroom (static + switching) | could have said GO for the wrong reason | verdict re-scored on the switching increment |
| 10:50 | property tests exposed a metric edge (incumbents beyond the reference) and a cuOpt placeholder objective in a final-objective field | none published changed | primal_gap rule; wrapper fix |
| 13:40 | pausing an unrelated host job over its slot | host job missed one run, re-anchored | left for Berk |
| 17:30 | solution checker (exact over every row) started on all 20 cores and too slow on large instances | none (stopped) | float + exact re-check near tolerance; efficiency cores only |
| 18:50 | cuOpt status codes mislabelled in the wrapper (8 = FeasibleFound, 5 = TimeLimit without solution) | labels only | fixed |
| 19:05 | solution check complete: 1,713 checked, 1,709 strictly within 1e-6, 4 at the tolerance boundary (1.0000001e-6; neos-3046615-murg, HEU arm) | no real infeasibility | reported as such in the paper |
| 19:10 | **SCIP recorder lag:** at BESTSOLFOUND, getPrimalbound() still holds the previous incumbent, so every SCIP incumbent event stored the previous solution's value (found by a tutorial example) | SCIP primal integrals pessimistic, more for settings that reach nodes later; "separation off" advantage partly an artifact (B1: 27→20 % at 30 s) | exact correction of 3,918 traces (`analysis/fix_scip_traces.py`), recorder fixed, everything re-scored; conclusions unchanged; Laya retrain on corrected labels pending |
| 19:30 | analysis scripts broke on new experiment folders (build_runs and pairs read every set; B0 arm list gained B1's arm) | stale tables for ~20 min | loaders restricted to their own sets |
| 19:58 | diag chain's last step ran the restore script inline; the script's first action stops the chain unit → it killed itself | agents back 4 min late (by hand, 20:02) | chain now launches the restore as a separate unit |

## 2026-09-24 night
- **Exchange arms measured a start delay, not the exchange** (found 00:27): SCIP's process loaded cuOpt's library and
  parsed the MPS a second time to map variables — inside the pair's wall clock, ~0.7 s. Interim result "exchange worse on
  13/17" was this artifact. Fix: exchange in SCIP's own order, the partner maps. Affected runs re-run. Lesson: anything a
  treatment arm does before its solver starts is part of the treatment; check start offsets against the control.
- **EA feasibility test too loose** (found 02:52): sum of normalised row violations ≤ 1e-6 × rows — 26 of 176 posts claimed
  objectives better than the known optimum. SCIP rejected them, so SCIP's numbers were safe, but the arm was unfair to the
  idea. Fixed to per-row tolerances; re-run; the first run kept under `traces/raw/_superseded/`.
- **Silent native crashes**: the pair driver logged "ok" whenever a process exited; 9/80 SCIP runs per exchange arm died
  with no trace. Now the exit code is logged and a missing trace scores as a failure. Cause not isolated (not reproducible
  in isolation); trySol from an event handler is the suspect.
- **Auto-mode classifier blocked stopping the serving units** until Berk answered explicitly — correct behaviour; ask first.

## 2026-09-24 07:06 — the host's memory watchdog shed caused by an uncapped GPU fine-tune (second shed caused by optopt)
- I started the Laya fine-tune (`agents/laya_service.py --train`) on the GPU with BOTH local models up, without a
  systemd MemoryMax and without a MemAvailable check. GPU allocations are system RAM on the GB10; MemAvailable fell to
  7.9 GiB, the host's memory watchdog hit its HARD floor, shed the operator's remote sessions (restored by an automatic session restore at 07:10) and
  `the Ornith-1.5-35B-A3B server (vLLM)` stopped 07:07:30 (down until I restarted it ~07:30). The training was SIGKILLed (exit 137).
- No cron run was lost (every run 06:45–07:25 completed); chat bridges, the model gateway, gateway and the DBs stayed up.
- Rule (extends D-003): **GPU jobs — training, model services, anything that loads a model — count against the memory
  budget. Run them only under `systemd-run --user -p MemoryMax=… -p MemorySwapMax=0`, after checking MemAvailable, and
  never while both local models are up.**
- **Caveat found right after:** the capped re-run (`systemd-run -p MemoryMax=16G`) reported a *memory peak of 508 KiB* for
  a job that loaded 1.6 GB of weights onto the GPU — the cgroup does not see CUDA/unified-memory allocations here. So
  `MemoryMax` bounds CPU-side solvers but NOT GPU jobs; for GPU work the protection is the MemAvailable check before
  launch and never running beside both local models.
