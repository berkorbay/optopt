"""Write job files for the pool runner (experiments/00_baseline.py).

  miplib   : the 80 selected MIPLIB 2017 instances, 60 s, seed 0
  variance : 12 of those, seeds 1-4 (run-to-run variance, spec §8)
  ml4co    : item_placement + load_balancing, first N train + first M valid instances, 30 s
  uc       : PGLib-UC MPS files, 30 s
"""
import json
import random
import sys
from pathlib import Path

from optopt.paths import WORK as ROOT  # the workspace (cwd or $OPTOPT_HOME)
from optopt.paths import DATA, rel  # noqa: E402
from optopt.portfolio.strategies import MILESTONE  # noqa: E402


def write(name, rows):
    p = ROOT / "jobs" / f"{name}.jsonl"
    p.parent.mkdir(exist_ok=True)
    with open(p, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    print(p, len(rows))


def miplib():
    from importlib.resources import files
    sel = json.loads(files("optopt.references").joinpath("miplib_selected.json").read_text())
    rows = [dict(set="miplib", instance=rel(DATA / f"miplib/inst/{r['name']}.mps.gz"), strategies=MILESTONE,
                 seeds=[0], budget=60) for r in sel]
    write("miplib", rows)
    rng = random.Random(7)
    var = rng.sample(rows, 12)
    # GPU time is the bottleneck: CPU strategies get 4 extra seeds, cuOpt 2 (decided 00:55, D-001)
    write("variance", [x for r in var for x in (dict(r, strategies=["H0", "H1", "S0", "S1"], seeds=[1, 2, 3, 4]),
                                                  dict(r, strategies=["C0", "C1"], seeds=[1, 2]))])


def ml4co(n_train=100, n_test=25):
    rows = []
    for fam in ("1_item_placement", "2_load_balancing"):
        base = DATA / f"ml4co/instances/{fam}"
        for split, n in (("train", n_train), ("valid", n_test)):
            files = sorted((base / split).glob("*.mps.gz"), key=lambda p: int("".join(c for c in p.stem if c.isdigit()) or 0))[:n]
            rows += [dict(set=f"ml4co_{fam.split('_', 1)[1]}", split=split, instance=rel(p), strategies=MILESTONE,
                          seeds=[0], budget=30) for p in files]
    # interleave families so a partial run still covers both
    a = [r for r in rows if "item" in r["set"]]
    b = [r for r in rows if "load" in r["set"]]
    inter = [x for pair in zip(a, b) for x in pair] + a[len(b):] + b[len(a):]
    write("ml4co", inter)


def uc():
    files = sorted((DATA / "pglib_uc/mps").glob("*.mps.gz"))
    write("uc", [dict(set="pglib_uc", instance=rel(p), strategies=MILESTONE, seeds=[0], budget=60) for p in files])


if __name__ == "__main__":
    {"miplib": miplib, "ml4co": ml4co, "uc": uc}[sys.argv[1]]()
