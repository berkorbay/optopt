"""Laya as a resident service for the agent arms (D-004): the fine-tuned diagnosis model (SCIP setting at t = 0, the
same task as analysis/laya_diag.py), loaded once and answering over HTTP on 127.0.0.1:8111, like any model server.
A decision is one ~30 ms forward pass; the call is charged to the solver run that makes it.

  python agents/laya_service.py --train     # fine-tune on diag_train (60 ML4CO training instances), save checkpoint
  python agents/laya_service.py             # serve  POST /choose {"instance": name} -> {"probs": {setting: p}}
"""
import argparse
import json
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from optopt.paths import WORK as ROOT  # the workspace (cwd or $OPTOPT_HOME)
from optopt.analysis.build_runs import stem  # noqa: E402
from optopt.analysis.diag import S6, T, costs  # noqa: E402
from optopt.analysis.laya_diag import INSTR, OPTIONS  # noqa: E402
from optopt.policies.laya import Laya, state_text  # noqa: E402

from optopt.paths import MODELS  # noqa: E402

CKPT = MODELS / "laya_diag_ft.pt"
PORT = 8111


def features():
    return pd.read_parquet(ROOT / "datasets/features.parquet").assign(name=lambda d: d["instance"].map(stem)).set_index("name")


def train(beta=20.0, epochs=8, seed=0):
    F = features()
    tr = costs("diag_train", "P").pivot_table(index="name", columns="arm", values="c").reindex(columns=S6).dropna()
    tr = tr.loc[tr.index.intersection(F.index)]
    C = tr.to_numpy()
    soft = np.exp(-beta * (C - C.min(1, keepdims=True)))
    soft /= soft.sum(1, keepdims=True)
    lay = Laya(options=OPTIONS, instructions=INSTR)
    lay.finetune([state_text(F.loc[n].to_dict(), T) for n in tr.index], soft, epochs=epochs, seed=seed, log=print)
    CKPT.parent.mkdir(parents=True, exist_ok=True)
    torch.save(lay.model.state_dict(), CKPT)
    print("saved", CKPT, "trained on", len(tr), "instances")


def serve():
    F = features()
    lay = Laya(options=OPTIONS, instructions=INSTR)
    lay.model.load_state_dict(torch.load(CKPT, map_location=lay.device))
    lay.model.eval()
    lay.predict([state_text(F.iloc[0].to_dict(), T)])  # warm-up

    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            req = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            t0 = time.perf_counter()
            n = req["instance"]
            if n not in F.index:
                body = {"error": f"no features for {n}"}
            else:
                p = lay.predict([state_text(F.loc[n].to_dict(), req.get("budget", T))])[0]
                body = {"probs": {k: round(float(v), 4) for k, v in zip(S6, p)}, "ms": round(1000 * (time.perf_counter() - t0), 1)}
            out = json.dumps(body).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(out)))
            self.end_headers()
            self.wfile.write(out)

        def log_message(self, *a):
            pass

    print(f"laya service on 127.0.0.1:{PORT}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", action="store_true")
    a = ap.parse_args()
    train() if a.train else serve()
