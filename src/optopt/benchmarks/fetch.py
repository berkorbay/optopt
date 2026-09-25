"""Fetch the public instance sets into the workspace's data directory (optopt.paths.DATA).

    optopt fetch miplib|pglib|ml4co

  miplib  MIPLIB 2017 benchmark set (benchmark.zip, ~330 MB) from miplib.zib.de, unpacked into data/miplib/inst/.
          The 80 instances used here are listed in optopt/references/miplib_selected.json; reference values ship
          with the package (optopt/references/miplib2017.solu).
  pglib   PGLib-UC (git clone of power-grid-lib/pglib-uc) and conversion to MPS with the benchmark's own Pyomo model
          (optopt.benchmarks.pglib_uc.to_mps; needs the `uc` extra).
  ml4co   The ML4CO competition instances (item placement, load balancing) are distributed by the organisers through
          Google Drive (see https://github.com/ds4dm/ml4co-competition/blob/main/DATA.md); download instances.tar.gz
          there and unpack it into data/ml4co/instances/. This command only prints the instructions.
Everything is public; nothing here needs credentials.
"""
import subprocess
import sys
import urllib.request
import zipfile

from optopt.paths import DATA

MIPLIB_URL = "https://miplib.zib.de/downloads/benchmark.zip"
PGLIB_REPO = "https://github.com/power-grid-lib/pglib-uc"
ML4CO_DATA = "https://github.com/ds4dm/ml4co-competition/blob/main/DATA.md"


def miplib():
    d = DATA / "miplib"
    (d / "inst").mkdir(parents=True, exist_ok=True)
    z = d / "benchmark.zip"
    if not z.exists():
        print(f"downloading {MIPLIB_URL} -> {z}")
        urllib.request.urlretrieve(MIPLIB_URL, z)
    with zipfile.ZipFile(z) as f:
        f.extractall(d / "inst")
    print(f"MIPLIB instances in {d / 'inst'}")


def pglib():
    d = DATA / "pglib_uc"
    d.mkdir(parents=True, exist_ok=True)
    if not (d / "repo").exists():
        subprocess.run(["git", "clone", "--depth", "1", PGLIB_REPO, str(d / "repo")], check=True)
    subprocess.run([sys.executable, "-m", "optopt.benchmarks.pglib_uc.to_mps", str(d / "repo"), str(d / "mps")], check=True)


def ml4co():
    print(f"ML4CO instances: follow {ML4CO_DATA}, then unpack instances.tar.gz into {DATA / 'ml4co'}/ so that\n"
          f"{DATA / 'ml4co/instances/1_item_placement'} and .../2_load_balancing exist.")


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else ""
    {"miplib": miplib, "pglib": pglib, "ml4co": ml4co}.get(what, lambda: print(__doc__))()
