"""Phase 4: Laya zero-shot and fine-tuned (MIP-Laya) strategy selection, on exactly the folds of 01_selection.

Writes datasets/laya_preds.json: {"<scheme>@<T>|<policy>": {instance: strategy_index}} and
datasets/laya_log.jsonl (per-fold training time, loss, inference latency). Feed the preds to
`01_selection.py --laya datasets/laya_preds.json`.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch

from optopt.paths import WORK as ROOT  # the workspace (cwd or $OPTOPT_HOME)
from optopt.experiments import selection as sel  # noqa: E402
from optopt.policies.laya import Laya, state_text  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--budgets", default="10,30")
    ap.add_argument("--epochs", type=int, default=8)
    ap.add_argument("--beta", type=float, default=20.0)
    ap.add_argument("--schemes", default="pooled,lofo")
    a = ap.parse_args()
    L = Laya()
    pf = ROOT / "datasets/laya_preds.json"
    out = json.load(open(pf)) if pf.exists() else {}  # keep other budgets' predictions
    logf = open(ROOT / "datasets/laya_log.jsonl", "a")

    def log(msg):
        print(msg, flush=True)

    for T in [int(x) for x in a.budgets.split(",")]:
        d = sel.load(T)
        if d is None:
            continue
        inst, C, _ = d
        feats = inst.to_dict("records")
        texts = [state_text(f, T) for f in feats]
        Cm = C.to_numpy()
        # zero-shot: the published checkpoint, no training
        L.reset()
        t0 = time.perf_counter()
        p = L.predict(texts)
        torch.cuda.synchronize()
        zs = p.argmax(1)
        for scheme in a.schemes.split(","):
            out[f"{scheme}@{T}|laya-zeroshot"] = {i: int(k) for i, k in zip(inst.index, zs)}
        logf.write(json.dumps(dict(T=T, policy="zeroshot", n=len(texts), infer_s=time.perf_counter() - t0)) + "\n")
        log(f"T={T} zero-shot choice dist: {np.bincount(zs, minlength=6).tolist()}")
        for scheme in a.schemes.split(","):
            if scheme == "pooled":
                fold = sel.assign_folds(inst).to_numpy()
                splits = [(np.where(fold != k)[0], np.where(fold == k)[0]) for k in range(5)]
            else:
                fams = inst["set"].to_numpy()
                splits = [(np.where(fams != f)[0], np.where(fams == f)[0]) for f in sorted(set(fams))]
            pred = {}
            for fi, (tr, te) in enumerate(splits):
                if len(te) == 0:
                    continue
                L.reset()
                t0 = time.perf_counter()
                L.finetune([texts[i] for i in tr], sel.soft_targets(Cm[tr], a.beta), epochs=a.epochs, seed=fi,
                           log=log)
                train_s = time.perf_counter() - t0
                t0 = time.perf_counter()
                pr = L.predict([texts[i] for i in te])
                torch.cuda.synchronize()
                for j, i in enumerate(te):
                    pred[inst.index[i]] = int(pr[j].argmax())
                logf.write(json.dumps(dict(T=T, scheme=scheme, fold=fi, n_train=len(tr), n_test=len(te), train_s=train_s,
                                           infer_s=time.perf_counter() - t0)) + "\n")
                logf.flush()
                log(f"T={T} {scheme} fold {fi}: train {len(tr)} test {len(te)} in {train_s:.0f}s")
            out[f"{scheme}@{T}|mip-laya"] = pred
        json.dump(out, open(ROOT / "datasets/laya_preds.json", "w"))
    L.reset()
    lat = []
    for i in range(53):
        t0 = time.perf_counter()
        L.predict([texts[i % len(texts)]])
        torch.cuda.synchronize()
        lat.append(1000 * (time.perf_counter() - t0))
    lat = lat[3:]
    json.dump(dict(single_median_ms=float(np.median(lat)), single_p90_ms=float(np.percentile(lat, 90)), n=len(lat),
                   gpu_mem_gb=torch.cuda.max_memory_allocated() / 1e9), open(ROOT / "datasets/laya_latency.json", "w"))
    print("LAYA-DONE", flush=True)


if __name__ == "__main__":
    main()
