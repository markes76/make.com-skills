#!/usr/bin/env python3
"""Record a sanitized, review-required Make automation learning candidate."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from learning_safety import (
    ALLOWED_ORIGIN,
    ALLOWED_REVIEW_STATUS,
    SCHEMA_VERSION,
    PublicLearningSafetyError,
    canonical_official_source_url,
    generic_public_text,
)

DEFAULT_OUTPUT = Path(os.environ.get("MAKE_SKILLS_PUBLIC_CANDIDATES", "~/.make-com-skills/public-candidates.jsonl")).expanduser()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--title", required=True)
    parser.add_argument("--kind", choices=("schema", "runtime", "design", "api", "tooling"), required=True)
    parser.add_argument("--symptom", required=True)
    parser.add_argument("--root-cause", required=True)
    parser.add_argument("--resolution", required=True)
    parser.add_argument("--evidence", required=True, help="Generic reproducible evidence; never paste an incident trace")
    parser.add_argument("--source-url", required=True, help="Allowlisted official Make documentation URL without query or fragment")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--consent", action="store_true", help="Required permission to retain a generic public-learning candidate locally")
    args = parser.parse_args()
    if not args.consent:
        raise SystemExit("Refusing to retain a lesson without --consent")

    try:
        fields = {
            "title": generic_public_text("title", args.title, 160),
            "kind": args.kind,
            "symptom": generic_public_text("symptom", args.symptom),
            "root_cause": generic_public_text("root_cause", args.root_cause),
            "resolution": generic_public_text("resolution", args.resolution),
            "evidence": generic_public_text("evidence", args.evidence),
        }
        source_url = canonical_official_source_url(args.source_url)
    except PublicLearningSafetyError as error:
        raise SystemExit(f"Refusing unsafe public-learning candidate: {error}") from error
    payload = "\n".join([source_url, *fields.values()]).encode("utf-8")
    lesson = {
        "id": hashlib.sha256(payload).hexdigest()[:16],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "candidate",
        "origin": ALLOWED_ORIGIN,
        "source_url": source_url,
        **fields,
        "schema_version": SCHEMA_VERSION,
        "expires_after_days": 90 if args.kind in {"schema", "runtime", "api", "tooling"} else 180,
        "review_status": ALLOWED_REVIEW_STATUS,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        args.out.parent.chmod(0o700)
    except OSError:
        pass
    with args.out.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(lesson, ensure_ascii=False) + "\n")
    try:
        args.out.chmod(0o600)
    except OSError:
        pass
    print(f"Recorded sanitized candidate {lesson['id']} in {args.out}")


if __name__ == "__main__":
    main()
