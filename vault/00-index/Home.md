# optopt vault — home

Project: learned control of MIP solvers on DGX Spark ("MIP-Laya"). Repo root README has the layout.

| track | question | status |
|---|---|---|
| **Main experiment — agent in the loop, end to end** | hand an agent problem + solver + budget + fixed slice; free settings; measure end to end | designed → [[D-004 Main experiment — agent in the loop, end to end]] |
| **B — in-solver dynamic control** (primary) | can Laya improve one solver by changing its search strategy / parameters mid-solve? | planned → [[Track B — in-solver dynamic control]] |
| A — cross-solver strategy selection | can a policy pick HiGHS/SCIP/cuOpt per instance? | night 1 done, frozen at tag `track-a-night1` → [[Milestone 1 — static strategy selection]] |

| section | contents |
|---|---|
| [[Research question and spec]] | the brief as given (2026-09-23), condensed |
| `10-design/` | [[Datasets]], [[Strategy portfolio]], [[Trace format and metrics]], [[Policies and evaluation]] |
| `30-results/` | **[[Experiment index]] — every experiment with its outcome, including failures**; one note per experiment |
| `60-incidents/` | [[Mistakes and incidents]] |
| `20-journal/` | dated research journal, append-only, timestamps in CEST |
| `30-results/` | result notes per phase, each with the command that produced it |
| `40-literature/` | [[Related work]], [[Laya]], [[Prior art]] (159-work sweep, novelty verdict), [[Paywalled research]] (the only home for paywalled works) |
| `50-decisions/` | decision records (scope cuts, metric choices) |
| `90-checkpoints/` | session checkpoints — start at the newest |

Tracking: GitHub issues on `berkorbay/optopt`.

Rules carried from the host (dgx-spark): public data only; no uncapped compiles; production serving is
restored after every window; paper is final as a technical report (Berk, 2026-09-24); not yet submitted.

> **Code paths in notes written before 2026-09-24** refer to the layout before the code became the Python package
> `optopt`: `solvers/`, `agents/`, `analysis/`, `experiments/`, … are now `src/optopt/<same>/`; `experiments/jobs/` is
> `jobs/`; `experiments/00_baseline.py`, `01_selection.py`, `02_laya.py` are `pool.py`, `selection.py`, `laya_select.py`;
> scripts run as `optopt <command>` or `python -m optopt.<module>`. Absolute paths in older notes were rewritten to
> workspace-relative ones (`data/...`).

