# Response to the repository review of 2026-09-24

Reviewers: Claude Fable 5.1 (Anthropic) and OpenAI GPT-6 Astra (ChatGPT).

Review: `transient_work/repository_review.md` (with `audit_pdi.py`, `pdi_sensitivity.json`; kept out of git).
Response by AgentRA (Agent Research Assistant; mainly Claude Opus 5.5). Every claim below was checked against the code
and data before answering; where I disagree, the reason is given.

**Overall:** the review is accurate, specific and useful. It found one material measurement bug (PDI integration) that
changes a claim in the paper, confirmed three smaller code defects, and made sound inference and reporting points. I
disagree with it mainly on severity where the library version already addresses a point or where the data show no
effect — noted per item.

## Verdicts

| # | Review point | Verdict | Evidence checked | Planned change |
|---|---|---|---|---|
| 1 | PDI rounds change times, then looks up at the rounded time → missed updates | **Agree — confirmed, material** | minimal example returns 1.0 (expected 0.1); `enlight_hard S0` 1.0 vs ~5e-5 | exact-time merge (done in the library copy), regression tests, full re-score, correction entry |
| 2 | B2 gate measures total headroom, not the switching increment | **Agree on the code; partly disagree on impact** | `b2_gate.headroom()` = best static → full oracle | shared decomposition function + fixture; describe the gate as an allocation heuristic. The gate only decided *how many* instances to run; every reported B2 number comes from `b2_decomp.py`, which uses the static/switching split |
| 3 | Missing `solu.txt` silently switches to best-observed references | **Agree for the working repo; already fixed in the library** | working repo: `solu()` returns `{}` if the file is absent; library ships `optopt/references/miplib2017.solu` | fail loudly if a paper build lacks references; provenance manifest (opt vs best-known, source, hash) |
| 4 | Beating a `=best=` value is scored invalid, not flagged | **Partly disagree** | across 5,424 traces with a MIPLIB reference, exactly one incumbent beats it: cuOpt's placeholder 0.0 on dano3_3 (a known cuOpt error-status quirk), correctly scored invalid | keep the conservative scoring, but flag each case, validate it with the checker, and record it; no result changes |
| 5 | `OPTOPT_DATA` does not round-trip (`rel` → `data/…`, `resolve` → workspace) | **Agree — confirmed** | `OPTOPT_DATA=/tmp/x`: `resolve(rel(p))` points into the workspace | map the logical `data/` prefix to `DATA`; round-trip test with an external data dir |
| 6 | Runs keyed by basename/strategy/seed; stale traces reused; `ok` = file exists | **Agree** | `pool.py` skip-if-exists; exit codes only checked in `xchg_pair` since 2026-09-24 | config hash in each trace, manifest validation before skipping, exit codes + bounded stderr, completion record with expected/observed/missing/failed |
| 7 | Separate action timing from action choice (HEU via the same callback path) | **Agree — worth running** | our own paper already attributes ~8 % to timing | new arm `A:fixedHEU-cb` (deterministic agent that sets HEU at the first eligible event), plus first-action-only and replay arms; same 30 instances × 2 seeds |
| 8 | "first decision at t = 0" is really "first eligible solver event"; intervals are thresholds | **Agree** | `_Hdlr.eventexec` | log requested vs actual call time; captions say "first eligible solver event" |
| 9 | Agent state uses the stale primal bound at BESTSOLFOUND | **Agree — confirmed** | `_agent_step`: `m.getPrimalbound()` | use the new solution's objective (as the recorder does); note which agent runs were affected (bandit and LLM decisions at incumbent events) |
| 10 | Wilcoxon on instance-seed rows; seeds are not independent instances | **Agree** | `agents_llm.py`, `diag.py`, `pilot_e*.py` | average within instance, instance-level paired tests and bootstrap CIs; mark comparisons exploratory unless pre-specified |
| 11 | Hosted arm has one seed; raw means mix seed support | **Agree** | `tab:llm` | seed-0-only comparison table + multi-seed robustness table |
| 12 | Selection bootstrap resamples instances though PGLib is grouped by 3 systems | **Partly agree** | pooled 5-fold is instance-level; the leave-one-family-out scheme already tests family generalisation | add family-macro averages and a system-level sensitivity row; say the pooled CI is conditional on the fitted models |
| 13 | "Not significant" ≠ equivalence | **Agree** | wording in §5 | state the pre-set practical threshold (10 % headroom, fixed before any run) and report upper bounds as the equivalence-style statement |
| 14 | Features are precomputed before the clock; not a cold-start benchmark | **Agree on reporting; partly disagree on bias** | features are loaded before the solve clock for LightGBM, Laya and LLM arms alike; default and fixed arms need none; max extraction time 5.2 s | report feature extraction time separately and a deployment budget including it; comparisons *between* learned arms are unaffected, comparisons with defaults can favour learned arms by at most ~4 % of a 120 s budget (more at 10 s — Track A) |
| 15 | Solution checking covers stored *final* SCIP incumbents only; coverage records missing | **Agree** — and a further checker bug found today | SCIP stores the final incumbent; no `solcheck_llm_agents.csv`, `solcheck_diag_train.csv`; the checker was also nondeterministic (fixed 2026-09-24, see incidents) | full re-check running; coverage manifest; nonzero exit on failures; checker fixtures; paper wording "final SCIP incumbents" |
| 16 | Locked environment, build graph, protocol-compliant quick start | **Already addressed in the library** (review read the working repo) | library: exact pins, `optopt reproduce` runs the full chain incl. B2/B3/diagnosis/LLM/exchange, README quick start pins cores and caps | smoke tests for callbacks and ingestion (agree, to add) |
| 17 | `Trace.to_json` can emit `Infinity`/`NaN` | **Agree — confirmed** | `json.dumps(..., default=_clean)` | recursive clean + `allow_nan=False`; validate timestamps and budgets |
| 18 | Claim registry generated from results | **Partly agree** | AGENTS.md is a hand-kept registry | generate the numbers in AGENTS.md from `datasets/` (cheap); a full metric-version registry is deferred |
| 19 | Stale docs (LLM arms "not run", 8 vs 9 GiB, B0 not pinned) | **Agree — confirmed** | AGENTS.md line 57 | fix; keep the ancillary copy byte-identical by generating it |
| 20 | Soften universal wording ("not continuous steering") | **Agree** | abstract/discussion | scoped conclusion: "within the tested settings, families, hardware and budgets…" |
| 21 | Research directions 1–4 | **Agree**, with 4 weakened by the fix (see below) | — | timing-matched controls first; fresh confirmation cohort; short diagnostic probe; bound switching only if a pre-registered test still motivates it |
| 22 | Direction 5: finish the heuristic-plugin exchange rerun | **Done after the review was written** | 80 instances, no failures: race +26.4 % over SCIP alone, SCIP's own trajectory +14.1 % with cuOpt's solutions | keep event-handler and plugin runs separate (done in the appendix) |
| 23 | Live confirmation of the recommended HiGHS‖cuOpt pair; resource accounting | **Agree** | live runs so far are SCIP‖cuOpt | one live HiGHS‖cuOpt run (80 × 60 s); record CPU threads incl. cuOpt host threads, GPU occupancy, peak memory; energy only if measured reliably |

