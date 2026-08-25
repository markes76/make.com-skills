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


def choose(items: list[dict[str, Any]], noun: str, ask: Input, say: Output, allow_id: bool = False) -> dict[str, Any] | None:
    if not items:
        say(f"No {noun}s were returned.")
        return None
    for index, item in enumerate(items, start=1):
        say(f"  {index}. {label(item)}")
    while True:
        suffix = " or ID" if allow_id else ""
        answer = ask(f"Choose a {noun} [1-{len(items)}]{suffix} (Enter for 1): ").strip() or "1"
        if answer.isdigit() and 1 <= int(answer) <= len(items):
            return items[int(answer) - 1]
        if allow_id:
            for item in items:
                if str(item.get("id")) == answer:
                    return item
        say("Choose one of the displayed numbers" + (" or IDs." if allow_id else "."))


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


def unwrap_scenario(value: Any) -> dict[str, Any]:
    """Support common official-CLI response envelopes without retaining raw detail."""
    if not isinstance(value, dict):
        return {}
    nested = value.get("scenario")
    if isinstance(nested, dict):
        return {**value, **nested}
    return value


def decode_blueprint(scenario: dict[str, Any]) -> Any:
    blueprint = scenario.get("blueprint")
    if isinstance(blueprint, str):
        try:
            return json.loads(blueprint)
        except json.JSONDecodeError:
            return None
    return blueprint


def find_modules(value: Any) -> list[str]:
    """Extract module labels from a blueprint shape without assuming its exact schema."""
    found: list[str] = []
    if isinstance(value, dict):
        module = value.get("module")
        if isinstance(module, str):
            found.append(module)
        for nested in value.values():
            found.extend(find_modules(nested))
    elif isinstance(value, list):
        for nested in value:
            found.extend(find_modules(nested))
    return found


def build_scenario_review(detail: Any) -> dict[str, Any]:
    """Create a derived, secret-free review report from one live scenario read."""
    scenario = unwrap_scenario(detail)
    blueprint = decode_blueprint(scenario)
    modules = find_modules(blueprint)
    serialized = json.dumps(blueprint, ensure_ascii=False).casefold() if blueprint is not None else ""
    observations: list[str] = []
    recommendations = [
        "Confirm a stable idempotency key for every externally visible side effect.",
        "Inspect current module schemas, options, and connections with Make MCP before proposing configuration changes.",
        "Run a controlled test and inspect its execution before any activation or replay.",
    ]
    if not blueprint:
        observations.append("A parseable blueprint was not available in this response; inspect the scenario in Make or retrieve it through MCP before changing it.")
    else:
        observations.append(f"Parsed blueprint with {len(modules)} module reference(s).")
    if "webhook" in serialized or "hook" in serialized:
        recommendations.append("For webhook-triggered paths, verify the learned payload schema and route malformed deliveries to review.")
    if "http" in serialized or "api" in serialized:
        recommendations.append("For API calls, confirm timeout, rate-limit recovery, and non-2xx error routing.")
    if not any(marker in serialized for marker in ("error", "incomplete", "retry")):
        recommendations.append("No obvious error/retry marker was found in the available blueprint; verify error handling and incomplete-execution policy manually.")
    return {
        "schema_version": 1,
        "status": "read-only-review",
        "scenario_id": scenario.get("id"),
        "scenario_name": scenario.get("name") or scenario.get("label") or "unnamed",
        "active": scenario.get("isActive", scenario.get("active")),
        "module_count": len(modules),
        "module_references": modules[:50],
        "observations": observations,
        "recommendations": recommendations,
        "safety_note": "This derived report omits the raw blueprint and does not authorize edits, runs, or activation."
    }


def write_scenario_review(directory: Path, review: dict[str, Any], say: Output) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    scenario_id = review.get("scenario_id") or "unknown"
    path = directory / f"scenario-review-{scenario_id}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    path.write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    say(f"Saved derived review report: {path}")
    return path


def review_scenarios(team_id: Any, binary: str, reviews_directory: Path, ask: Input, say: Output) -> None:
    scenarios = list_items(run_json(["scenarios", "list", "--team-id", str(team_id)], binary), ("scenarios", "data"))
    say(f"{len(scenarios)} scenario(s) returned for team {team_id}.")
    while scenarios:
        selected = choose(scenarios, "scenario", ask, say, allow_id=True)
        if not selected:
            return
        scenario_id = selected.get("id")
        detail = run_json(["scenarios", "get", str(scenario_id)], binary)
        review = build_scenario_review(detail)
        say(f"\nReview: {review['scenario_id']}: {review['scenario_name']}")
        say(f"  Active: {review['active']}; module references: {review['module_count']}")
        for observation in review["observations"]:
            say(f"  Observation: {observation}")
        for recommendation in review["recommendations"]:
            say(f"  Recommendation: {recommendation}")
        write_scenario_review(reviews_directory, review, say)
        if ask("Review another scenario from this team? [y/N] ").strip().casefold() not in {"y", "yes"}:
            return


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
    reviews_directory: Path = Path("make-skills-reviews"),
    ask: Input = input,
    say: Output = print,
) -> None:
    try:
        binary = locate(executable)
    except OfficialCliError as exc:
        say(str(exc))
        say("Install the official Make CLI first, then re-run this wizard. It can guide authentication after the binary is available.")
        return
    say(f"Using official Make CLI: {binary}")
    run(["--version"], binary)
    try:
        run(["users", "me"], binary)
    except OfficialCliError as exc:
        detail = str(exc).casefold()
        if "api key is required" in detail or "zone is required" in detail:
            prompt = "No usable Make API authentication was found. Start official `make-cli login` to create/connect a key now? [Y/n] "
        else:
            say(f"The official CLI could not complete a read: {exc}")
            say("Check network access and that MAKE_ZONE is a hostname such as eu1.make.com, then run `make-skills doctor`.")
            return
        if ask(prompt).strip().casefold() not in {"n", "no"}:
            subprocess.run([binary, "login"], check=False)
            run(["users", "me"], binary)
        else:
            say("Authentication was not changed. No Make API call beyond the failed read was made.")
            return
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
        say("\nChoose an action: 1) review one scenario  2) team-wide enhancement prompts  3) new scenario design handoff  4) exit")
        action = ask("Action [1-4]: ").strip()
        if action == "1":
            review_scenarios(team_id, binary, reviews_directory, ask, say)
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
