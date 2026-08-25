#!/usr/bin/env python3
"""Validate portable-skill invariants without third-party dependencies."""

from __future__ import annotations

import json
import sys
from datetime import date, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    "README.md",
    "COMMUNITY_NOTICE.md",
    "assets/make-skills-cli-mark.svg",
    "assets/make-skills-cli-hero.png",
    "assets/README.md",
    "VERSION",
    "plugin.json",
    "pyproject.toml",
    "setup.py",
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    ".cursor/rules/make-automation-guru.mdc",
    ".codex/skills/make-com-skills-npm-publish/SKILL.md",
    "SKILL.md",
    "references/mcp-operations.md",
    "references/automation-architecture.md",
    "references/mapping-and-data.md",
    "references/ai-agents.md",
    "references/ai-engagement.md",
    "references/cli-delivery.md",
    "references/official-cli.md",
    "references/enterprise-operations.md",
    "references/continuous-learning.md",
    "references/error-playbook.md",
    "references/approved-lessons.md",
    "docs/LEARNING_LOOP.md",
    "docs/INSTALLATION.md",
    "docs/DEVELOPMENT.md",
    "docs/BRAND.md",
    "docs/NPM_RELEASE.md",
    "docs/UPSTREAM_SOURCE_WATCH.md",
    "docs/MCP_CAPABILITY_LOG.md",
    "evaluations/README.md",
    "learning/schemas/candidate.schema.json",
    "sources/README.md",
    "sources/community-solved-patterns.json",
    "references/community-research.md",
    "sources/upstream-manifest.json",
    "sources/upstream-source-state.json",
    "src/make_skills/cli.py",
    "src/make_skills/official_cli.py",
    "src/make_skills/personal_learning.py",
    "src/make_skills/wizard.py",
    "scripts/start_wizard.py",
    "scripts/sync_npm_version.py",
    "scripts/check_upstream_sources.py",
    "scripts/learning_safety.py",
    ".github/workflows/publish-npm.yml",
    ".github/workflows/upstream-source-watch.yml",
    "npm/package.json",
    "npm/bin/make-com-skills.js",
    "npm/lib/bridge.cjs",
    "npm/lib/official-cli-installer.cjs",
    "npm/lib/skill-installer.cjs",
    "npm/scripts/bundle-python.cjs",
    "npm/scripts/bundle-skill.cjs",
    "npm/test/bridge.test.cjs",
    "npm/NOTICE.md",
    "tests/TEST.md",
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

npm_publish_skill = (ROOT / ".codex/skills/make-com-skills-npm-publish/SKILL.md").read_text(encoding="utf-8")
if not npm_publish_skill.startswith("---\nname: make-com-skills-npm-publish\n"):
    fail("npm publishing skill frontmatter must identify make-com-skills-npm-publish")
if "[TODO:" in npm_publish_skill:
    fail("npm publishing skill contains an unfinished TODO")

readme = (ROOT / "README.md").read_text(encoding="utf-8")
if "Unofficial community companion" not in readme:
    fail("README must identify the project as an unofficial community companion")

index = ROOT / "sources/make-docs-index.json"
if index.exists():
    payload = json.loads(index.read_text(encoding="utf-8"))
    if not payload.get("documents"):
        fail("source index has no documents")
    for document in payload["documents"]:
        if set(document) != {"url", "title", "source", "content_sha256"}:
            fail("source index contains fields other than permitted metadata")

community_patterns = json.loads((ROOT / "sources/community-solved-patterns.json").read_text(encoding="utf-8"))
if community_patterns.get("schema_version") != 1:
    fail("community pattern ledger must use schema version 1")
if community_patterns.get("retention") != "metadata and sanitized paraphrases only":
    fail("community pattern ledger must forbid raw-content retention")
for pattern in community_patterns.get("patterns", []):
    required = {"id", "topic_url", "accepted_answer_url", "accepted_at", "outcome_summary", "official_cross_checks"}
    if set(pattern) != required:
        fail(f"community pattern has unexpected fields: {pattern.get('id', '<unknown>')}")
    if not pattern["topic_url"].startswith("https://community.make.com/t/") or not pattern["accepted_answer_url"].startswith("https://community.make.com/t/"):
        fail(f"community pattern has an invalid source URL: {pattern['id']}")
    try:
        accepted_at = datetime.fromisoformat(pattern["accepted_at"].replace("Z", "+00:00")).date()
    except ValueError:
        fail(f"community pattern has an invalid accepted_at value: {pattern['id']}")
    if (date.today() - accepted_at).days > 365:
        fail(f"community pattern is older than 365 days: {pattern['id']}")
    if not isinstance(pattern["official_cross_checks"], list) or not pattern["official_cross_checks"]:
        fail(f"community pattern requires official cross-checks: {pattern['id']}")
    if any(not link.startswith(("https://help.make.com/", "https://apps.make.com/", "https://developers.make.com/")) for link in pattern["official_cross_checks"]):
        fail(f"community pattern has a non-official cross-check: {pattern['id']}")

schema = json.loads((ROOT / "learning/schemas/candidate.schema.json").read_text(encoding="utf-8"))
if schema.get("type") != "object" or not schema.get("required"):
    fail("candidate schema must be a non-empty object schema")

for py_file in (ROOT / "scripts").glob("*.py"):
    compile(py_file.read_text(encoding="utf-8"), str(py_file), "exec")
for py_file in (ROOT / "src").glob("**/*.py"):
    compile(py_file.read_text(encoding="utf-8"), str(py_file), "exec")

plugin = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
if plugin.get("version") != (ROOT / "VERSION").read_text(encoding="utf-8").strip():
    fail("plugin.json version must match VERSION")

pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
if 'make-skills = "make_skills.cli:main"' not in pyproject:
    fail("pyproject.toml must expose make-skills")

package_version = (ROOT / "src/make_skills/__init__.py").read_text(encoding="utf-8")
if f'__version__ = "{plugin["version"]}"' not in package_version:
    fail("make_skills package version must match plugin.json")

npm_package = json.loads((ROOT / "npm/package.json").read_text(encoding="utf-8"))
if npm_package.get("name") != "@markesai/make-com-skills":
    fail("npm package must use the documented @markesai/make-com-skills scope")
if npm_package.get("version") != plugin["version"]:
    fail("npm/package.json version must match plugin.json")
if npm_package.get("private") is True:
    fail("npm package must not remain private after release configuration")
if npm_package.get("publishConfig", {}).get("access") != "public":
    fail("npm package must declare public publish access")
if set(npm_package.get("bin", {})) != {"make-com-skills", "make-skills-npx"}:
    fail("npm package must expose both documented command aliases")
if "python" not in npm_package.get("files", []) or "skill" not in npm_package.get("files", []) or "NOTICE.md" not in npm_package.get("files", []):
    fail("npm package must include the bundled Python companion, AI skill, and community notice")

print("Project validation passed")