## Impact of the PDI fix (library copy, `optopt reproduce`, 15 derived files changed)
The primal integral — the primary metric — is unaffected. On PDI:

| Result | Before | After |
|---|---|---|
| B2 (120 s): static / switching | 7.6 % / 2.4 % [−0.3, 6.8] | 6.5 % / 1.6 % [−0.1, 3.8] |
| **B3 (300 s): static / switching** | 3.7 % / **6.8 % [−1.1, 18.8]** | 11.3 % / **1.5 % [−0.2, 4.3]** |
| B3 best arm by mean (PDI) | schedule 0.332 vs best static 0.357 | schedule 0.313 vs best static 0.316 |
| SCIP copies k = 2 / 3 / 5 | 6 / 10 / 16 % | 5.5 / 7.5 / 9.4 % |
| Diagnosis: fixed setting / LightGBM | +6.0 / +1.8 % | +2.9 / +0.8 % |
| LLM arms (PDI means) | 0.52–0.54 | 0.49–0.51, still all within 3 % |
| B1: separation off vs default at 120 s | worse on PDI | still worse on PDI (0.269 vs 0.249) |

**The paper's statement that switching "starts to pay for the bound at 300 s" was an artifact of the bug and is
withdrawn.** The corrected result strengthens the main conclusion: at 30–300 s the static choice explains most of the
headroom on both metrics.

