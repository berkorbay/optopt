# optopt

**Measuring learned and agent control of MIP solvers.** A Python library and a complete research record for the
paper *"Optimizing the Optimizers: Measuring Learned Control of MIP Solvers on a Single DGX Spark"* (Berk Orbay).

It provides:
- **solver harness** — HiGHS, SCIP and NVIDIA cuOpt wrappers that record the full incumbent and bound trajectory of a
  run (`optopt.solvers`), switch settings or restart mid-solve, and exchange solutions between two solvers;
- **agents in the loop** — an interface that lets an agent change SCIP's settings during a wall-clock budget that
  includes its own thinking time, with an online bandit, a Laya-based agent and LLM agents (`optopt.agents`);
- **metrics and evaluation** — primal and primal-dual integrals, time to target, held-out-seed oracles,
  static-versus-switching decomposition, an exact-arithmetic solution checker (`optopt.analysis`);
- **the job definitions** of the over 8,000 runs behind the paper (`jobs/`), the derived tables (`datasets/`), the paper source
  (`paper/`), a research vault with the journal, decisions and failures (`vault/`), and tutorials (`tutorials/`).

For AI agents reviewing or extending the work: start at [`AGENTS.md`](AGENTS.md) — every claim with its numbers,
evidence files and caveats.

## Install
```bash
git clone https://github.com/berkorbay/optopt && cd optopt
uv venv && source .venv/bin/activate
uv pip install -e ".[dev,plots]"          # solvers on the CPU, analysis, tests
uv pip install -e ".[gpu]" --extra-index-url https://pypi.nvidia.com   # + NVIDIA cuOpt (CUDA 13 GPU)
uv pip install -e ".[laya]"               # + Laya (torch, transformers)
```
Versions are pinned to the ones used for the paper (Python 3.12, HiGHS 1.15.1, PySCIPOpt 6.2.1 / SCIP 10.0,
cuOpt 26.08).

