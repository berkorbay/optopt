"""Write traces/env.json: the reproducibility record shared by every run of a session (spec §24)."""
import json
import platform
import subprocess
import sys
from pathlib import Path

from optopt.paths import WORK as ROOT  # the workspace (cwd or $OPTOPT_HOME)


def sh(c):
    try:
        return subprocess.run(c, shell=True, capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception as e:  # noqa: BLE001
        return f"error: {e}"


def main():
    from optopt.solvers import cuopt, highs, scip
    env = {
        "git_commit": sh(f"git -C {ROOT} rev-parse HEAD"),
        "hardware": "NVIDIA DGX Spark (GB10 Grace Blackwell, 10x Cortex-X925 + 10x Cortex-A725, 128 GB unified)",
        "kernel": platform.release(),
        "driver": sh("nvidia-smi --query-gpu=driver_version --format=csv,noheader"),
        "cuda": sh("nvidia-smi | grep -o 'CUDA Version: [0-9.]*'"),
        "python": sys.version.split()[0],
        "solvers": {"highs": highs.version(), "scip": scip.version(), "cuopt": cuopt.version()},
        "threads": {"highs": 1, "scip": 1, "cuopt_cpu": 3},
        "notes": "HiGHS/SCIP single-threaded on CPU lanes; cuOpt on GPU with 3 CPU threads; 2 cuOpt lanes run concurrently.",
    }
    out = ROOT / "traces/env.json"
    out.write_text(json.dumps(env, indent=1))
    print(json.dumps(env, indent=1))


if __name__ == "__main__":
    main()
