# D-003 Memory budget and priorities beside serving (2026-09-23 08:3x)

**Incident.** 08:21 the host's memory watchdog HARD floor during the B0 grid (10 SCIP runs × up to 6 GB beside both models) shed
the operator's remote sessions and the Ornith-1.5-35B-A3B server (vLLM).

**Berk's priority order.** the operator's sessions, databases, running scheduled jobs, the chat relay and other critical systems
first. the two local agents — the fast chat agent (Hermes Agent with Ornith-1.5-35B-A3B, NVFP4 on vLLM) and the deep-research agent (Hermes Agent with Qwen3.8-27B, UD-IQ3_XXS on llama.cpp) — may be stopped temporarily for experiments (the host's service-hold list + restore); the hosted agent (Hermes Agent with OpenAI GPT-6 Sol) too
if needed.

**Rules for every optopt run from now on.**
1. Every solver run gets a hard per-process memory cap (systemd scope `MemoryMax`, no swap), so a runaway solver
   dies alone — `limits/memory` inside the solver is not enough.
2. Lanes × cap + 16 GB ≤ MemAvailable at start, and the runner stops launching below 20 GB (live, not only at start).
3. If the experiment needs more memory, stop a local agent deliberately (the host's service-hold list + a restore step) — never let
   the host's memory watchdog choose.
4. Timed runs pinned one per X925 core.
