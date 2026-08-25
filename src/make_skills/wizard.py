"""Interactive, read-first guidance layered on top of official make-cli."""

from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .official_cli import OfficialCliError, label, list_items, locate, run, run_json
from .personal_learning import (
    PersonalLearningStore,
    default_artifact_directory,
    default_directory,
    ensure_private_directory,
    sanitize,
    write_private_text,
)


Input = Callable[[str], str]
Output = Callable[[str], None]
COMMUNITY_NOTICE = (
    "Make Skills is an independent community companion, not an official Make.com package or a replacement for make-cli. "
    "Review every plan and command; it provides no guarantee and never authorizes a Make mutation by itself."
)


def safe_filename_component(value: Any, fallback: str = "unknown") -> str:
    """Keep response-derived identifiers inside the intended local directory."""
    compact = re.sub(r"[^A-Za-z0-9_-]+", "_", str(value or "")).strip("_")
    return compact[:80] or fallback


def choose(items: list[dict[str, Any]], noun: str, ask: Input, say: Output, allow_id: bool = False) -> dict[str, Any] | None:
    if not items:
        say(f"No {noun}s were returned.")
        return None
    for index, item in enumerate(items, start=1):
        say(f"  {index}. {label(item)}")
    while True:
        suffix = " or ID (use id:<ID> to force an ID)" if allow_id else ""
        answer = ask(f"Choose a {noun} [1-{len(items)}]{suffix} (Enter for 1): ").strip() or "1"
        requested_id = answer[3:].strip() if allow_id and answer.casefold().startswith("id:") else ""
        if requested_id:
            for item in items:
                if str(item.get("id")) == requested_id:
                    return item
            return {"id": requested_id, "name": "Requested scenario ID (not in current list)"}
        if allow_id:
            for item in items:
                if str(item.get("id")) == answer:
                    return item
        if answer.isdigit() and 1 <= int(answer) <= len(items):
            return items[int(answer) - 1]
        if allow_id and answer.isdigit():
            return {"id": answer, "name": "Requested scenario ID (not in current list)"}
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


def unwrap_scenario(value: Any) -> tuple[dict[str, Any], str]:
    """Support known response envelopes and classify unknown shapes conservatively."""
    if not isinstance(value, dict):
        return {}, "unsupported-response"
    nested = value.get("scenario")
    if isinstance(nested, dict):
        return {**value, **nested}, "scenario-envelope"
    if any(key in value for key in ("id", "blueprint", "isActive", "active")):
        return value, "direct-scenario"
    return value, "unrecognized-object"


def decode_blueprint(scenario: dict[str, Any]) -> tuple[Any, str]:
    blueprint = scenario.get("blueprint")
    if blueprint is None:
        return None, "absent"
    if isinstance(blueprint, str):
        try:
            return json.loads(blueprint), "parsed-json"
        except json.JSONDecodeError:
            return None, "malformed-json"
    if isinstance(blueprint, (dict, list)):
        return blueprint, "structured"
    return None, "unsupported-type"


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


def reported_findings(detail: Any, scenario: dict[str, Any], envelope: str) -> list[dict[str, str]]:
    """Classify only API-reported errors; never expose their raw text or data."""
    findings: list[dict[str, str]] = []
    containers = [(detail, "$")]
    if scenario is not detail:
        containers.append((scenario, "$.scenario" if envelope == "scenario-envelope" else "$"))
    for container, path in containers:
        if not isinstance(container, dict):
            continue
        for key, severity in (("errors", "error"), ("issues", "warning"), ("warnings", "warning")):
            value = container.get(key)
            count = len(value) if isinstance(value, list) else int(bool(value))
            if count:
                findings.append(
                    {
                        "code": f"API_REPORTED_{key.upper()}",
                        "severity": severity,
                        "classification": "confirmed",
                        "confidence": "high",
                        "evidence_path": f"{path}.{key}",
                        "summary": f"The official CLI response reported {count} {key} item(s).",
                        "recommendation": "Inspect the current scenario and the narrowest relevant execution before proposing a repair.",
                    }
                )
    unique: dict[str, dict[str, str]] = {finding["code"]: finding for finding in findings}
    return list(unique.values())


