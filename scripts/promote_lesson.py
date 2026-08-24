#!/usr/bin/env python3
"""Promote one reviewed learning candidate into the public skill lessons file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lesson_id")
    parser.add_argument("--candidates", type=Path, default=Path(".learning/candidates.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("references/approved-lessons.md"))
    parser.add_argument("--approve", action="store_true", help="Required explicit maintainer approval")
    args = parser.parse_args()
    if not args.approve:
        raise SystemExit("Refusing promotion without --approve")
    if not args.candidates.exists():
        raise SystemExit(f"Candidate store not found: {args.candidates}")

    selected = None
    for line in args.candidates.read_text(encoding="utf-8").splitlines():
        record = json.loads(line)
        if record.get("id") == args.lesson_id:
            selected = record
            break
    if not selected:
        raise SystemExit(f"No candidate with id {args.lesson_id}")
    required = ("title", "kind", "symptom", "root_cause", "resolution", "evidence")
    if any(not selected.get(key) for key in required):
        raise SystemExit("Candidate lacks required reviewed fields")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    if not args.output.exists():
        args.output.write_text("# Approved Make Automation Lessons\n\n", encoding="utf-8")
    entry = (
        f"## {selected['title']}\n\n"
        f"- **Type:** {selected['kind']}\n"
        f"- **Symptom:** {selected['symptom']}\n"
        f"- **Root cause:** {selected['root_cause']}\n"
        f"- **Resolution:** {selected['resolution']}\n"
        f"- **Evidence:** {selected['evidence']}\n"
        "- **Status:** Maintainer-approved; revalidate when platform behavior changes.\n"
    )
    with args.output.open("a", encoding="utf-8") as handle:
        handle.write(entry + "\n")
    print(f"Promoted {selected['id']} to {args.output}")


if __name__ == "__main__":
    main()
