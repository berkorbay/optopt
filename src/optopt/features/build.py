"""Compute static features for every instance in the given job files -> datasets/features.parquet (cached)."""
import json
import sys
import time
from pathlib import Path
import pandas as pd
from optopt.paths import WORK as ROOT  # the workspace (cwd or $OPTOPT_HOME)
from optopt.experiments.run_one import main as _  # noqa: F401,E402  (keeps sys.path consistent)
from optopt.features.static import extract  # noqa: E402


if __name__ == "__main__":
    out = ROOT / "datasets/features.parquet"
    have = pd.read_parquet(out) if out.exists() else pd.DataFrame()
    done = set(have["instance"]) if len(have) else set()
    rows = []
    for jf in sys.argv[1:]:
        for line in open(jf):
            j = json.loads(line)
            if j["instance"] in done:
                continue
            done.add(j["instance"])
            t = time.perf_counter()
            try:
                f = extract(j["instance"])
            except Exception as e:  # noqa: BLE001
                print("fail", j["instance"], e, flush=True)
                continue
            f.update(instance=j["instance"], set=j["set"], split=j.get("split", ""), feat_time=time.perf_counter() - t)
            rows.append(f)
    df = pd.concat([have, pd.DataFrame(rows)], ignore_index=True) if rows else have
    out.parent.mkdir(exist_ok=True)
    df.to_parquet(out)
    print(len(df), "instances;", len(rows), "new")