## Reproducibility
The repository holds the code, the exact experiment definitions and the derived tables. The original per-run
trajectories (`traces/raw/`, with the pair runs' launch records), stored solutions (`traces/sol/`) and resource records
are published separately as a versioned release archive with SHA-256 checksums and the code revision they belong to:
[`traces-v1`](https://github.com/berkorbay/optopt/releases/tag/traces-v1) (`optopt-traces-v1.tar.gz`, unpack into the workspace root).
Two uses differ:

- **Re-analysis of the published study:** unpack the archive into the workspace, then run `optopt reproduce`. This
  checks that every published table follows from the original measurements.
- **A new replication:** re-run the jobs (step 3). This tests whether the findings hold on your machine; wall-clock
  results will differ (see below).

**1. Re-derive every table from the runs.**
```bash
optopt reproduce
```
Runs the whole deterministic analysis chain on the trajectories in `traces/` and compares every file in `datasets/`
and `paper/generated/` with its committed version (text byte for byte, parquet by content). It lists any file that
changed and exits with code 1 if one did or if any analysis step failed; without trajectories it exits with code 2
and says what to do. On the original traces
this reproduces every committed table exactly; on re-run traces, expect the differences described below. Not re-run: the Laya fine-tuning steps
(GPU, not bit-reproducible); their stored predictions (`datasets/laya_preds.json`, `datasets/laya_diag.json`) are
inputs. `pytest -q` checks the metrics, including property-based tests.

**2. Check the solutions — needs the instances and the runs' stored solutions.**
```bash
optopt fetch miplib                 # public instance sets into data/ (see `optopt fetch` for ML4CO and PGLib-UC)
optopt check traces/sol/<set>       # every stored incumbent, re-checked independently -> datasets/solcheck_<set>.csv
```
Every run stores the incumbent its result relies on in `traces/sol/`. The checker re-reads the original model with a
different solver library than the one that produced the solution and checks bounds, integrality and the objective in
exact rational arithmetic, and every row in floating point with an exact re-check of any row near the tolerance
(1e-6, MIPLIB-checker style). So no reported objective rests on a solver's own feasibility check.

**3. Re-run the experiments — needs the instances and, for cuOpt, a CUDA 13 GPU.** This is the step that
produces `traces/`.
```bash
optopt pool jobs/b2_seeds.jsonl --pin 5,6,7,8 --mem-cap-gb 9     # any job file under jobs/
optopt pair jobs/miplib.jsonl --arms race,g2c --budget 60         # SCIP || cuOpt with solution exchange
```
The job files in `jobs/` are the exact experiment definitions (instances, strategies, seeds, budgets); the strategies
and agent arms are defined in `optopt.portfolio.strategies`; seeds are fixed throughout; the committed `traces/resources/` records
for every run set the cores, memory caps, thread counts and what else was running.

**What a re-run will and will not reproduce.** Results are wall-clock measurements on one NVIDIA DGX Spark (GB10, one
run per Cortex-X925 core, hard memory caps). On other hardware the conclusions should hold but the exact numbers
will not: node throughput, and therefore every primal integral, depends on the core, the memory bandwidth and what
runs beside it. The LLM-agent arms additionally need the same models: Ornith-1.5-35B-A3B served by vLLM on
127.0.0.1:8094, and OpenAI GPT-6 Luna, which the paper reached through a ChatGPT Plus subscription via Hermes Agent's
Codex client (`optopt.agents.gpt_bridge`); a hosted model can change behind the same name.

**Environment.** Python 3.12; `pyproject.toml` pins the versions used for the paper (HiGHS 1.15.1, PySCIPOpt 6.2.1 /
SCIP 10.0, cuOpt 26.08, LightGBM 4.7.0, torch 2.14, transformers 5.17, numpy 2.4.6, pandas 3.0.3, scikit-learn 1.9.1).
Laya is `convaiinnovations/laya` (421.3M parameters) at revision `1c5edc17a7acd8701df6fc341c0d179f1c62c982`, placed
in `data/models/laya` (`hf download convaiinnovations/laya --revision 1c5edc1 --local-dir data/models/laya`).

## Run experiments
optopt works in a **workspace**: the current directory (or `$OPTOPT_HOME`) holding `jobs/`, `data/`, `traces/`,
`datasets/`. Paths in job files and traces are relative to it, so a clone runs anywhere. Instances go in `data/`
(or `$OPTOPT_DATA`); see [`vault/10-design/Datasets.md`](vault/10-design/Datasets.md) for the public sources.
```bash
optopt run data/miplib/inst/air05.mps.gz S0 --budget 60 --out traces/raw/demo/air05__S0__s0.json
optopt pool jobs/miplib.jsonl --pin 5,6,7,8 --mem-cap-gb 8       # pinned, memory-capped pool
optopt pair jobs/miplib.jsonl --arms race,g2c --budget 60        # SCIP || cuOpt, with solution exchange
optopt analyse b3                                                # any analysis module
```
As a library:
```python
from optopt.solvers import scip
from optopt.agents.bandit import BanditAgent
from optopt.analysis.metrics import primal_integral

trace = scip.run("data/miplib/inst/air05.mps.gz", "S0", {}, budget=60, seed=0, agent=BanditAgent(interval=5))
print(primal_integral(trace.__dict__, ref=26374, T=60))
```

## Layout
| path | what |
|---|---|
| `src/optopt/solvers` | solver wrappers, solution exchange (`xchg`), evolutionary partner (`ea`) |
| `src/optopt/agents` | agent interface, bandit, rules, Laya agent and service, LLM agents |
| `src/optopt/experiments` | runners (`run_one`, `pool`, `xchg_pair`), job builders, selection experiments |
| `src/optopt/analysis` | metrics, table builders, solution checker, `reproduce` |
| `src/optopt/references` | MIPLIB 2017 reference values and the instance selection |
| `jobs/`, `traces/`, `datasets/` | job files; resource records (trajectories and solutions are written here by runs, not committed); derived tables |
| `paper/`, `vault/`, `tutorials/` | paper source, research vault (Obsidian), tutorials with examples |

## Where to go next
The research agenda that follows from these results — confirmation cohorts, diagnostic probes, longer budgets,
language-model agents with a thinking-time budget, CPU/GPU portfolios and cooperation, the GPU inside MILP — is in
[`vault/10-design/Future research.md`](vault/10-design/Future%20research.md).

## Credits
Author: Berk Orbay (berk.orbay@tideseed.com). Paper and original measurements: [doi:10.5281/zenodo.22947442](https://doi.org/10.5281/zenodo.22947442). Website and tutorials: https://berkorbay.github.io/optopt/. The experiments were designed with and executed by **AgentRA** (Agent Research Assistant) — **AgentRA is mainly Claude Opus 5.5** — under the author's direction; every number comes from the
code and job definitions here and can be re-derived with `optopt reproduce` after re-running the jobs. The study was
reviewed, with suggestions for improvement, by Claude Fable 5.1 (Anthropic) and OpenAI GPT-6 Astra (ChatGPT); the reviews' findings and the responses are in `vault/80-reviews/`.

## License
Code, data (traces, derived tables), vault and tutorials: [MIT](LICENSE). The paper: [CC BY 4.0](paper/LICENSE), as on
arXiv. Both allow any use, including commercial, with attribution. Third-party files keep their own terms (see LICENSE).

