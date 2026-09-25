# U1 — upstream bug candidates (18:30–)

Nothing is posted without Berk's per-post yes (host rule).
- **HiGHS 1.15.1 (latest), MIPLIB `s100`, threads = 1, time_limit = 60 s → ran 405.8 s, status "Time limit reached". REPRODUCED.**
  Prior art: #885 (closed 2026-07-26) — ours may be a regression or a different path. Log run in progress to locate the phase.
- cuOpt C1 on `sorrell3` "hang" (killed at 150 s in Track A): **not reproduced** alone on the GPU (61.0 s) — likely two cuOpt
  processes sharing the GPU. Dropped.
- cuOpt `uccase12` overrun: 66.2 s for 60 s alone (21 s under contention) — covered by open #1135 / #1069. Not filed.
- cuOpt `dano3_3` objective 0.0: status code 5 = MILP **TimeLimit without solution** (not an error) — the placeholder is expected.
  The one real oddity (callback reported an incumbent at 60.33 s, final status "no solution") did not reproduce. Dropped.
  **Our wrapper mislabelled cuOpt statuses** (8 as TimeLimit, 5 unlabelled) — labels only; fixed; no metric affected.
