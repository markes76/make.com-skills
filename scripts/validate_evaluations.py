#!/usr/bin/env python3
"""Validate the repository's dependency-free scenario evaluation format."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {"id", "references", "query", "expected_behavior", "safety_checks"}


def fail(path: Path, message: str) -> None:
    print(f"ERROR: {path.relative_to(ROOT)}: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    paths = sorted((ROOT / "evaluations").glob("**/*.json"))
    if not paths:
        fail(ROOT / "evaluations", "no evaluation files found")
    identifiers: set[str] = set()
    for path in paths:
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            fail(path, f"invalid JSON: {exc}")
        missing = REQUIRED - set(record)
        if missing:
            fail(path, f"missing keys: {', '.join(sorted(missing))}")
        if not isinstance(record["id"], str) or not record["id"]:
            fail(path, "id must be a non-empty string")
        if record["id"] in identifiers:
            fail(path, f"duplicate id: {record['id']}")
        identifiers.add(record["id"])
        for name in ("references", "expected_behavior", "safety_checks"):
            if not isinstance(record[name], list) or not record[name] or not all(isinstance(item, str) and item for item in record[name]):
                fail(path, f"{name} must be a non-empty list of strings")
        if not isinstance(record["query"], str) or not record["query"].strip():
            fail(path, "query must be a non-empty string")
    print(f"Evaluation validation passed ({len(paths)} cases)")


if __name__ == "__main__":
    main()
