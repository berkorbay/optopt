# Datasets

All under `data/` in the repository checkout (or `$OPTOPT_DATA`; not in git — on the author's machine `data` is a
symlink to the data disk). Public data only. Job files and traces store paths relative to the repository root.

| family | source | tonight | budget | split |
|---|---|---|---|---|
| MIPLIB 2017 benchmark | miplib.zib.de `benchmark.zip` (240), `miplib2017-v33.solu`, `tag_benchmark.html` | 80 selected by `benchmarks/miplib/select.py` | 60 s | 5-fold by instance |
| ML4CO item placement | ds4dm/ml4co-competition `instances.tar.gz` (Google Drive, 5.6 GB) | train 0–99, valid first 25 | 30 s | official train/valid |
| ML4CO load balancing | same archive (16 GB extracted with item placement) | train 0–99, valid first 25 | 30 s | official train/valid |
| PGLib-UC | github power-grid-lib/pglib-uc, 56 JSON cases | all 56 → MPS with the repo's own `uc_model.py` | 60 s | by base system (ca / ferc / rts_gmlc) |
| BenLOC | — | deferred (#2) | | |

**MIPLIB selection** (seed 20260923): ≤2.5M nonzeros, not infeasible, status easy/hard/open → one instance per
MIPLIB *group* (removes near-duplicate families) → proportional stratified sample by status × size tercile.
Reference objective = the `.solu` value (`=opt=` or `=best=`).

**PGLib-UC** is ~250k rows × ~250k columns per case, ~40 % binary. Three base systems only, so the by-system
split has just three groups — a UC result is a statement about transfer across *systems*, with n=3 groups.

**ML4CO** reference = best value found by any of our runs (no published optima for these; the competition
scored primal integrals against its own reference). Item placement instances are small (0.35 GB for 10k);
load balancing are large (16 GB for 10k).
