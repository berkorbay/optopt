"""SCIP (one Cortex-X925 core) and cuOpt (GPU + Cortex-A725 cores) run side by side on one instance, with or without
exchanging incumbents. Arms (all start from default settings, same wall-clock budget, launched together):
  race  - no exchange: the portfolio result, now measured live instead of computed from separate runs
  g2c   - cuOpt -> SCIP only (cuOpt keeps its presolve; registering a set-solution callback would disable it)
  both  - two-way exchange (cuOpt's presolve is off because it must accept SCIP's solutions)
One instance at a time (the GPU is not shared); arms interleaved per instance, so a partial run is still paired.
Writes traces/raw/xchg_<arm>/<inst>__{scip,cuopt}__s<seed>.json and a launch record in traces/raw/xchg_launch.jsonl.

  python experiments/xchg_pair.py jobs/miplib.jsonl --budget 60 --deadline 06:10
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from optopt.paths import WORK as ROOT  # the workspace (cwd or $OPTOPT_HOME)
from optopt.analysis.build_runs import stem  # noqa: E402

# arm -> (scip side exchange mode, partner kind, partner exchange mode / EA rho)
ARMS = {"race": ("", "cuopt", ""), "g2c": ("recv", "cuopt", "send"), "both": ("send,recv", "cuopt", "send,recv"),
        "solo": ("", None, ""),                    # SCIP alone, one core
        "scip2": ("", "scip", ""),                 # equal-compute control: a second SCIP (other seed) on a slow core
        "ea0": ("send,recv", "ea", 0.0),           # SCIP + evolutionary partner, feasible population only
        "ea20": ("send,recv", "ea", 0.2),          # ... up to 20 % super-optimal infeasible individuals
        "hrace": ("", "cuopt", ""),                # HiGHS (heavy heuristics, H1) || cuOpt, no exchange (review 2026-09-24)
        "hsolo": ("", None, "")}                   # HiGHS H1 alone, same core and session
CPU_STRATEGY = {"hrace": "H1", "hsolo": "H1"}                     # CPU-side strategy per arm (default: SCIP default, S0)


def mem_avail_gb():
    for line in open("/proc/meminfo"):
        if line.startswith("MemAvailable"):
            return int(line.split()[1]) / 1048576


def cmd(inst, strat, budget, seed, out, xdir, mode, cpus, cap_gb, scip_mb=None):
    c = [sys.executable, "-m", "optopt.experiments.run_one", inst, strat, "--budget", str(budget), "--seed", str(seed),
         "--out", str(out)]
    if mode:
        c += ["--xchg-dir", xdir, "--xchg", mode]
    return ["systemd-run", "--user", "--scope", "--quiet", "-p", f"MemoryMax={cap_gb}G", "-p", "MemorySwapMax=0",
            "taskset", "-c", cpus] + c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("jobs")
    ap.add_argument("--budget", type=float, default=60)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--arms", default="race,g2c,both")
    ap.add_argument("--scip-core", default="19")
    ap.add_argument("--cuopt-cores", default="0-4")
    ap.add_argument("--partner-core", default="", help="core for EA / second-SCIP partners (default: first cuopt core)")
    ap.add_argument("--shard", default="0/1", help="k/N: run every N-th instance starting at k")
    ap.add_argument("--scip-cap", type=float, default=9)
    ap.add_argument("--partner-cap", type=float, default=9, help="GB for EA / second-SCIP partners")
    ap.add_argument("--prefix", default="xchg", help="trace set prefix (use xtest for functional tests)")
    ap.add_argument("--deadline", default="", help="HH:MM local time; no new instance is started after it")
    a = ap.parse_args()
    arms = a.arms.split(",")
    insts = [json.loads(line)["instance"] for line in open(a.jobs)]
    k, n = map(int, a.shard.split("/"))
    insts = insts[k::n]
    launch_log = open(ROOT / "traces/raw/xchg_launch.jsonl", "a")
    log = open(ROOT / f"traces/{a.prefix}_pair.log", "a")
    for inst in insts:
        if a.deadline and time.strftime("%H:%M") >= a.deadline and time.strftime("%H:%M") < "12:00":
            log.write(f"{time.strftime('%T')} deadline reached, stop\n")
            break
        for arm in arms:
            d = ROOT / "traces/raw" / f"{a.prefix}_{arm}"
            d.mkdir(parents=True, exist_ok=True)
            cpu = CPU_STRATEGY.get(arm, "S0")
            o_s = d / f"{stem(inst)}__{'scip' if cpu == 'S0' else 'cpu'}__s{a.seed}.json"
            o_c = d / f"{stem(inst)}__partner__s{a.seed}.json"
            if o_s.exists() and (o_c.exists() or ARMS[arm][1] is None):
                continue
            while mem_avail_gb() < 20:
                time.sleep(5)
            ms, kind, mc = ARMS[arm]
            pcore = a.partner_core or a.cuopt_cores.split("-")[0].split(",")[0]
            with tempfile.TemporaryDirectory(prefix="xchg_") as xd:
                env = dict(os.environ, OPTOPT_HOME=str(ROOT), OMP_NUM_THREADS="1", OPTOPT_SCIP_MEM_MB=str(int(a.scip_cap * 1024 - 1024)))
                penv = dict(env, OPTOPT_SCIP_MEM_MB=str(int(max(1, a.partner_cap - 1) * 1024)))
                t0 = time.time()
                procs = [("scip", subprocess.Popen(cmd(inst, cpu, a.budget, a.seed, o_s, xd, ms, a.scip_core, a.scip_cap),
                                                   env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))]
                if kind == "cuopt":
                    c = cmd(inst, "C0", a.budget, a.seed, o_c, xd, mc, a.cuopt_cores, 24)
                elif kind == "scip":
                    c = cmd(inst, "S0", a.budget, a.seed + 1, o_c, xd, "", pcore, a.partner_cap)
                elif kind == "ea":
                    c = ["systemd-run", "--user", "--scope", "--quiet", "-p", f"MemoryMax={a.partner_cap}G", "-p", "MemorySwapMax=0",
                         "taskset", "-c", pcore, sys.executable, "-m", "optopt.experiments.run_ea", inst,
                         "--budget", str(a.budget), "--seed", str(a.seed), "--rho", str(mc), "--xchg-dir", xd,
                         "--out", str(o_c)]
                if kind:
                    procs.append((kind, subprocess.Popen(c, env=penv if kind != "cuopt" else env, stdout=subprocess.DEVNULL,
                                                         stderr=subprocess.DEVNULL)))
                st = {}
                for name, p in procs:
                    try:
                        rc = p.wait(timeout=max(1, a.budget * 1.5 + 60 - (time.time() - t0)))
                        st[name] = "ok" if rc == 0 else f"rc={rc}"  # a native crash leaves no trace file
                    except subprocess.TimeoutExpired:
                        p.kill()
                        st[name] = "killed"
                launch_log.write(json.dumps({"set": a.prefix, "instance": stem(inst), "arm": arm, "seed": a.seed, "budget": a.budget,
                                             "launch_epoch": t0, "wall": time.time() - t0, "status": st}) + "\n")
                launch_log.flush()
                log.write(f"{time.strftime('%T')} {arm:5s} {stem(inst)} {time.time()-t0:.1f}s {st}\n")
                log.flush()
    log.write(f"{time.strftime('%T')} XCHG-DONE shard {a.shard}\n")


if __name__ == "__main__":
    main()