def build_scenario_review(detail: Any, official_cli_version: str | None = None) -> dict[str, Any]:
    """Create a derived, minimized review report from one live scenario read."""
    scenario, response_shape = unwrap_scenario(detail)
    blueprint, blueprint_state = decode_blueprint(scenario)
    modules = find_modules(blueprint)
    findings = reported_findings(detail, scenario, response_shape)
    limitations: list[str] = []
    if response_shape in {"unsupported-response", "unrecognized-object"}:
        findings.append(
            {
                "code": "RESPONSE_NOT_EVALUABLE",
                "severity": "warning",
                "classification": "not_evaluable",
                "confidence": "high",
                "evidence_path": "$",
                "summary": "The official CLI response did not match a recognized scenario response shape.",
                "recommendation": "Re-read the scenario through Make MCP or the Make UI before planning a change.",
            }
        )
        limitations.append("The response envelope could not be normalized as a scenario.")
    elif blueprint_state != "parsed-json" and blueprint_state != "structured":
        findings.append(
            {
                "code": "BLUEPRINT_NOT_EVALUABLE",
                "severity": "warning",
                "classification": "not_evaluable",
                "confidence": "high",
                "evidence_path": "$.blueprint",
                "summary": "A parseable scenario blueprint was not available in the official CLI response.",
                "recommendation": "Retrieve current scenario detail through Make MCP or the Make UI before planning a configuration change.",
            }
        )
        limitations.append("Blueprint structure could not be evaluated.")
    elif not modules:
        findings.append(
            {
                "code": "BLUEPRINT_MODULE_STRUCTURE_NEEDS_VALIDATION",
                "severity": "warning",
                "classification": "needs_validation",
                "confidence": "medium",
                "evidence_path": "$.blueprint..module",
                "summary": "The available blueprint did not expose recognizable module references.",
                "recommendation": "Validate the returned blueprint shape and module configuration through live MCP schema discovery.",
            }
        )
        limitations.append("No recognized module-reference path was present in the parsed blueprint.")
    findings.append(
        {
            "code": "ERROR_HANDLING_NEEDS_VALIDATION",
            "severity": "warning",
            "classification": "needs_validation",
            "confidence": "low",
            "evidence_path": None,
            "summary": "Error and incomplete-execution behavior requires a live configuration and execution review.",
            "recommendation": "Inspect error routes, incomplete-execution settings, and one controlled execution before declaring the scenario reliable.",
        }
    )
    active = scenario.get("isActive", scenario.get("active"))
    if active is True:
        findings.append(
            {
                "code": "ACTIVE_SCENARIO_CHANGE_CONTROL",
                "severity": "info",
                "classification": "confirmed",
                "confidence": "high",
                "evidence_path": "$.isActive",
                "summary": "The selected scenario is active.",
                "recommendation": "Use a change plan, controlled test, rollback path, and explicit approval before any update.",
            }
        )
    return {
        "schema_version": 2,
        "status": "read-only-review",
        "source": {
            "control_plane": "official make-cli",
            "command": "scenarios get",
            "official_cli_version": official_cli_version or "not-recorded",
        },
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "scenario_id": scenario.get("id"),
        "active": active,
        "input_shape": {
            "response": response_shape,
            "blueprint": blueprint_state,
            "assessment": "evaluable" if response_shape in {"scenario-envelope", "direct-scenario"} and blueprint_state in {"parsed-json", "structured"} else "not_evaluable",
            "recognized_module_evidence_path": "$.blueprint..module" if modules else None,
        },
        "derived_facts": {"module_count": len(modules)},
        "findings": findings,
        "limitations": limitations + [
            "No execution history, module configuration, or live MCP schema was read by this review.",
            "A read-only structural review cannot establish runtime reliability.",
        ],
        "recommended_actions": [
            {"action": "discover_live_schema", "control_plane": "Make MCP", "side_effects": "read-only"},
            {"action": "inspect_relevant_execution", "control_plane": "official make-cli or Make MCP", "side_effects": "read-only"},
            {"action": "confirm_official_cli_capability_if_mcp_is_unavailable", "control_plane": "official make-cli", "side_effects": "read-only help/inspection until the user explicitly approves a supported command"},
            {"action": "prepare_change_plan", "control_plane": "make-skills", "side_effects": "local file only"},
        ],
        "safety_note": "This minimized report omits the raw blueprint, mappings, URLs, connection identifiers, payloads, and raw error data. It does not authorize edits, runs, or activation.",
    }


