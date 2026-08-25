#!/usr/bin/env python3
"""Keep the npm bridge version aligned with the canonical repository version."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "npm" / "package.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Validate that npm/package.json matches VERSION (the default)")
    mode.add_argument("--write", action="store_true", help="Explicitly update npm/package.json to match VERSION")
    args = parser.parse_args()
    version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
    if not version:
        raise SystemExit("VERSION is empty")
    payload = json.loads(PACKAGE.read_text(encoding="utf-8"))
    current = payload.get("version")
    if current == version:
        print(f"npm package version matches VERSION ({version})")
        return 0
    if not args.write:
        raise SystemExit(f"npm/package.json version {current!r} does not match VERSION {version!r}; run with --write after review")
    payload["version"] = version
    PACKAGE.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"updated npm/package.json version to {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
