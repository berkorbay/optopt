"""Phase 0/1 pool runner: every (instance, strategy, seed) of a job file, each in its own subprocess.

CPU strategies (HiGHS, SCIP; one thread each) run on `--cpu-workers` lanes; cuOpt runs on `--gpu-lanes` lanes.
Resumable: a trace that already exists is skipped. A run that exceeds budget*1.5+60 s is killed and recorded as
`error: killed`. Launches wait while MemAvailable is below `--min-avail-gb`.

Job file: JSONL with {"set", "instance" (path), "strategies": [...], "seeds": [...], "budget"}.
Writes traces/raw/<set>/<stem>__<strategy>__s<seed>.json and, at the end, traces/raw/<set>/DONE.
"""
from __future__ import annotations

import argparse
import json
import os
import queue
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

from optopt.paths import WORK as ROOT  # the workspace (cwd or $OPTOPT_HOME)
from optopt.experiments.identity import config_hash  # noqa: E402
from optopt.portfolio.strategies import STRATEGIES  # noqa: E402


def mem_avail_gb() -> float:
    for line in open("/proc/meminfo"):
        if line.startswith("MemAvailable"):
            return int(line.split()[1]) / 1048576
    return 0.0


def stem(p: str) -> str:
    n = os.path.basename(p)
    for ext in (".mps.gz", ".mps", ".lp.gz", ".lp"):
        if n.endswith(ext):
            return n[: -len(ext)]
    return n


COUNTS = {"queued": 0, "reused_valid": 0, "reused_legacy": 0, "stale": 0}
STALE: list = []
RESULTS: list = []


def worker(q: queue.Queue, args, log, lock, cpu=None):
    """cpu: pin every run of this lane to one core (GB10 has 10 fast X925 + 10 slower A725 cores; unpinned runs get a
    random effective budget — measured ~2x node throughput difference on SCIP)."""
    while True:
        try:
            job = q.get_nowait()
        except queue.Empty:
            return
        inst, strat, seed, budget, out = job
        while mem_avail_gb() < args.min_avail_gb:  # checked before EVERY launch, not only at start
            time.sleep(5)
        t = time.time()
        cmd = [sys.executable, "-m", "optopt.experiments.run_one", inst, strat, "--budget", str(budget),
               "--seed", str(seed), "--out", str(out)]
        if cpu is not None:
            cmd = ["taskset", "-c", str(cpu)] + cmd
        if args.mem_cap_gb > 0:  # D-003: a runaway solver dies alone instead of pushing the host's memory watchdog to shed services
            cmd = ["systemd-run", "--user", "--scope", "--quiet", "-p", f"MemoryMax={args.mem_cap_gb}G",
                   "-p", "MemorySwapMax=0"] + cmd
        env = dict(os.environ, OPTOPT_HOME=str(ROOT), OMP_NUM_THREADS="1",
                   OPTOPT_SCIP_MEM_MB=str(int(max(500, args.mem_cap_gb * 1024 - 1024))))  # solver limit below the hard cap
        err_tail = ""
        try:
            r = subprocess.run(cmd, timeout=budget * 1.5 + 60, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                               env=env, text=True)
            err_tail = (r.stderr or "")[-2000:]
            status = "ok" if (r.returncode == 0 and out.exists()) else (f"rc={r.returncode}" if r.returncode else "no-output")
        except subprocess.TimeoutExpired:
            status = "killed"
        if not out.exists():  # a process that died without output is a scored failure, with its exit code and stderr
            out.write_text(json.dumps({"instance": inst, "strategy": strat, "seed": seed, "budget": budget,
                                       "solver": STRATEGIES[strat]["solver"], "error": status,
                                       "stderr_tail": err_tail, "events": []}))
        elif status != "ok" and err_tail:
            out.with_suffix(".stderr.txt").write_text(err_tail)
        with lock:
            RESULTS.append(status)
        with lock:
            log.write(f"{time.strftime('%H:%M:%S')} {status} {strat} s{seed} {stem(inst)} {time.time()-t:.1f}s\n")
            log.flush()