def write_scenario_review(directory: Path, review: dict[str, Any], say: Output) -> Path:
    ensure_private_directory(directory)
    scenario_id = safe_filename_component(review.get("scenario_id"))
    path = directory / f"scenario-review-{scenario_id}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    write_private_text(path, json.dumps(review, ensure_ascii=False, indent=2) + "\n")
    say(f"Saved derived review report: {path}")
    return path


def classify_change_request(request: str) -> str:
    words = request.casefold()
    if any(word in words for word in ("error", "fail", "debug", "troubleshoot", "fix")):
        return "troubleshoot"
    if any(word in words for word in ("document", "docs", "explain", "runbook")):
        return "document"
    if any(word in words for word in ("new", "expand", "add", "build")):
        return "build-or-expand"
    return "change-or-adapt"


def write_change_plan(directory: Path, review: dict[str, Any], request: str, say: Output) -> Path:
    """Persist a local, reviewable intent; it is never a Make write instruction."""
    ensure_private_directory(directory)
    sanitized_request = sanitize(request)
    plan = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "proposed",
        "scenario_id": review.get("scenario_id"),
        "assistance_mode": classify_change_request(sanitized_request),
        "requested_change": sanitized_request,
        "review_finding_codes": [finding["code"] for finding in review.get("findings", []) if isinstance(finding, dict) and finding.get("code")],
        "required_next_steps": [
            "Use Make MCP to discover exact live module schemas, options, connections, and current scenario state.",
            "If MCP does not expose the required operation, verify the exact supported official make-cli command and its current documentation before proposing it; do not invent a raw API workaround.",
            "Present a minimal change blueprint, side effects, rollback path, and controlled test before any official make-cli write.",
            "Keep activation unchanged unless the user explicitly approves it after testing.",
        ],
        "safety_note": "This independent community companion's local plan is not a scenario blueprint, a warranty, or authorization to edit, run, or activate a scenario.",
    }
    scenario_id = safe_filename_component(review.get("scenario_id"))
    path = directory / f"scenario-change-plan-{scenario_id}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    write_private_text(path, json.dumps(plan, ensure_ascii=False, indent=2) + "\n")
    say(f"Saved local {plan['assistance_mode']} plan: {path}")
    return path


def manage_personal_learning(review: dict[str, Any], learner: PersonalLearningStore | None, ask: Input, say: Output) -> None:
    if not learner:
        return
    candidate_id = learner.record_review(review)
    say(f"Updated private learning candidate {candidate_id} in {learner.directory}; nothing was written to GitHub.")
    if ask("Has a safe change already been implemented and verified for these findings? [y/N] ").strip().casefold() in {"y", "yes"}:
        lesson_id = learner.record_verified_resolution(review)
        say(f"Updated verified private personal skill lesson {lesson_id}: {learner.skill_path}")


