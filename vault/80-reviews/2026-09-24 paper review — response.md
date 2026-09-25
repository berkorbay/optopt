# Response to the paper review of 2026-09-24 (evening)

Review of the paper at 6f0122b by a second reviewer: accept after revision, 7 major and 13 minor points. The full report,
with both positions side by side, is in `transient_work/` (not committed). Outcome:

| point | outcome |
|---|---|
| M1 abstract leads with the control | agreed, changed: abstract, contributions, conclusion quote Table 6 (fixed rule +33 / +41 % at the first call; LLM +34 %, worse than the timed rule on 22 of 30 instances) |
| M2 two sessions, two numbers | agreed in substance; both tables kept (Table 5 is the only evidence for Laya-as-agent, LLM+Laya and GPT-6 Luna); Table 6 first and primary; Table 5 labelled as the first session with the replication numbers |
| M3 "held out" claim false for Table 1 | agreed, changed: single-seed oracle stated; 83 % on the 12-instance five-seed subset; cuOpt not re-run; unpinned cores |
| M4 race numbers | agreed: HiGHS‖cuOpt +30 % (80, one session) headlined; SCIP‖cuOpt +21.5 % on the first 44 in job-file order. Reviewer's "21–26 % depending on session" not adopted (cross-session). On the same 44: same-session 21.5 %, cross-session 24.0 %, solo drift 3.9 % |
| M5 CI with zero next to p 0.005 | agreed: median per-instance gain (+12.7 %) added to text and Table 6; judgement contrast reported as 22/30 worse, mean −10.6 %, median −3.4 % |
| M6 mechanism and scope | disagreed with the reviewer's scope (item placement) and mechanism: the consistent timing effect is on load balancing (15/15, p 6e-5), item placement 9/6 (p 0.25). Reviewer conceded. Mechanism test run (jobs/timing_mech.jsonl: before presolve / first call / after 10 s, SCIP stage and heuristic statistics) |
| M7 "switching" | agreed: "the six schedules we tried"; 12 % (45 instances) vs 20 % (20 selected) |
| minor | resources table completed; overhead caption (56 ms, n 50); orphaned selection_para removed; memory 128 GB / 121 GiB; cuOpt bib note; cuOpt 1e-4 tolerance clause in Sections 3 and 7. Minor 10 (drift example) withdrawn by the reviewer. Repository URL waits for berkorbay/optopt |
