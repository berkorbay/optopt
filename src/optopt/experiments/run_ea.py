"""Run the evolutionary partner (solvers/ea.py) for one instance, exchanging solutions with SCIP; write a JSON record."""
import argparse
import json
import os
import sys
import time
import traceback



def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("instance")
    ap.add_argument("--budget", type=float, required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--rho", type=float, default=0.2)
    ap.add_argument("--xchg-dir", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    from optopt.solvers import ea
    from optopt.solvers.xchg import Mailbox
    mb = Mailbox(a.xchg_dir, "cuopt", "scip")  # the EA takes the partner slot of the SCIP mailbox
    rec = {"instance": a.instance, "solver": "ea", "rho": a.rho, "seed": a.seed, "budget": a.budget,
           "t0_epoch": time.time()}
    try:
        rec["stats"] = ea.run(a.instance, a.budget, mb, seed=a.seed, rho=a.rho)
    except Exception as e:
        rec["error"] = f"{type(e).__name__}: {e}"
        rec["tb"] = traceback.format_exc()[-2000:]
    rec["xchg_log"] = [[round(t, 3), k, o] for t, k, o in mb.log]
    tmp = a.out + ".tmp"
    open(tmp, "w").write(json.dumps(rec))
    os.replace(tmp, a.out)


if __name__ == "__main__":
    main()
