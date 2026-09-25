# Compute resources per experiment (for the paper)

Machine: NVIDIA DGX Spark — GB10 (10 × Cortex-X925 @ 3.9 GHz = cores 5–9, 15–19; 10 × Cortex-A725 @ 2.8 GHz =
cores 0–4, 10–14), Blackwell GPU, 121 GiB usable unified memory (CPU and GPU share it), Ubuntu 24.04, kernel 6.17,
driver 580.173.02, CUDA 13.0. Measured: SCIP explores ~2× more nodes/s on an X925 than an A725 (tr12-30, 20 s:
4,686 vs 2,413 nodes). From 2026-09-23 08:47 every run set also writes `traces/raw/<set>/RESOURCES-*.json`.

| experiment | when (CEST, 09-23) | CPU lanes | pinning | GPU | memory per run | co-running | budget |
|---|---|---|---|---|---|---|---|
| Track A grid (MIPLIB, ML4CO, UC) | 00:50–05:01 | 12 × 1 thread (HiGHS/SCIP) | none (X925+A725 mixed) | 2 cuOpt lanes × (GPU + 3 CPU threads) | no hard cap; SCIP `limits/memory` 6000 MB | both LLM servers **stopped**; 02:10–02:21 an analysis job added CPU load (172 runs re-run) | 30/60 s |
| Track A 300 s screening | 02:29–03:3x | 12 × 1 thread | none | cuOpt lanes busy with ML4CO | as above | LLM servers stopped | 300 s |
| Variance subset | 02:15–02:29, re-run 03:28–03:39 | 12 × 1 thread | none | — | as above | LLM servers stopped | 60 s |
| Laya fine-tune / zero-shot | 05:01–05:28 | — | — | GPU exclusive (bf16, peak 15.4 GB) | — | LLM servers stopped, no solver runs | — |
| GPU contention A–D | 05:28–06:01 | cuOpt 3 CPU threads | none | 1 cuOpt lane + 0/1 Laya process | — | LLM servers stopped, nothing else | 30 s |
| Track B · B0 | 07:52–08:36 | 10 × 1 thread (SCIP) | none | idle (LLMs resident) | no hard cap; SCIP 6000 MB | **both LLM servers up** (~72 GB resident); the host's memory watchdog shed at 08:21 (ornith down 08:21–08:40) | 30 s |
| Track B · B1 | 08:47–09:05 | 10 × 1 thread (SCIP) | **one run per X925 core** (5–9, 15–19) | idle | **hard cap 8 GiB** (systemd scope, no swap); SCIP 7168 MB | both LLM servers **stopped** (Berk: idle agents may be stopped), restored 09:05–09:09 | 120 s |

Consequences recorded in the paper: Track A and B0 timings mix core types (≈2× effective-budget spread, random, not
arm-dependent); B0 ran beside resident LLM servers (memory-bandwidth contention); B1 is the first clean setting.
