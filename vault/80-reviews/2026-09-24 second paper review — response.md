# Response to the second paper review (2026-09-24, night)

Review: "Academic peer review" of commit 511de867 (27-page PDF), recommendation **major revision**, positive on the
paper's potential. Response by AgentRA. Every concrete claim was checked against the committed data before answering.
Nothing in the paper is changed yet — Berk asked to discuss first.

**Overall:** the review is accurate. Its first point is a real error in the headline number, several others catch
wording that overstates what the design shows (some of it introduced in the plain-language rewrite), and two catch
factual slips (the ML4CO split, a self-contradictory sentence). I disagree with one requested propagation and note
where a request is Berk's decision.

## Verification of the concrete claims

| claim | check | result |
|---|---|---|
| 23 PGLib-UC cases dropped | `datasets/runs.parquet`: 23 instances with no reference, 0 incumbents in all 6 strategies, no score | **confirmed**; all 23 are FERC (23 of 24 FERC cases); CA 20 and RTS 12 all kept |
| pooled headroom 24.6 % → 19.4 % with them at P = 1 | recomputed from the table means: best fixed (313·0.278 + 23)/336 = 0.327, oracle (313·0.210 + 23)/336 = 0.264 | **confirmed**; UC at 60 s: 10.6 % → 5.1 % |
| "official test" instances are the ML4CO validation split | job paths `data/ml4co/instances/*/valid/…` | **confirmed** |
| resources table printed twice | `env.tex` and `appendix.tex` both `\input` it | **confirmed** |
| `optopt reproduce` exits 0 when a step fails | `reproduce.main` returns 1 only for changed files or AGENTS mismatch | **confirmed** |
| "matches the fixed setting because both act after presolve" contradicts the table | sentence refers to the arm set before presolve | **confirmed** (my wording) |
| "at most 2 % on PDI" | point estimates 1.5–1.6 %, upper 95 % bounds 3.8–4.3 % | **confirmed** (my wording) |
| timing control applies one setting to both families, not a rule per family | `A:heu_cb` = HEU for all 30 instances | **confirmed**; the abstract's "rule per family" is wrong for Table 6 |

## Point by point

**1. UC cohort — agree; different scope of propagation.** Report both estimands and name them: headroom on instances where
at least one configuration finds a solution (25 % pooled, 313 instances) and on all attempted instances with no-solution
runs at P = 1 (19 %, 336). Abstract: "19–41 %" with the definition. Add a flow table per family and system (attempted /
some solution / scored). Selectors: keep the existing experiment, labelled as a conditional-cohort experiment. With
predictions held fixed, adding k cases where every arm scores 1 scales each cost difference by n/(n+k), so the closed-gap
point estimates and the hindsight best-fixed configuration are unchanged; retraining could change predictions, the
bootstrap intervals depend on the resampled population, and coverage stays the conditional cohort (one FERC case).
Retraining is not needed to correct the headline headroom (see the resolution below). Headroom percentages and the
pooled pair gain do change. State that FERC is essentially absent from the UC results (1 of 24 cases).

**2. "Cannot be predicted" / limits on switching — agree.** Define the three parts algebraically; call the residual the gap to
a per-run hindsight oracle; say "limited additional transferable benefit from the six schedules tested"; give point
estimates and bounds separately; add intervals to Figure 2 (B2: `datasets/b2_decomposition.json`, key `ci`; B3: `datasets/b3_results.json`).

**3. Statistical language — agree.** "Statistically tied" → run the paired comparison of Laya and LightGBM out-of-fold costs
(cheap, from stored predictions) and report it, or say "no superiority established". "Nothing measurable" → "no detected
benefit (+3.6 %, interval −10.2 to +15.7 %)". Label selector intervals as conditional on the fitted models (they do not
cover retraining or fold variation). Name principal comparisons for reading (choosing vs switching; timing control), stating that they were identified
after the experiments; only the headroom threshold was set in advance, and nothing was pre-registered.

