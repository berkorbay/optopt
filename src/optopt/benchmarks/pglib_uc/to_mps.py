"""Build PGLib-UC instances as MPS using the benchmark's own reference Pyomo model (uc_model.py, unmodified).

The model source is executed up to its solver call, then written out, so the formulation is exactly the
published one. Usage: python to_mps.py <pglib-uc repo> <outdir>
"""
import sys
from pathlib import Path


if __name__ == "__main__":
    repo, out = Path(sys.argv[1]), Path(sys.argv[2])
    src = (repo / "uc_model.py").read_text().split("from pyomo.opt import SolverFactory")[0]
    out.mkdir(parents=True, exist_ok=True)
    for f in sorted(repo.glob("*/*.json")):
        dst = out / f"{f.parent.name}__{f.stem}.mps"
        if dst.exists() or Path(str(dst) + ".gz").exists():
            continue
        sys.argv = ["uc_model.py", str(f)]
        g = {"__name__": "uc"}
        exec(compile(src, "uc_model.py", "exec"), g)
        g["m"].write(str(dst), io_options={"symbolic_solver_labels": False})
        print(dst.name, flush=True)
