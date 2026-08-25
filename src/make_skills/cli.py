"""Command-line entry point for the Make.com Skills companion."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .official_cli import OfficialCliError, locate, run, run_json
from .wizard import run_wizard


def doctor(executable: str | None, as_json: bool) -> int:
    binary = locate(executable)
    version = run(["--version"], binary).stdout.strip()
    user = run_json(["users", "me"], binary)
    result = {"status": "ok", "official_cli": binary, "official_cli_version": version, "authenticated": bool(user)}
    if as_json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(f"Official Make CLI: {binary} (v{version})")
        print("Authentication: verified")
    return 0


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="make-skills", description="Safe companion wizard for the official Make CLI")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--make-cli", help="Path to the official make-cli executable")
    commands = parser.add_subparsers(dest="command", required=True)
    doctor_parser = commands.add_parser("doctor", help="Verify official CLI and authentication with read-only calls")
    doctor_parser.add_argument("--json", action="store_true", help="Emit machine-readable status")
    wizard_parser = commands.add_parser("wizard", help="Start a read-first scenario review and planning wizard")
    wizard_parser.add_argument("--plans-dir", type=Path, default=Path("make-skills-plans"))
    wizard_parser.add_argument("--reviews-dir", type=Path, default=Path("make-skills-reviews"))
    args = parser.parse_args(argv)
    try:
        if args.command == "doctor":
            raise SystemExit(doctor(args.make_cli, args.json))
        if args.command == "wizard":
            run_wizard(args.make_cli, args.plans_dir, args.reviews_dir)
    except OfficialCliError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
