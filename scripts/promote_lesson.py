#!/usr/bin/env python3
"""Promote one reviewed learning candidate into the public skill lessons file."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from learning_safety import PublicLearningSafetyError, canonical_official_source_url, validate_candidate

DEFAULT_CANDIDATES = Path(os.environ.get("MAKE_SKILLS_PUBLIC_CANDIDATES", "~/.make-com-skills/public-candidates.jsonl")).expanduser()

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("lesson_id")
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--output", type=Path, default=Path("references/approved-lessons.md"))
    parser.add_argument("--approve", action="store_true", help="Required explicit maintainer approval")
    parser.add_argument("--reviewed-source-url", required=True, help="The exact allowlisted official source the maintainer reviewed")
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
    try:
        selected = validate_candidate(selected)
        reviewed_source_url = canonical_official_source_url(args.reviewed_source_url)
    except PublicLearningSafetyError as error:
        raise SystemExit(f"Refusing unsafe public-learning promotion: {error}") from error
    if reviewed_source_url != selected["source_url"]:
        raise SystemExit("Refusing promotion: reviewed-source-url must match the candidate's official source URL")

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
        f"- **Official source reviewed:** {selected['source_url']}\n"
        "- **Status:** Maintainer-approved; revalidate when platform behavior changes.\n"
    )
    with args.output.open("a", encoding="utf-8") as handle:
        handle.write(entry + "\n")
    print(f"Promoted {selected['id']} to {args.output}")


if __name__ == "__main__":
    main()
