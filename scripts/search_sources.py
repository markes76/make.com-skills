#!/usr/bin/env python3
"""Search the publishable Make official-document metadata index."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", nargs="+", help="Words that must occur in a title or URL")
    parser.add_argument("--source", choices=("apps.make.com", "developers.make.com", "help.make.com"))
    parser.add_argument("--index", type=Path, default=Path("sources/make-docs-index.json"))
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    if args.limit < 1:
        raise SystemExit("--limit must be at least 1")
    if not args.index.is_file():
        raise SystemExit(f"Source index not found: {args.index}")

    terms = [term.casefold() for term in args.query]
    records = json.loads(args.index.read_text(encoding="utf-8"))["documents"]
    matches = []
    for record in records:
        if args.source and record["source"] != args.source:
            continue
        haystack = f"{record['title']} {record['url']}".casefold()
        if all(term in haystack for term in terms):
            matches.append(record)

    for record in matches[:args.limit]:
        print(f"[{record['source']}] {record['title']}\n  {record['url']}")
    print(f"{min(len(matches), args.limit)} of {len(matches)} matching document(s)")


if __name__ == "__main__":
    main()