def review_scenarios(
    team_id: Any,
    binary: str,
    reviews_directory: Path,
    changes_directory: Path,
    learner: PersonalLearningStore | None,
    ask: Input,
    say: Output,
) -> None:
    scenarios = list_items(run_json(["scenarios", "list", "--team-id", str(team_id)], binary), ("scenarios", "data"))
    official_cli_version = run(["--version"], binary).stdout.strip()
    say(f"{len(scenarios)} scenario(s) returned for team {team_id}.")
    while scenarios:
        selected = choose(scenarios, "scenario", ask, say, allow_id=True)
        if not selected:
            return
        scenario_id = selected.get("id")
        try:
            detail = run_json(["scenarios", "get", str(scenario_id)], binary)
        except OfficialCliError as exc:
            say(f"Could not read scenario {scenario_id}: {exc}")
            if ask("Try another scenario from this team? [y/N] ").strip().casefold() in {"y", "yes"}:
                continue
            return
        review = build_scenario_review(detail, official_cli_version)
        say(f"\nReview: {review['scenario_id']} ({selected.get('name', 'selected scenario')})")
        say(f"  Active: {review['active']}; derived module count: {review['derived_facts']['module_count']}")
        error_count = sum(1 for finding in review["findings"] if finding["severity"] == "error")
        warning_count = sum(1 for finding in review["findings"] if finding["severity"] == "warning")
        say(f"  Found {len(review['findings'])} review finding(s): {error_count} potential error(s), {warning_count} warning(s).")
        for finding in review["findings"]:
            say(f"  [{finding['severity'].upper()} / {finding['classification']}] {finding['code']}: {finding['summary']}")
        write_scenario_review(reviews_directory, review, say)
        request = ask("What would you like to change, adapt, fix, expand, troubleshoot, or document? (Enter to skip): ").strip()
        if request:
            write_change_plan(changes_directory, review, request, say)
        else:
            say("No change request was recorded.")
        manage_personal_learning(review, learner, ask, say)
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
            "If MCP cannot perform a needed operation, confirm that the official make-cli supports the exact command before proposing an explicitly approved fallback.",
            "Define an idempotency key, error route, controlled test event, and inactive-by-default activation plan.",
            "Present the discovered blueprint for review before calling an official make-cli write command."
        ],
        "safety_note": "This independent community companion file is a local design handoff, not a Make scenario blueprint or warranty. It is not authorization to create or activate a scenario."
    }
    ensure_private_directory(directory)
    path = directory / f"make-scenario-plan-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    write_private_text(path, json.dumps(plan, ensure_ascii=False, indent=2) + "\n")
    say(f"Created local design handoff: {path}")
    return path


def run_wizard(
    executable: str | None = None,
    plans_directory: Path | None = None,
    reviews_directory: Path | None = None,
    changes_directory: Path | None = None,
    personal_directory: Path | None = None,
    personal_learning: bool | None = None,
    ask: Input = input,
    say: Output = print,
) -> None:
    say(COMMUNITY_NOTICE)
    plans_directory = plans_directory or default_artifact_directory("plans")
    reviews_directory = reviews_directory or default_artifact_directory("reviews")
    changes_directory = changes_directory or default_artifact_directory("change-plans")
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
        if exc.reason == "authentication":
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
    if personal_learning is None:
        location = personal_directory or default_directory()
        personal_learning = ask(
            f"Enable continuous private personal learning at {location}? It stores sanitized generic findings only and never writes GitHub. [y/N] "
        ).strip().casefold() in {"y", "yes"}
    learner = PersonalLearningStore(personal_directory) if personal_learning else None
    if learner:
        say(f"Private learning enabled at {learner.directory}. Only verified lessons become personal guidance.")

    while True:
        say("\nChoose an action: 1) review one scenario  2) team-wide enhancement prompts  3) new scenario design handoff  4) exit")
        action = ask("Action [1-4]: ").strip()
        if action == "1":
            review_scenarios(team_id, binary, reviews_directory, changes_directory, learner, ask, say)
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
