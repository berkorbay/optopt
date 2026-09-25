# DRAFT — not posted. Needs Berk's explicit yes (per-post rule). Target: github.com/ERGO-Code/HiGHS/issues

**Title:** MIP: `time_limit` not honoured before the first LP iteration on MIPLIB `s100` (60 s limit → 241–406 s)

**Body:**
Drafted by AgentRA (Agent Research Assistant; mainly Claude Opus 5.5), an AI agent, on behalf of Berk Orbay, who reviewed it.

With HiGHS 1.15.1 (git hash 04024d7, `highspy` wheel, the latest release) on MIPLIB 2017 instance `s100`
(14,733 rows, 364,417 binary columns, 1.78 M nonzeros; https://miplib.zib.de/instance_details_s100.html), a MIP solve
with `time_limit = 60` runs for 4–7 minutes before stopping with status "Time limit reached". The solver log shows
presolve finishing at ~22 s and then no output until the end; the final summary reports **0 nodes and 0 LP
iterations** for the whole run:

```
Timing            293.53
                   22.38 (Presolve)
                  271.09 (Solve)
Nodes             0
LP iterations     0
```

Reproduction (single thread, Linux aarch64, NVIDIA DGX Spark / Cortex-A725 core):
```python
import highspy, time
h = highspy.Highs()
h.setOptionValue("threads", 1)
h.setOptionValue("time_limit", 60.0)
h.readModel("s100.mps.gz")
t = time.time(); h.run(); print(time.time() - t, h.modelStatusToString(h.getModelStatus()))
# -> 293.7 s  Time limit reached   (405.8 s in another run; 241.0 s with mip_detect_symmetry = False)
```
Observations: happens with and without `mip_detect_symmetry`; the overrun is between the end of presolve and the first
LP iteration of the root relaxation, so a phase there does not appear to check the time limit. #885 reported similar
symptoms and was closed in July 2026; this may be a remaining path.

Happy to run further diagnostics (e.g. a debug build or specific options) if useful.

---
Prior-art search (2026-09-23): `time limit not respected` → #885 (closed); `time_limit exceeded MIP`, `time limit ignored` → nothing matching.
Evidence: `traces/repro/highs_s100.log`, `traces/repro/highs_s100_nosym.log`, `traces/repro/upstream_repro.json`.
