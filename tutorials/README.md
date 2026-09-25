# Tutorials — learned control of MIP solvers, from zero

Six short chapters that explain the ideas behind the paper *"Optimizing the Optimizers"*, each with a figure made from
this repository's own runs and a hands-on example you can run in about a minute. No data downloads are needed for
the examples (they generate their own problems); chapter 3 reads the paper's recorded results.

| # | chapter | you will learn | hands-on |
|---|---|---|---|
| 1 | [What a MIP solver does while it runs](01-mip-solver-in-motion.md) | incumbents, bounds, gaps, branch-and-bound | `examples/ex01_first_mip.py` |
| 2 | [Measuring "good solutions early"](02-primal-integral.md) | primal integral, primal-dual integral, time to target | `examples/ex02_primal_integral.py` |
| 3 | [Portfolios, oracles and headroom](03-portfolios-and-oracles.md) | single best strategy, per-instance oracle, noise, closed gap | `examples/ex03_headroom.py` |
| 4 | [Choosing versus switching](04-choosing-vs-switching.md) | static settings, mid-solve schedules, restarts, run-level variation | `examples/ex04_switching.py` |
| 5 | [Agents in the loop](05-agents-in-the-loop.md) | the agent interface, bandits, charging decisions to the clock | `examples/ex05_my_agent.py` |
| 6 | [Parallel copies and learned selectors](06-parallel-and-learned.md) | portfolios without prediction, LightGBM vs a decision model | reading the paper's tables |

**Further reading:** [resources.md](resources.md) — seminal books and papers, marked open or paywalled.

## Setup
```bash
cd optopt
uv venv .venv && source .venv/bin/activate
uv pip install highspy pyscipopt numpy scipy pandas pyarrow matplotlib
python tutorials/examples/ex01_first_mip.py
```
Figures are regenerated with `python tutorials/make_figures.py`.
