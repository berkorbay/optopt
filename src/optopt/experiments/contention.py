"""Spec §15: does Laya inference interfere with cuOpt on the shared GB10 GPU?

Conditions (one cuOpt lane, nothing else running on the box):
  A  cuOpt alone
  B  Laya loaded on the GPU but idle (separate process holding the weights)
  C  Laya making one decision every 5 s (a dynamic controller at a 5 s interval; duty cycle ~1 %)
  D  Laya inferring back-to-back for the whole solve (worst case, ~100 % duty)
Each (instance, condition, rep) runs cuOpt C0 for `budget` s. Order is rotated per rep (Latin square) so drift
does not line up with a condition. nvidia-smi is sampled every 0.5 s. The Laya side logs every latency.

Output: datasets/contention.jsonl (one row per cuOpt run) and datasets/contention_laya.jsonl.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

from optopt.paths import WORK as ROOT  # the workspace (cwd or $OPTOPT_HOME)


def laya_worker(mode: str, ready: str, stop: str, out: str):
    """Runs in a child process: load Laya, signal ready, then idle / periodic / continuous until `stop` exists."""
    import numpy as np
    import pandas as pd
    import torch

    from optopt.policies.laya import Laya, state_text
    L = Laya()
    f = pd.read_parquet(ROOT / "datasets/features.parquet").to_dict("records")
    texts = [state_text(r, 30) for r in f[:64]]
    L.predict(texts[:2])
    torch.cuda.synchronize()
    Path(ready).write_text("1")
    lat, i = [], 0
    while not os.path.exists(stop):
        if mode == "B":
            time.sleep(0.2)
            continue
        t = time.perf_counter()
        L.predict([texts[i % len(texts)]])
        torch.cuda.synchronize()
        lat.append(time.perf_counter() - t)
        i += 1
        if mode == "C":
            time.sleep(max(0.0, 5.0 - lat[-1]))
    with open(out, "a") as fh:
        fh.write(json.dumps(dict(mode=mode, n=len(lat), lat_ms=[round(1000 * x, 2) for x in lat])) + "\n")


def smi_sampler(stop_evt, samples):
    q = "utilization.gpu,utilization.memory,memory.used,clocks.sm,power.draw"
    while not stop_evt.is_set():
        r = subprocess.run(["nvidia-smi", f"--query-gpu={q}", "--format=csv,noheader,nounits"], capture_output=True,
                           text=True)
        samples.append((time.time(), r.stdout.strip()))
        stop_evt.wait(0.5)


def run_cuopt(inst, budget, seed):
    from optopt.analysis.metrics import summarize
    tmp = f"/tmp/contention-{os.getpid()}.json"
    subprocess.run([sys.executable, "-m", "optopt.experiments.run_one", inst, "C0", "--budget", str(budget),
                    "--seed", str(seed), "--out", tmp], timeout=budget * 2 + 60)
    tr = json.load(open(tmp))
    return tr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("instances", nargs="+")
    ap.add_argument("--budget", type=float, default=30)
    ap.add_argument("--reps", type=int, default=2)
    a = ap.parse_args()
    from optopt.analysis.build_runs import solu, stem
    from optopt.analysis.metrics import summarize
    ref = solu()
    out = open(ROOT / "datasets/contention.jsonl", "a")
    lay_out = str(ROOT / "datasets/contention_laya.jsonl")
    conds = ["A", "B", "C", "D"]
    for rep in range(a.reps):
        for ii, inst in enumerate(a.instances):
            k = (rep + ii) % 4
            for cond in conds[k:] + conds[:k]:
                proc, ready, stop = None, f"/tmp/laya-ready-{os.getpid()}", f"/tmp/laya-stop-{os.getpid()}"
                for p in (ready, stop):
                    if os.path.exists(p):
                        os.remove(p)
                if cond != "A":
                    code = ("from optopt.experiments.contention import laya_worker; "
                            f"laya_worker({cond!r}, {ready!r}, {stop!r}, {lay_out!r})")
                    proc = subprocess.Popen([sys.executable, "-c", code], stdout=subprocess.DEVNULL,
                                            stderr=subprocess.DEVNULL)
                    t0 = time.time()
                    while not os.path.exists(ready) and time.time() - t0 < 300:
                        time.sleep(0.5)
                samples, ev = [], threading.Event()
                th = threading.Thread(target=smi_sampler, args=(ev, samples))
                th.start()
                t = time.time()
                tr = run_cuopt(inst, a.budget, seed=rep)
                wall = time.time() - t
                ev.set()
                th.join()
                if proc:
                    Path(stop).write_text("1")
                    proc.wait(timeout=120)
                r = ref.get(stem(inst))
                if r is None:
                    ps = [e["primal"] for e in tr.get("events", []) if e.get("primal") is not None]
                    r = min(ps) if ps else None
                m = summarize(tr, r, a.budget) if not tr.get("error") else {}
                out.write(json.dumps(dict(instance=stem(inst), cond=cond, rep=rep, wall=wall, ref=r,
                                          final_primal=tr.get("final_primal"), nodes=tr.get("nodes"),
                                          lp_iters=tr.get("lp_iters"), incumbent_count=tr.get("incumbent_count"),
                                          smi=[s for _, s in samples], **m)) + "\n")
                out.flush()
                print(time.strftime("%H:%M:%S"), stem(inst), cond, rep, round(m.get("pi", float("nan")), 4),
                      tr.get("nodes"), flush=True)
    print("CONTENTION-DONE", flush=True)


if __name__ == "__main__":
    main()
