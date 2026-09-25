"""Reference manifest: which reference value every scored instance uses, where it comes from, and every recorded
incumbent that beats it (review 2026-09-24).

  optopt analyse references   -> datasets/reference_manifest.csv, datasets/reference_flags.csv

MIPLIB instances use the published value from the MIPLIB 2017 solution file shipped with the package (`=opt=` proven
optimal, `=best=` best known); ML4CO and PGLib-UC have no published optima and use the best value found by any run of
this study ("best_observed"). An incumbent that beats a published value by more than 1e-4 (relative) is scored as
invalid by the primal gap (conservative) and listed in reference_flags.csv for independent checking — it is either an
invalid solution or a sign of a stale best-known value.
"""
import hashlib
import json
from importlib.resources import files

import pandas as pd

from optopt.analysis.build_runs import stem
from optopt.paths import WORK as ROOT


def published():
    txt = files("optopt.references").joinpath("miplib2017.solu").read_text()
    out = {}
    for line in txt.splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[0] in ("=opt=", "=best="):
            out[parts[1]] = (float(parts[2]), "opt" if parts[0] == "=opt=" else "best_known")
    return out, hashlib.sha256(txt.encode()).hexdigest()


def main():
    pub, sha = published()
    rows, flags, best = {}, [], {}
    for f in sorted((ROOT / "traces/raw").glob("*/*.json")):
        try:
            t = json.loads(f.read_text())
        except json.JSONDecodeError:
            continue
        if "instance" not in t or t.get("error"):
            continue
        n, s = stem(t["instance"]), t.get("sense", 1) or 1
        for e in t.get("events", []):
            p = e.get("primal")
            if p is None:
                continue
            if n not in best or s * p < s * best[n][0]:
                best[n] = (p, s)
            if n in pub and s * (p - pub[n][0]) < -1e-4 * max(1.0, abs(pub[n][0])):
                flags.append(dict(trace=f"{f.parent.name}/{f.name}", instance=n, incumbent=p, t=e.get("t"),
                                  reference=pub[n][0], reference_kind=pub[n][1]))
                break
        rows.setdefault(n, None)
    man = []
    for n in sorted(rows):
        if n in pub:
            man.append(dict(instance=n, reference=pub[n][0], kind=pub[n][1],
                            source=f"MIPLIB 2017 solution file (optopt/references/miplib2017.solu, sha256 {sha[:12]})"))
        elif n in best:
            man.append(dict(instance=n, reference=best[n][0], kind="best_observed", source="best value of any run in traces/"))
    pd.DataFrame(man).to_csv(ROOT / "datasets/reference_manifest.csv", index=False)
    pd.DataFrame(flags, columns=["trace", "instance", "incumbent", "t", "reference", "reference_kind"]).to_csv(
        ROOT / "datasets/reference_flags.csv", index=False)
    kinds = pd.DataFrame(man)["kind"].value_counts().to_dict() if man else {}
    print(f"{len(man)} instances: {kinds}; {len(flags)} trace(s) with an incumbent beating a published reference")


if __name__ == "__main__":
    main()