**4. "Judgement" — agree.** Rename to "LLM agent vs callback-fixed control": an end-to-end contrast including inference latency
(1.3 % of the budget) and later actions. Keep the latency-matched / action-replay control as optional future work.

**5. Archival evidence — agree.** Berk chose, in this session, to prepare a release archive; nothing is published until
the public repository exists and he says so. Pack `traces/raw`, `traces/sol`, launch records, resource
records, stored predictions and check summaries with SHA-256 checksums as a versioned release (GitHub release asset on the
public repository, or Zenodo for a DOI), and cite its identifier in the paper. README and `optopt reproduce` distinguish
*re-analysis of the archived study* (download the archive, then reproduce) from *a new replication* (re-run the jobs).
Fix `reproduce` to fail on any failed step.

**6. Operating conditions — agree.** Move the exceptions into Setup: Track A and B0 unpinned; the cross-solver oracle
single-seed; live pairs clock from process launch (includes model reading); agents' "one core" is the solver's slice,
while the local LLM server and cuOpt's host threads are extra compute — say "equal solver budget", not equal total
compute. Pair arms ran in a fixed order per instance (not randomised): state it. Intervals for the live pairs (instance
bootstrap, 4000 resamples): HiGHS‖cuOpt +30.4 % [17.7, 44.2] (80 instances, 61/13, p 5e-9); SCIP‖cuOpt +21.5 %
[9.3, 36.9] (44, 28/13, p 4e-5). Hardware transfer stated as open, not expected.

## Minor points
1 relabel "best fixed selected on training data" vs the hindsight best — agree. 2 define the fixed setting of Table 6 as one
setting for both families (HEU), and the family rule of Table 4 separately — agree. 3 contradictory sentence — agree, fix.
4 instance and seed counts in separate columns; "ML4CO validation split, used as held-out test" — agree. 5 warm-feature
note beside the 10 s result — agree. 6 checker covers final solutions only, not intermediate incumbents — agree; a
sensitivity at a common tolerance is possible for final values only. 7 reference policy: distinguish stale best-known from
infeasible — agree, one sentence. 8 "simulated, exactly" → "trace-based counterfactual estimate" — agree. 9 one readable
resources table — agree. 10 shorter abstract with three findings — agree.

## Also pending
The timing-mechanism test (jobs/timing_mech.jsonl, heuristics before presolve / at the first call / after 10 s, with SCIP
statistics) finishes around 23:10; its result goes into Section 6 with this revision.

## Reviewer's reply and agreed resolution
The reviewer agreed with the proposed revisions, subject to implementation and verification (not acceptance of the
unchanged manuscript), with two refinements, both adopted:
- **Headline:** lead with the full-cohort 19 % (336 instances, no-solution runs at P = 1); keep 25 % as the result
  conditional on at least one configuration finding a solution.
- **Selectors:** "unchanged" holds only for point estimates with predictions held fixed (each cost difference scales by
  n/(n+k), so closed gap and the hindsight best-fixed configuration are invariant). Retraining could change predictions,
  bootstrap intervals depend on the resampled population, and coverage stays the conditional cohort with one FERC case.
  The selector experiment is kept and labelled as a conditional-cohort experiment; no retraining is needed to correct
  the headline headroom.
- **Archive:** traces stay out of git; a versioned release with checksums, the code revision, and the original launch and
  resource records gives access to the original measurements (a DOI is optional). Without it the review would keep a
  reproducibility limitation: re-running tests replication, not whether the published tables follow from the original
  observations.

A second reply asked for four corrections to this note, all made: the point-1 selector paragraph now matches the
resolution; the B2 interval source is `datasets/b2_decomposition.json` (`ci`); the archive decision is stated as Berk's
choice to prepare one, not authorisation to publish; agreement is distinguished from completion, and the principal
comparisons are stated as identified after the fact, not pre-registered (also corrected in the paper's Protocol). The
reviewer will reassess the revised paper once the changes are implemented.
