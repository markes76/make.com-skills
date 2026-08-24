#!/usr/bin/env python3
"""Create a publishable Make documentation index without copying article bodies."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("corpus", type=Path, help="User-authorized JSONL corpus")
    parser.add_argument("--output", type=Path, default=Path("sources/make-docs-index.json"))
    args = parser.parse_args()

    entries: list[dict[str, str]] = []
    counts: Counter[str] = Counter()
    for number, line in enumerate(args.corpus.read_text(encoding="utf-8").splitlines(), start=1):
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid JSON on corpus line {number}: {exc}") from exc
        required = ("url", "title", "source", "content_sha256")
        if any(not record.get(key) for key in required):
            raise SystemExit(f"Corpus line {number} lacks one of: {', '.join(required)}")
        entries.append({key: str(record[key]) for key in required})
        counts[str(record["source"])] += 1

    entries.sort(key=lambda item: (item["source"], item["title"].casefold(), item["url"]))
    output = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "record_count": len(entries),
        "by_source": dict(sorted(counts.items())),
        "notice": "Metadata index only. Article Markdown is intentionally excluded.",
        "documents": entries,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(entries)} source records to {args.output}")


if __name__ == "__main__":
    main()
