# 4 · Choosing versus switching

If configurations matter, maybe the solver should change them **during** the run: start with aggressive heuristics, then
switch to proving; restart when stuck; change the branching rule after the first solution. SCIP allows all of this from a
callback. The paper tested it with six static settings and six mid-solve schedules on 45 MIPLIB instances.

The key step is to **split the headroom into parts**:

![decomposition](figures/04_decomposition.png)

| part (gain over the best single static setting) | primal integral | primal-dual integral |
|---|---|---|
| choosing the right static setting per instance | 11.8 % | 7.6 % |
| switching during the solve, on top | 2.1 % (95 % CI −0.4…7.3) | 2.4 % (−0.3…6.8) |
| run-level part (only visible in hindsight) | 5.0 pts | 10.1 pts |

Most of the value is in **choosing**, not **switching**. The third part is real but tricky: the best setting also depends
on the particular run (random choices inside the solver), which no up-front choice can see and which proved hard to
predict from the early state of a run.

**Hands-on.** `python tutorials/examples/ex04_switching.py` compares default, separation off, a switch at 25 % and a restart
at 25 % on three generated problems.

**Try:** add your own schedule, e.g. `("HEU", "D", "stall20")` — aggressive heuristics until the search stalls for 20 % of the
budget (settings are in `src/optopt/solvers/scip.py`, `SETTINGS`).
