"""Pick a diverse ~80-instance subset of the MIPLIB 2017 benchmark set (spec §6.2), deterministically.

Rules:
- at most one instance per MIPLIB `Group`, so near-duplicate families (drayage, neos-*, …) cannot dominate;
- drop instances with >2.5M nonzeros (memory with 14 concurrent CPU runs plus 2 GPU lanes) and known-infeasible ones;
- stratify by status (easy / hard / open) and size tercile, then sample with a fixed seed.

The spec's SHORT/MEDIUM/HARD grouping (by 300 s screening time) is assigned afterwards from measured runs.
"""
import html
import json
import random
import re
import sys
from pathlib import Path

from optopt.paths import DATA as _D  # noqa: E402
DATA = _D / "miplib"


def table():
    s = (DATA / "tag_benchmark.html").read_text()
    out = []
    for r in re.findall(r"<tr[^>]*>(.*?)</tr>", s, re.S)[1:]:
        c = [html.unescape(re.sub("<[^>]+>", "", x)).strip() for x in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", r, re.S)]
        out.append(dict(name=c[0], status=c[1], vars=int(c[2]), bin=int(c[3]), int=int(c[4]), cont=int(c[5]),
                        cons=int(c[6]), nnz=int(c[7]), group=c[9], objective=c[10], tags=c[11].split()))
    return out


def main(n=80, seed=20260923):
    rows = [r for r in table() if r["nnz"] <= 2_500_000 and "infeasible" not in r["objective"].lower()
            and r["status"] in ("easy", "hard", "open")]
    rng = random.Random(seed)
    rng.shuffle(rows)
    seen, uniq = set(), []
    for r in rows:
        g = r["group"] if r["group"] not in ("–", "-", "") else r["name"]
        if g in seen:
            continue
        seen.add(g)
        uniq.append(r)
    uniq.sort(key=lambda r: r["nnz"])
    k = len(uniq)
    for i, r in enumerate(uniq):
        r["size_tercile"] = min(2, 3 * i // k)
    strata = {}
    for r in uniq:
        strata.setdefault((r["status"], r["size_tercile"]), []).append(r)
    # proportional allocation, at least 2 per non-empty stratum
    picked = []
    for key, lst in sorted(strata.items()):
        take = max(2, round(n * len(lst) / k))
        picked += lst[:take]
    rng.shuffle(picked)
    picked = sorted(picked[:n], key=lambda r: r["name"])
    json.dump(picked, open(DATA / "selected.json", "w"), indent=1)
    from collections import Counter
    print(len(rows), "eligible,", k, "after one-per-group,", len(picked), "picked", file=sys.stderr)
    print(Counter((r["status"], r["size_tercile"]) for r in picked), file=sys.stderr)


if __name__ == "__main__":
    main()
