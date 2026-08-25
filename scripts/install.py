#!/usr/bin/env python3
"""Install the portable Make Automation Guru bundle without symlinks.

The command is a dry run unless --apply is present. It never overwrites an
existing destination unless --force is present.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_NAME = "make-automation-guru"
IGNORED = shutil.ignore_patterns(
    ".git",
    ".learning",
    ".tools",
    "dist",
    ".venv",
    "venv",
    "node_modules",
    "make-skills-plans",
    "make-skills-reviews",
    "make-skills-change-plans",
    "make_public_docs.jsonl",
    "python",
    "__pycache__",
    "*.pyc",
    ".DS_Store",
)


def package_destination(target: str, scope: str, project: Path) -> Path:
    if target == "codex":
        return Path.home() / ".codex/skills" / PACKAGE_NAME if scope == "user" else project / ".codex/skills" / PACKAGE_NAME
    if target == "claude":
        return Path.home() / ".claude/skills" / PACKAGE_NAME if scope == "user" else project / ".claude/skills" / PACKAGE_NAME
    if target == "openclaw":
        return Path.home() / ".openclaw/skills" / PACKAGE_NAME if scope == "user" else project / ".agents/skills" / PACKAGE_NAME
    return project / ".agents/skills" / PACKAGE_NAME


def cursor_rule() -> str:
    return "---\ndescription: Use Make Automation Guru for Make.com scenario design and operations.\nalwaysApply: false\n---\n\n@../../.agents/skills/make-automation-guru/SKILL.md\n"


def gemini_context() -> str:
    return f"@.agents/skills/{PACKAGE_NAME}/SKILL.md\n"


def copy_bundle(destination: Path, apply: bool, force: bool) -> None:
    source_symlink = next((path for path in ROOT.rglob("*") if path.is_symlink()), None)
    if source_symlink:
        raise SystemExit(f"Refusing to install a bundle containing a symlink: {source_symlink}")
    if destination.exists() and not force:
        raise SystemExit(f"Refusing to overwrite existing bundle: {destination} (use --force)")
    print(f"bundle: {ROOT} -> {destination}")
    if not apply:
        return
    if destination.exists():
        shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT, destination, ignore=IGNORED)


def write_file(path: Path, content: str, apply: bool, force: bool) -> None:
    if path.exists() and not force:
        raise SystemExit(f"Refusing to overwrite existing adapter: {path} (use --force)")
    print(f"adapter: {path}")
    if apply:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", choices=("codex", "claude", "cursor", "gemini", "openclaw", "agents"), required=True)
    parser.add_argument("--scope", choices=("project", "user"), default="project")
    parser.add_argument("--project", type=Path, default=Path.cwd(), help="Target project for project-scoped installs")
    parser.add_argument("--apply", action="store_true", help="Perform the copy; omitted means dry run")
    parser.add_argument("--force", action="store_true", help="Permit replacement of an existing bundle or adapter")
    args = parser.parse_args()

    if args.scope == "user" and args.target in {"cursor", "gemini", "agents"}:
        raise SystemExit(f"{args.target} has no supported user-scope installer; use --scope project")

    project = args.project.resolve()
    effective_target = "agents" if args.target in {"cursor", "gemini", "agents"} else args.target
    destination = package_destination(effective_target, args.scope, project)
    copy_bundle(destination, args.apply, args.force)

    if args.target == "cursor":
        write_file(project / ".cursor/rules/make-automation-guru.mdc", cursor_rule(), args.apply, args.force)
    elif args.target == "gemini":
        write_file(project / "GEMINI.md", gemini_context(), args.apply, args.force)

    if not args.apply:
        print("Dry run only. Re-run with --apply to install.")


if __name__ == "__main__":
    main()
