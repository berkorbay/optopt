"""Workspace paths. optopt is a library; the experiments run in a *workspace* directory that holds

    jobs/       job files (one JSON line per instance: set, instance, strategies, seeds, budget)
    data/       instances, reference values, model weights (not in git; see the data README)
    traces/     raw run trajectories, stored solutions, resource records
    datasets/   derived tables
    paper/      LaTeX source; paper/generated/ is written by the analysis modules

The workspace is $OPTOPT_HOME if set, otherwise the current working directory. The data directory is $OPTOPT_DATA
if set, otherwise <workspace>/data. Paths inside job files and traces are relative to the workspace
("data/miplib/inst/air05.mps.gz"), so a workspace can be moved or cloned and still runs.
"""
import os
from pathlib import Path

WORK = Path(os.environ.get("OPTOPT_HOME") or Path.cwd()).resolve()
os.environ.setdefault("OPTOPT_HOME", str(WORK))  # child processes (solver runs) inherit the same workspace
DATA = Path(os.environ["OPTOPT_DATA"]).resolve() if os.environ.get("OPTOPT_DATA") else WORK / "data"
MODELS = DATA / "models"


def resolve(p) -> Path:
    """Absolute path for a workspace-relative (or already absolute) path. The logical prefix `data/` maps to DATA,
    so `resolve(rel(x)) == x` also when $OPTOPT_DATA points outside the workspace."""
    p = Path(p)
    if p.is_absolute():
        return p
    if p.parts and p.parts[0] == "data":
        return DATA.joinpath(*p.parts[1:])
    return WORK / p


def rel(p) -> str:
    """Workspace-relative string for a path under the workspace or the data directory."""
    p = Path(p)
    if not p.is_absolute():
        return str(p)
    for base, pre in ((DATA.resolve(), "data"), (DATA, "data"), (WORK, "")):
        try:
            r = p.resolve().relative_to(base) if base is not WORK else p.relative_to(base)
            return str(Path(pre) / r) if pre else str(r)
        except ValueError:
            continue
    return str(p)