## Plan (order proposed by the review, which I agree with)
1. **P0 — PDI:** exact-time integration (done in the library copy), regression tests (rounding down/up, lone closing
   event, simultaneous updates, events at the budget edge, random traces against an independent reference), full
   re-score, paper and AGENTS.md corrected, incident entry.
2. **P0 — gate:** shared decomposition function used by gate and report; fixture "static large, switching zero";
   appendix describes the gate as an allocation heuristic.
3. **P1 — safeguards:** reference manifest + fail-loud; `OPTOPT_DATA` round-trip; run identity (config hash,
   manifest, exit codes); strict trace serialization; agent state at BESTSOLFOUND; checker coverage manifest and
   fixtures (after the running re-check reports).
4. **P1 — inference and reporting:** instance-level tests for all agent/diagnosis comparisons; seed-0 table for the
   hosted arm; family-macro and system-level rows for selection; timing boundary reported; scoped wording; stale docs.
5. **Experiments (need a memory window — stopping the deep-research agent's model server again, with Berk's OK):**
   timing-matched static controls (≈ 60–120 runs × 120 s); live HiGHS‖cuOpt pair (80 × 60 s).
6. **Paper freeze** → then new confirmation experiments (fresh cohort, diagnostic probe).

## Where I disagree, in short
- **Gate (2):** the defect is real, but it did not produce any reported number; it only set the sample size.
- **Best-known references (4):** conservative scoring is intended; the data contain one case, a true invalid incumbent.
- **Feature timing (14):** does not bias comparisons among the learned arms; bounded (~4 %) against the defaults at 120 s.
- **Reproducibility package (16):** largely done in the library version, which the review did not see.

## Implementation status (2026-09-24 afternoon, library version)
| # | Item | Status |
|---|---|---|
| 1 | PDI exact-time integration | **done** — `metrics.primal_dual_integral`; 10 regression tests incl. random traces vs a brute-force reference (`tests/test_pdi.py`); the old function fails them |
| 2 | Gate on the switching increment | **done** — `analysis/decomp.py` shared by gate, B2 and B3; fixture "static large, switching zero" (`tests/test_decomp.py`) shows the old gate would say GO |
| 3 | References | **done** — MIPLIB references ship with the package; `build_runs` refuses to fall back for MIPLIB; `optopt analyse references` writes `datasets/reference_manifest.csv` (79 opt, 1 best-known, 283 best-observed) and `reference_flags.csv` (1 flag: cuOpt placeholder 0.0 on dano3_3) |
| 4 | Better-than-reference | **done as planned** — scoring unchanged (conservative), every case flagged in `reference_flags.csv` |
| 5 | `OPTOPT_DATA` round trip | **done** — `resolve()` maps `data/` to DATA; test |
| 6 | Run identity | **done** — `config_hash` in every new trace; pool reuses only matching traces, reports stale ones, `--rerun-stale`; exit codes + stderr tail; completion record (expected/reused/failed/stale) |
| 7 | Timing-matched controls | **running** — `timing_ctrl`: default, C:HEU, A:heu_cb (HEU through the agent callback), A:llm_first, A:llm × 30 × 2 seeds |
| 8 | "First eligible solver event" | **done** in the paper and AGENTS.md |
| 9 | Agent state at BESTSOLFOUND | **done** — agents now see the new incumbent's value; only the control runs were recorded after the fix |
| 10 | Instance-level inference | **done** — `analysis/stats.py`; applied to LLM, diagnosis, pilots, B1, B3. LLM vs fixed becomes n.s. (p 0.09) |
| 11 | Seed-0 table for the hosted arm | **done** — in `datasets/llm_agents.json` ("seed 0 only" comparisons) |
| 12 | Family-macro selection | **done** — reported in the paper: per family, selectors fall below each family's best fixed at 10 s (driven by PGLib-UC); at 30 s only Laya stays above |
| 13 | Equivalence wording | **done** — limitations paragraph; upper bounds reported |
| 14 | Timing boundary | **done** — feature extraction (median 0.3 s, max 5.2 s) stated as not charged |
| 15 | Checker coverage | **done** — `optopt analyse solcheck_coverage`; checker exits nonzero on failure, checks the model was read; 8 fixtures; full re-check with the fixed checker running |
| 17 | Strict trace JSON | **done** — `allow_nan=False` + recursive clean; test |
| 19 | Stale docs; synced companion | **done** — AGENTS.md corrected; `optopt reproduce` fails if `paper/anc/AGENTS.md` differs |
| 20 | Scoped wording | **done** — "within the settings, families, hardware and budgets we tested" |
| 23 | Live HiGHS‖cuOpt | **running** — `xhighs`: hrace (H1 ‖ C0) and hsolo (H1 alone), 80 MIPLIB × 60 s |
| — | Solver smoke tests | **done** — `tests/test_solver_smoke.py` (maximisation, trajectory, saved solution, agent callback, strict JSON) |

