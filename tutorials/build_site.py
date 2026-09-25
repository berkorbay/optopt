"""Copy the tutorials into the GitHub Pages site (docs/tutorials/), which Jekyll renders as HTML.

    python tutorials/build_site.py

The markdown in tutorials/ stays the single source. Links between chapters (*.md) are converted to pages by GitHub
Pages; README.md becomes the section's index. Inline references to example scripts are linked to the repository.
"""
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC, OUT = ROOT / "tutorials", ROOT / "docs/tutorials"
REPO = "https://github.com/berkorbay/optopt/blob/main/"


def title(md):
    m = re.search(r"^#\s+(.+)$", md, re.M)
    return m.group(1).strip() if m else "Tutorial"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for f in sorted(SRC.glob("*.md")):
        md = f.read_text()
        # `tutorials/examples/x.py` or `examples/x.py` in inline code -> link to the file in the repository
        md = re.sub(r"`((?:tutorials/)?examples/[\w./-]+\.py)`",
                    lambda m: f"[`{m.group(1)}`]({REPO}tutorials/{m.group(1).removeprefix('tutorials/')})", md)
        md = re.sub(r"`(src/optopt/[\w./-]+\.py)`", lambda m: f"[`{m.group(1)}`]({REPO}{m.group(1)})", md)
        front = f"---\nlayout: default\ntitle: \"{title(md)}\"\n---\n\n"
        nav = "[← optopt](../) · [Tutorials](./)\n\n" if f.name != "README.md" else "[← optopt](../)\n\n"
        (OUT / f.name).write_text(front + nav + md)
    if (OUT / "figures").exists():
        shutil.rmtree(OUT / "figures")
    shutil.copytree(SRC / "figures", OUT / "figures")
    print(f"{len(list(SRC.glob('*.md')))} pages and {len(list((OUT / 'figures').iterdir()))} figures -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
