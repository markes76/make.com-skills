#!/usr/bin/env python3
"""Record a sanitized, review-required Make automation learning candidate."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


SECRET_PATTERNS = (
    re.compile(r"\b(?:ghp|github_pat|sk|xox[baprs]|AIza)[_-][A-Za-z0-9_-]{8,}\b", re.I),
    re.compile(r"(?im)\b(authorization|api[_ -]?key|token|password|secret)\s*[:=]\s*[^\r\n]+"),
)
URL_QUERY = re.compile(r"https?://[^\s?]+\?[^\s]+", re.I)
EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
WEBHOOK_URL = re.compile(r"https?://[^\s]*(?:webhook|hooks)[^\s]*", re.I)
MAX_FIELD_LENGTH = 2_000


def sanitize(value: str) -> str:
    value = WEBHOOK_URL.sub("[REDACTED_WEBHOOK_URL]", value)
    value = URL_QUERY.sub("[REDACTED_URL_QUERY]", value)
    value = EMAIL.sub("[REDACTED_EMAIL]", value)
    for pattern in SECRET_PATTERNS:
        value = pattern.sub("[REDACTED]", value)
    return value.strip()[:MAX_FIELD_LENGTH]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--title", required=True)
    parser.add_argument("--kind", choices=("schema", "runtime", "design", "api", "tooling"), required=True)
    parser.add_argument("--symptom", required=True)
    parser.add_argument("--root-cause", required=True)
    parser.add_argument("--resolution", required=True)
    parser.add_argument("--evidence", required=True, help="Sanitized test/inspection evidence")
    parser.add_argument("--out", type=Path, default=Path(".learning/candidates.jsonl"))
    parser.add_argument("--consent", action="store_true", help="Required permission to retain a sanitized candidate locally")
    args = parser.parse_args()
    if not args.consent:
        raise SystemExit("Refusing to retain a lesson without --consent")

    fields = {key: sanitize(str(getattr(args, key))) for key in ("title", "kind", "symptom", "root_cause", "resolution", "evidence")}
    payload = "\n".join(fields.values()).encode("utf-8")
    lesson = {
        "id": hashlib.sha256(payload).hexdigest()[:16],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "candidate",
        **fields,
        "schema_version": 1,
        "expires_after_days": 90 if args.kind in {"schema", "runtime", "api", "tooling"} else 180,
        "promotion_rule": "Requires maintainer review and validate_project.py before promotion.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(lesson, ensure_ascii=False) + "\n")
    print(f"Recorded sanitized candidate {lesson['id']} in {args.out}")


if __name__ == "__main__":
    main()
