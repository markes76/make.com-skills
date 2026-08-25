"""Command-line entry point for the Make.com Skills companion."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .official_cli import OfficialCliError, locate, run, run_json
from .personal_learning import default_artifact_directory
from .wizard import COMMUNITY_NOTICE, build_scenario_review, run_wizard, write_scenario_review


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
        print(COMMUNITY_NOTICE)
    return 0


def review(executable: str | None, scenario_id: str, reviews_directory: Path, as_json: bool, save: bool) -> int:
    """Read and derive a minimized review for one exact scenario without a Make write."""
    binary = locate(executable)
    version = run(["--version"], binary).stdout.strip()
    report = build_scenario_review(run_json(["scenarios", "get", scenario_id], binary), version)
    if save:
        write_scenario_review(reviews_directory, report, print)
    if as_json:
        print(json.dumps(report, ensure_ascii=False))
    else:
        confirmed = sum(1 for finding in report["findings"] if finding.get("classification") == "confirmed")
        needs_validation = sum(1 for finding in report["findings"] if finding.get("classification") == "needs_validation")
        not_evaluable = sum(1 for finding in report["findings"] if finding.get("classification") == "not_evaluable")
        print(f"Read-only review for scenario {report.get('scenario_id')}: {confirmed} confirmed, {needs_validation} needs-validation, {not_evaluable} not-evaluable finding(s).")
        print("No Make edit, run, or activation was performed.")
    return 0


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="make-skills", description="Independent community companion for the official Make CLI; plans and reports are not Make authorization.")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--make-cli", help="Path to the official make-cli executable")
    commands = parser.add_subparsers(dest="command", required=True)
    doctor_parser = commands.add_parser("doctor", help="Verify official CLI and authentication with read-only calls")
    doctor_parser.add_argument("--json", action="store_true", help="Emit machine-readable status")
    wizard_parser = commands.add_parser("wizard", help="Start a read-first scenario review and planning wizard")
    wizard_parser.add_argument("--plans-dir", type=Path, default=default_artifact_directory("plans"), help="Private local plan directory")
    wizard_parser.add_argument("--reviews-dir", type=Path, default=default_artifact_directory("reviews"), help="Private local review directory")
    wizard_parser.add_argument("--changes-dir", type=Path, default=default_artifact_directory("change-plans"), help="Private local change-plan directory")
    wizard_parser.add_argument("--personal-dir", type=Path, help="Private personal-learning location (defaults to ~/.make-com-skills)")
    wizard_parser.add_argument("--personal-learning", action="store_true", help="Enable consented private learning without asking again")
    review_parser = commands.add_parser("review", help="Read and derive a minimized review for one scenario ID")
    review_parser.add_argument("scenario_id", help="Exact Make scenario ID")
    review_parser.add_argument("--reviews-dir", type=Path, default=default_artifact_directory("reviews"), help="Private local review directory")
    review_parser.add_argument("--save", action="store_true", help="Save the derived report locally (never to Make or GitHub)")
    review_parser.add_argument("--json", action="store_true", help="Emit the derived report as JSON")
    args = parser.parse_args(argv)
    try:
        if args.command == "doctor":
            raise SystemExit(doctor(args.make_cli, args.json))
        if args.command == "wizard":
            run_wizard(
                args.make_cli,
                args.plans_dir,
                args.reviews_dir,
                args.changes_dir,
                args.personal_dir,
                True if args.personal_learning else None,
            )
        if args.command == "review":
            raise SystemExit(review(args.make_cli, args.scenario_id, args.reviews_dir, args.json, args.save))
    except OfficialCliError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
