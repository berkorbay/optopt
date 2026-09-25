# 5 · Agents in the loop

The end-to-end question: hand an **agent** a problem, a solver, a wall-clock budget and a fixed slice of the machine; it
starts from the defaults and may change settings or restart at any time. Everything it does — including its own
thinking time — counts against the budget.

In this repository the agent is called from inside SCIP every few seconds (`src/optopt/agents/base.py`) with the current state
(incumbent, bound, gap, time since the last new solution, node rate, current setting) and returns nothing, a setting, or a
restart. SCIP's time limit is wall clock, so slow agents pay for their slowness.

A simple and strong baseline is an **online bandit** (UCB1; Auer, Cesa-Bianchi & Fischer 2002): each interval it tries a
setting, rewards the gap progress it saw, and gradually prefers what works — no training data needed.

![bandit](figures/05_bandit.png)

On unseen ML4CO item-placement problems the bandit improved the primal integral by about 30 % over SCIP's defaults. But a
*fixed* "aggressive heuristics" setting from the start was just as good (and better early on): the bandit was mostly
**discovering the right static setting online**, paying for the exploration.

| item placement, P(120) | value |
|---|---|
| SCIP default | 0.350 |
| bandit agent (5 s decisions) | 0.244 |
| fixed aggressive heuristics | 0.238 |

**Hands-on.** `python tutorials/examples/ex05_my_agent.py` defines a 10-line "stall agent" and runs it next to the bandit.

**Try:** write an agent that looks at `state["node_rate"]` and switches off cuts when nodes are slow.