def _serving_units():
    """Running user and system services that look like model servers (vLLM, llama.cpp, Ollama, SGLang, TGI), plus any
    listed in $OPTOPT_SERVING_UNITS; recorded in every resource record so contention is on file (review 2026-09-24)."""
    import re
    pat = re.compile(r"vllm|llama|ollama|sglang|tgi|text-generation|ornith|qwen", re.I)
    out = {}
    for scope in (["systemctl", "--user"], ["systemctl"]):
        try:
            r = subprocess.run(scope + ["list-units", "--type=service", "--state=running", "--no-legend", "--plain"],
                               capture_output=True, text=True, timeout=10)
        except (OSError, subprocess.TimeoutExpired):
            continue
        for line in r.stdout.splitlines():
            unit = line.split()[0] if line.split() else ""
            if pat.search(unit):
                out[unit] = "active"
    for u in os.environ.get("OPTOPT_SERVING_UNITS", "").split(","):
        if u.strip() and u.strip() not in out:
            r = subprocess.run(["systemctl", "--user", "is-active", u.strip()], capture_output=True, text=True)
            out[u.strip()] = r.stdout.strip()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("jobs")
    ap.add_argument("--cpu-workers", type=int, default=12)
    ap.add_argument("--gpu-lanes", type=int, default=2)
    ap.add_argument("--min-avail-gb", type=float, default=20)
    ap.add_argument("--rerun-stale", action="store_true",
                    help="re-run (and keep a renamed copy of) existing traces whose configuration hash differs")
    ap.add_argument("--mem-cap-gb", type=float, default=3.0, help="hard per-run cap (systemd scope MemoryMax, no swap)")
    ap.add_argument("--only", choices=["cpu", "gpu", "all"], default="all")
    ap.add_argument("--pin", default="", help="comma list of cores for CPU lanes, one lane per core "
                    "(GB10 fast cores: 5,6,7,8,9,15,16,17,18,19); overrides --cpu-workers")
    args = ap.parse_args()

    cpu_q, gpu_q = queue.Queue(), queue.Queue()
    sets = set()
    for line in open(args.jobs):
        j = json.loads(line)
        d = ROOT / "traces/raw" / j["set"]
        d.mkdir(parents=True, exist_ok=True)
        sets.add(j["set"])
        for s in j["strategies"]:
            for seed in j.get("seeds", [0]):
                out = d / f"{stem(j['instance'])}__{s}__s{seed}.json"
                want = config_hash(j["instance"], s, j["budget"], seed)
                if out.exists():
                    try:
                        have = (json.loads(out.read_text()).get("extra") or {}).get("config_hash")
                    except json.JSONDecodeError:
                        have = "corrupt"
                    if have is None:
                        COUNTS["reused_legacy"] += 1  # recorded before run identity existed (2026-09-24)
                        continue
                    if have == want:
                        COUNTS["reused_valid"] += 1
                        continue
                    COUNTS["stale"] += 1
                    STALE.append(out.name)
                    if not args.rerun_stale:
                        continue
                    out.rename(out.with_suffix(f".stale-{time.strftime('%Y%m%d%H%M%S')}.json"))
                COUNTS["queued"] += 1
                gpu = STRATEGIES[s]["solver"] == "cuopt"
                (gpu_q if gpu else cpu_q).put((j["instance"], s, seed, j["budget"], out))
    print(f"queued cpu={cpu_q.qsize()} gpu={gpu_q.qsize()}", flush=True)
    lanes = len([c for c in args.pin.split(",") if c.strip()]) or args.cpu_workers
    if args.only != "gpu" and lanes * args.mem_cap_gb + 16 > mem_avail_gb():
        sys.exit(f"refusing: {lanes} lanes x {args.mem_cap_gb} GB + 16 GB margin > MemAvailable {mem_avail_gb():.0f} GB (D-003)")
    log = open(ROOT / "traces" / f"runner-{Path(args.jobs).stem}-{args.only}.log", "a")
    # resource record for the paper: what this run set was allocated and what else was running
    def _sh(c):
        try:
            return subprocess.run(c, shell=True, capture_output=True, text=True, timeout=20).stdout.strip()
        except Exception as e:  # noqa: BLE001
            return f"error: {e}"
    cores = [int(c) for c in args.pin.split(",") if c.strip()]
    rec = dict(started=time.strftime("%Y-%m-%dT%H:%M:%S%z"), jobs=args.jobs, only=args.only,
               cpu_lanes=(len(cores) or args.cpu_workers) if args.only != "gpu" else 0,
               gpu_lanes=args.gpu_lanes if args.only != "cpu" else 0,
               pinned_cores=cores or None,
               pinned_core_models=sorted(set(_sh(f"lscpu -e=CPU,MODELNAME | awk '$1=={c}{{print $2}}'") for c in cores)) or None,
               mem_cap_gb_per_run=args.mem_cap_gb or None, scip_mem_limit_mb=int(max(500, args.mem_cap_gb * 1024 - 1024)),
               min_avail_gate_gb=args.min_avail_gb, mem_available_gb_at_start=round(mem_avail_gb(), 1),
               threads_per_run={"highs": 1, "scip": 1, "cuopt_cpu": 3},
               serving_units=_serving_units(),  # model servers running beside the experiment (recorded unconditionally)
               gpu_processes=re.sub(r"\S*/", "", _sh("nvidia-smi --query-compute-apps=process_name,used_memory --format=csv,noheader")))  # names only, no paths
    for s_ in sets:
        rd = ROOT / "traces/resources" / s_  # kept OUT of traces/raw so trace loaders never see it
        rd.mkdir(parents=True, exist_ok=True)
        (rd / f"RESOURCES-{Path(args.jobs).stem}-{args.only}-{time.strftime('%H%M%S')}.json").write_text(json.dumps(rec, indent=1))
    lock = threading.Lock()
    threads = []
    if args.only in ("cpu", "all"):
        cores = [int(c) for c in args.pin.split(",") if c.strip()]
        if cores:
            threads += [threading.Thread(target=worker, args=(cpu_q, args, log, lock, c)) for c in cores]
        else:
            threads += [threading.Thread(target=worker, args=(cpu_q, args, log, lock)) for _ in range(args.cpu_workers)]
    if args.only in ("gpu", "all"):
        threads += [threading.Thread(target=worker, args=(gpu_q, args, log, lock)) for _ in range(args.gpu_lanes)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    from collections import Counter
    rec = dict(COUNTS, finished=dict(Counter(RESULTS)), stale_examples=STALE[:20], jobs=Path(args.jobs).name,
               only=args.only, ended=time.strftime("%Y-%m-%dT%H:%M:%S%z"))
    rec["failed"] = sum(v for k, v in rec["finished"].items() if k != "ok")
    for s in sets:
        (ROOT / "traces/raw" / s / f"DONE-{Path(args.jobs).stem}-{args.only}").write_text(json.dumps(rec, indent=1))
    print(f"done: {json.dumps(rec)}", flush=True)
    if STALE and not args.rerun_stale:
        print(f"WARNING: {len(STALE)} existing traces have a different configuration and were NOT re-run "
              f"(use --rerun-stale)", flush=True)


if __name__ == "__main__":
    main()
