#!/usr/bin/env python3
"""Validate portable-skill invariants without third-party dependencies."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    "README.md",
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    ".cursor/rules/make-automation-guru.mdc",
    "SKILL.md",
    "references/mcp-operations.md",
    "references/automation-architecture.md",
    "references/cli-delivery.md",
    "references/continuous-learning.md",
    "references/error-playbook.md",
    "references/approved-lessons.md",
    "docs/LEARNING_LOOP.md",
    "learning/schemas/candidate.schema.json",
    "sources/README.md",
)


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


for relative in REQUIRED:
    if not (ROOT / relative).is_file():
        fail(f"missing required file: {relative}")

skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
if not skill.startswith("---\nname: make-automation-guru\n"):
    fail("skill frontmatter must identify make-automation-guru")
if "[TODO:" in skill:
    fail("skill contains an unfinished TODO")

index = ROOT / "sources/make-docs-index.json"
if index.exists():
    payload = json.loads(index.read_text(encoding="utf-8"))
    if not payload.get("documents"):
        fail("source index has no documents")
    for document in payload["documents"]:
        if set(document) != {"url", "title", "source", "content_sha256"}:
            fail("source index contains fields other than permitted metadata")

schema = json.loads((ROOT / "learning/schemas/candidate.schema.json").read_text(encoding="utf-8"))
if schema.get("type") != "object" or not schema.get("required"):
    fail("candidate schema must be a non-empty object schema")

for py_file in (ROOT / "scripts").glob("*.py"):
    compile(py_file.read_text(encoding="utf-8"), str(py_file), "exec")

print("Project validation passed")
