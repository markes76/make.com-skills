#!/usr/bin/env python3
"""Build a clean portable Make.com Skills zip from the tracked source tree."""

from __future__ import annotations

import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_PARTS = {
    ".git",
    ".learning",
    ".tools",
    "dist",
    "__pycache__",
    ".venv",
    "venv",
    "node_modules",
    "make-skills-plans",
    "make-skills-reviews",
    "make-skills-change-plans",
}
EXCLUDED_NAMES = {"make_public_docs.jsonl", ".DS_Store"}


def include(path: Path) -> bool:
    if path.is_symlink():
        return False
    relative = path.relative_to(ROOT)
    generated_npm_bundle = relative.parts[:2] == ("npm", "python")
    return not (set(relative.parts) & EXCLUDED_PARTS or generated_npm_bundle or path.name in EXCLUDED_NAMES or path.suffix == ".pyc")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Zip destination (defaults to dist/)")
    args = parser.parse_args()
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if not version:
        raise SystemExit("VERSION is empty")
    output = args.output or ROOT / "dist" / f"make.com-skills-v{version}.zip"
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with ZipFile(output, "w", compression=ZIP_DEFLATED) as archive:
        for path in sorted(ROOT.rglob("*")):
            if path.is_symlink() or not path.is_file() or not include(path) or path.resolve() == output:
                continue
            archive.write(path, Path("make.com-skills") / path.relative_to(ROOT))
            count += 1
    print(f"Wrote {count} files to {output}")


if __name__ == "__main__":
    main()