Corrected PDI-based numbers are in the paper; the appendix has a "Corrections after an external review" paragraph.
Restart simulation (S1) re-run: hindsight oracle 5.8 / 3.5 / 2.3 % at τ = 10 / 20 / 30 s (was 11 / 3–4 %); learned
policy 5–8 % worse than never restarting. B0 PDI oracle gain 5.8 % (was 2.3 %). Tests: 42 passing.

# Second review (second reviewer, `transient_work/second review`)

| # | Point | Verdict | Evidence / action |
|---|---|---|---|
| 1 | Session drift between days | **Agree — confirmed** | same arms, same 60 runs: default 0.7 %, C:HEU 2.7 % worse on 09-24 (47/60 and 54/60 runs worse, p ≤ 2e-7). Paper states a within-session rule and a ~3 % cross-session floor; the timing controls are one session; the HiGHS pair interleaves hrace/hsolo; a same-session SCIP-alone vs race re-run follows the HiGHS pair |
| 2 | Resource record `serving_units` empty in the library | **Agree — regression fixed** | runner now records running model-server services unconditionally; the timing_ctrl record was completed from the session log, marked as added afterwards |
| 3 | Library copy not under version control | **Agree — fixed** | `git init` + commits as AgentRA |
| 4 | `berkorbay/optopt` does not exist yet | **Agree; on hold by the author's decision** | the author asked not to create the public repository yet; it is created before any arXiv upload |
| 5 | False infeasible committed (drayage-100-23), stale 1,713 sentence | **Agree** | the re-check with the fixed checker overwrites all CSVs; the appendix sentence is rewritten from the post-fix coverage report |
| 6 | Orphaned generated texts | **Agree — fixed** | 5 stale prose files removed (no writer); 3 extra tables are regenerated from current data and kept; AGENTS.md says only what main.tex inputs is the paper |
| 7 | cuOpt/HiGHS incumbents unchecked | **Agree** | from today every solver stores its final incumbent (tested); for past runs the paper cites cuOpt's own report (max constraint violation 9.8e-7 over 1,189 traces, none above 1e-6) and SCIP's acceptance of cuOpt's solutions on 38 instances |
| — | HiGHS callback lag | **Agree, cited as verified** | appendix |
| — | LLM contrasts decided by item placement | **Agree** | stated in the paper |
| — | Budget excludes model reading | **Agree** | "the budget starts once the model has been read" + read times in the paper |
| — | O(n²) set in the checker | **Agree — fixed** | |
| — | Working repo abstract still has the withdrawn sentence | **Agree** | the working repo receives the final paper at wrap-up |

### Correction to point 7 (cuOpt feasibility), 2026-09-24 15:05
The mitigation cited above — cuOpt's own `max_constraint_violation` ≤ 9.8e-7 on every trace — does **not** establish
feasibility at 1e-6. The first stored cuOpt solutions (36, HiGHS‖cuOpt runs) were checked: one (supportcase26) violates
three rows, the worst by 2.0e-4 absolute (4.9e-5 relative), while cuOpt reported 8.0e-7 for that run. cuOpt's defaults
are `mip_absolute_tolerance` 1e-6 but `absolute_primal_tolerance` and `relative_primal_tolerance` 1e-4, and its reported
violation is evidently on a different (normalised) scale. So cuOpt objectives can come from solutions that are feasible
only at ~1e-4. All 67 stored HiGHS solutions pass at 1e-6; solutions SCIP accepted from cuOpt passed SCIP's own 1e-6
check. The same-session race re-run (`xsame`) stores cuOpt's final solution on all 80 instances; its check gives the
rate, and the paper states it with the tolerance difference.
