"""Pack the original measurements into a versioned release archive.

    python -m optopt.analysis.archive OUT_DIR [--tag v1]

Writes OUT_DIR/optopt-traces-<tag>.tar.gz (traces/raw with the pair runs' launch records, traces/sol, traces/resources,
traces/env.json) with SHA256SUMS inside the archive and next to it, and MANIFEST.json (code revision, file counts,
archive checksum). Unpack into a workspace, then `optopt reproduce` re-analyses the published study.
"""
import argparse
import hashlib
import io
import json
import subprocess
import tarfile
from pathlib import Path

from optopt.paths import WORK

PARTS = ["traces/raw", "traces/sol", "traces/resources", "traces/env.json"]


def sha256(path, buf=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(buf):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--tag", default="v1")
    ap.add_argument("--revision", help="code revision to record (default: HEAD of the workspace's git repository)")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    files = []
    for p in PARTS:
        q = WORK / p
        files += sorted(f for f in (q.rglob("*") if q.is_dir() else [q]) if f.is_file() and not f.name.endswith(".tmp"))
    sums = "".join(f"{sha256(f)}  {f.relative_to(WORK)}\n" for f in files)
    rev = a.revision or subprocess.run(["git", "-C", str(WORK), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    dirty = bool(subprocess.run(["git", "-C", str(WORK), "status", "--porcelain", "--", "src", "jobs"],
                                capture_output=True, text=True).stdout.strip())
    manifest = {"tag": a.tag, "code_revision": rev, "code_dirty": dirty, "n_files": len(files),
                "parts": {p: sum(1 for f in files if str(f.relative_to(WORK)).startswith(p)) for p in PARTS}}
    name = out / f"optopt-traces-{a.tag}.tar.gz"
    with tarfile.open(name, "w:gz") as tar:
        for f in files:
            tar.add(f, arcname=str(f.relative_to(WORK)))
        for n, text in (("SHA256SUMS", sums), ("MANIFEST.json", json.dumps(manifest, indent=1))):
            data = text.encode()
            ti = tarfile.TarInfo(n)
            ti.size = len(data)
            tar.addfile(ti, io.BytesIO(data))
    (out / "SHA256SUMS").write_text(sums)
    manifest["archive"] = {"file": name.name, "sha256": sha256(name), "bytes": name.stat().st_size}
    (out / "MANIFEST.json").write_text(json.dumps(manifest, indent=1))
    print(json.dumps(manifest, indent=1))


if __name__ == "__main__":
    main()
