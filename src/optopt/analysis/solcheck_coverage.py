"""Coverage of the independent solution check: every stored solution joined to its trace and its check result.

  optopt analyse solcheck_coverage   -> datasets/solcheck_coverage.csv (one row per stored solution)

States: checked_feasible, checked_infeasible, not_checked (no row in datasets/solcheck_<set>.csv), no_trace (a stored
solution without its trace). What is stored: the FINAL incumbent of each SCIP run (SCIP is the only wrapper that
writes solution vectors); intermediate incumbents and HiGHS/cuOpt solutions are not stored, so they are not checked.
"""
import pandas as pd

from optopt.paths import WORK as ROOT


def main():
    rows = []
    for sd in sorted((ROOT / "traces/sol").iterdir()):
        if not sd.is_dir():
            continue
        chk_file = ROOT / f"datasets/solcheck_{sd.name}.csv"
        chk = pd.read_csv(chk_file).set_index("sol")["feasible"].to_dict() if chk_file.exists() else {}
        for f in sorted(sd.glob("*.json.gz")):
            trace = ROOT / "traces/raw" / sd.name / f.name.replace(".json.gz", ".json")
            if not trace.exists():
                state = "no_trace"
            elif f.name not in chk:
                state = "not_checked"
            elif "__CORRUPT__" in f.name:  # deliberately corrupted solution (night-1 checker smoke test): must fail
                state = "test_fixture_detected" if not bool(chk[f.name]) else "test_fixture_MISSED"
            else:
                state = "checked_feasible" if bool(chk[f.name]) else "checked_infeasible"
            rows.append(dict(set=sd.name, sol=f.name, state=state))
    df = pd.DataFrame(rows)
    df.to_csv(ROOT / "datasets/solcheck_coverage.csv", index=False)
    print(df.groupby(["set", "state"]).size().unstack(fill_value=0).to_string())
    print("\ntotal:", df["state"].value_counts().to_dict())


if __name__ == "__main__":
    main()
