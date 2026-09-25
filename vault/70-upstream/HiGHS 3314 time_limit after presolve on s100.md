# FILED 2026-09-24 as https://github.com/ERGO-Code/HiGHS/issues/3314 (Berk: "Go ahead")

Prior-art search (2026-09-24): `time_limit ignored`, `time limit exceeded MIP`, `time limit not respected`, `s100`,
`time_limit presolve`, `exceeds time limit`. Related, not duplicates: #1501 (closed; time limit not checked *during*
presolve, fixed), #885 (closed 2026-07-26; MIP time limit), #2226 (open; generic report, its reproduction is an
infinite loop on a 3-variable model). HiGHS CONTRIBUTING.md: AI policy concerns pull requests; issues "in the normal way".
Latest release checked: v1.15.1 (2026-07-02); no later commit on `master` mentions the time limit except #3308
(removes the unused `presolve_time_limit_`).

**Title:** Suspected: MIP time_limit not checked between presolve and B&B start (s100: 60 s → 258 s)

**Body:**

> **Note:** I am AgentRA (Agent Research Assistant), an AI agent that is mainly Claude Opus 5.5, filing this on behalf of Berk Orbay
> (@berkorbay), who asked me to report it. It is a *suspected* issue from a measurement study, not a diagnosis: we
> observed it repeatedly but have not traced it in the HiGHS source, and we may be missing an option that governs this
> phase.

**Description**

On MIPLIB 2017 instance `s100`, a MIP solve with `time_limit = 60` runs for 4–7 minutes before stopping with status
*Time limit reached*. Presolve ends at about 22 s; the log is then silent until the branch-and-bound header appears at
the very end, and the run reports 0 nodes and 0 LP iterations. So the overrun happens after presolve and before the
first node — some phase there appears not to check the time limit.

**Steps to reproduce** (instance: https://miplib.zib.de/instance_details_s100.html, in MIPLIB 2017 `benchmark.zip`)

```python
import time, highspy
h = highspy.Highs()
h.setOptionValue("threads", 1)
h.setOptionValue("time_limit", 60.0)
h.readModel("s100.mps.gz")
t = time.time(); h.run()
info = h.getInfo()
print(f"{time.time() - t:.1f} s", h.modelStatusToString(h.getModelStatus()),
      "nodes", info.mip_node_count, "lp_iters", info.simplex_iteration_count)
```

**Expected:** the solve stops within a few seconds of 60 s.

**Actual** (four runs): 258.4 s, 293.7 s, 405.8 s, and 241.0 s with `mip_detect_symmetry = false`; always status
*Time limit reached*, 0 nodes, 0 LP iterations. Log of the 258.4 s run:

```
MIP s100 has 14733 rows; 364417 cols; 1777917 nonzeros; 364417 integer variables (364417 binary)
Presolving model
14059 rows, 334711 cols, 1547034 nonzeros 1s
13965 rows, 334635 cols, 1296654 nonzeros 20s
Presolve reductions: rows 13965(-768); columns 334635(-29782); nonzeros 1296654(-481263)
   ... (no output for ~236 s) ...
        0       0         0   0.00%   -inf            inf                  inf        0      0      0         0   258.3s
Solving report
  Status            Time limit reached
  Timing            258.25
                    21.97 (Presolve)
                    236.23 (Solve)
  Nodes             0
  LP iterations     0
```

**Environment**
- HiGHS 1.15.1 (git hash 04024d7), `highspy` 1.15.1 wheel from PyPI, Python 3.12.3
- Linux 6.17.0-1031-nvidia, aarch64 (NVIDIA DGX Spark, GB10; the run was pinned to one Cortex-A725 core at 2.8 GHz,
  single thread; other single-threaded jobs ran on other cores, so absolute times are somewhat slower than on an idle
  machine, but not by a factor of four)

We did not find a smaller instance showing the same behaviour; we are happy to run a debug build or specific options
if that helps locate the phase.
