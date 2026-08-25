"""Interactive, read-first guidance layered on top of official make-cli."""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .official_cli import OfficialCliError, label, list_items, locate, run, run_json


Input = Callable[[str], str]
Output = Callable[[str], None]


def choose(items: list[dict[str, Any]], noun: str, ask: Input, say: Output) -> dict[str, Any] | None:
    if not items:
        say(f"No {noun}s were returned.")
        return None
    for index, item in enumerate(items, start=1):
        say(f"  {index}. {label(item)}")
    while True:
        answer = ask(f"Choose a {noun} [1-{len(items)}] (Enter for 1): ").strip() or "1"
        if answer.isdigit() and 1 <= int(answer) <= len(items):
            return items[int(answer) - 1]
        say("Choose one of the displayed numbers.")


def scenario_suggestions(scenarios: list[dict[str, Any]]) -> list[str]:
    """Return conservative review prompts from list metadata, not invented blueprints."""
    if not scenarios:
        return ["No scenarios were returned; confirm the selected team and token scopes."]
    suggestions = [
        "For each production scenario, verify idempotency, error routing, rate-limit handling, and a controlled test event.",
        "Inspect module schemas and connection scope with MCP before proposing a mapping or configuration change.",
    ]
    inactive = sum(1 for item in scenarios if item.get("isActive") is False or item.get("active") is False)
    if inactive:
        suggestions.append(f"{inactive} scenario(s) appear inactive; review purpose and readiness before considering activation.")
    return suggestions


def write_design_handoff(directory: Path, ask: Input, say: Output) -> Path:
    outcome = ask("Describe the automation outcome: ").strip()
    trigger = ask("What should trigger it? ").strip()
    side_effects = ask("What external effects can it make? ").strip()
    plan = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "design-only",
        "outcome": outcome,
        "trigger": trigger,
        "external_side_effects": side_effects,
        "required_next_steps": [
            "Use Make MCP or official current documentation to discover exact apps, modules, fields, options, and connections.",
            "Define an idempotency key, error route, controlled test event, and inactive-by-default activation plan.",
            "Present the discovered blueprint for review before calling an official make-cli write command."
        ],
        "safety_note": "This file is a local design handoff, not a Make scenario blueprint and not authorization to create or activate a scenario."
    }
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"make-scenario-plan-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    say(f"Created local design handoff: {path}")
    return path


def run_wizard(
    executable: str | None = None,
    plans_directory: Path = Path("make-skills-plans"),
    ask: Input = input,
    say: Output = print,
) -> None:
    binary = locate(executable)
    say(f"Using official Make CLI: {binary}")
    run(["--version"], binary)
    try:
        run(["users", "me"], binary)
    except OfficialCliError:
        if ask("Authentication is unavailable. Start official `make-cli login` now? [Y/n] ").strip().casefold() not in {"n", "no"}:
            subprocess.run([binary, "login"], check=False)
            run(["users", "me"], binary)
        else:
            raise
    say("Authentication verified. The wizard will only perform reads and local file creation.")

    organizations = list_items(run_json(["organizations", "list"], binary), ("organizations", "data"))
    organization = choose(organizations, "organization", ask, say)
    if not organization:
        return
    organization_id = organization.get("id")
    teams = list_items(run_json(["teams", "list", "--organization-id", str(organization_id)], binary), ("teams", "data"))
    team = choose(teams, "team", ask, say)
    if not team:
        return
    team_id = team.get("id")

    while True:
        say("\nChoose an action: 1) review scenarios  2) enhancement prompts  3) new scenario design handoff  4) exit")
        action = ask("Action [1-4]: ").strip()
        if action == "1":
            scenarios = list_items(run_json(["scenarios", "list", "--team-id", str(team_id)], binary), ("scenarios", "data"))
            say(f"{len(scenarios)} scenario(s) returned for team {team_id}.")
            for item in scenarios:
                say(f"  - {label(item)}")
        elif action == "2":
            scenarios = list_items(run_json(["scenarios", "list", "--team-id", str(team_id)], binary), ("scenarios", "data"))
            for suggestion in scenario_suggestions(scenarios):
                say(f"  - {suggestion}")
        elif action == "3":
            write_design_handoff(plans_directory, ask, say)
        elif action == "4":
            say("No Make changes were made.")
            return
        else:
            say("Choose 1, 2, 3, or 4.")
