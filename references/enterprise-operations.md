# Enterprise Make Operations

Use this reference when the request is to review, improve, build, troubleshoot, document, or govern a Make estate. It keeps the same safety boundary across Codex, Claude, Cursor, Gemini, and a terminal: discover first, propose a minimal plan, then obtain approval for any Make-side effect.

## Choose the control plane

| Need | Preferred control plane | Output before a mutation |
| --- | --- | --- |
| Authenticate, verify access, list/read Make API resources | Official `make-cli` through `make-skills` | Read-only report or local plan |
| Discover live app/module schema, dynamic values, connections, or current scenario structure | Make MCP available in the current agent client | Evidence-qualified design or diagnosis |
| Create, patch, run, activate, or deactivate | The live Make MCP surface if it exposes that exact operation | Scope, exact diff, side effects, controlled test, rollback, and explicit user approval |
| Diagnose execution failure | MCP execution tools; use the official CLI only for supported reads | Failure evidence, affected scope, and proposed minimal repair |
| Produce a runbook or architecture note | Local generated artifact | Redacted operational documentation |

Do not claim that the terminal can invoke an MCP server by itself. The companion creates a local handoff that an MCP-capable agent can use. Tool names, scope model, and mutation capabilities must be discovered in that client at run time.

## When MCP cannot do it

1. Say which required capability is missing from the live MCP surface and what was checked. Do not label it a Make product limitation unless the official source supports that conclusion.
2. Check the currently installed official `make-cli` help/reference for the exact read or mutation command. The community companion may use it as a harness, but must not reconstruct undocumented HTTP requests or guess flags.
3. Use the public skill/reference knowledge to prepare a minimal command plan: required scope, inputs, side effects, idempotency, controlled test, rollback, and activation state. Knowledge informs the plan; live CLI schema/help wins when they differ.
4. Run only read/help commands automatically. Before a supported official CLI mutation, show the exact command intent and request explicit approval. If neither MCP nor the official CLI supports the operation, return a documented manual Make-editor action instead of a workaround.

This repository is an independent community companion, not an official Make.com package. Its plans and suggestions provide no warranty and cannot transfer responsibility for third-party effects. Read [the community notice](../COMMUNITY_NOTICE.md) before using it against production systems.

## Engagement loop

1. **Understand.** State the requested outcome, in-scope team/private space, whether production effects are allowed, and the success signal. Treat vague words such as “fix” or “optimize” as a request for investigation and proposal—not permission to mutate.
2. **Read narrowly.** List only enough to identify the target. Read one named scenario or a small, risk-based sample; do not bulk-export every blueprint or execution.
3. **Classify evidence.** Separate platform-reported errors from `needs_validation` signals and `not_evaluable` input. Do not turn a module name, a keyword, or a missing field into a confirmed defect.
4. **Offer the next useful mode.** Ask whether the user wants to adapt/fix, expand/build, troubleshoot, or document. Capture the request as a local change plan before a Make write.
5. **Design the smallest safe change.** Discover live schemas/options/connections. Show exact affected modules, mappings, routing, idempotency, error path, side effects, controlled test, rollback, and post-change verification.
6. **Change only with approval.** Re-read immediately before an edit, use the current optimistic-concurrency value when the surface provides one, preserve the inactive/active state unless the user explicitly changes it, and never broaden the change after approval.
7. **Verify and document.** Use a controlled test, inspect the intended execution only, record a redacted runbook/change summary, and invite a private learning confirmation only after the resolution is actually verified.

## Mode-specific guidance

### Review

`make-skills review <scenario-id> --json` gives a minimized read-only report. `make-skills wizard` offers the same flow interactively. A report may contain an ID for the local user’s traceability but must never include raw blueprints, mappings, connection identifiers, payloads, URLs, raw error text, or module labels.

The review is a lead, not a health verdict. A structural read cannot prove that recent executions worked. Follow a suspected runtime issue with the narrowest relevant execution read and a current configuration/schema check.

### Adapt or fix

Treat a reported error as evidence to investigate, not a reason to apply a generic retry. Check current configuration against the execution time, identify the narrowest failing module/cycle, discover schema and dynamic option values live, then present a minimal patch. Never retry a potentially non-idempotent effect until the duplicate-risk decision is explicit.

### Expand or build

Start from an event contract: trigger, source data, target effect, data classification, idempotency key, schedule/replay preference, error routing, alerting, test event, and activation state. Use live module specifications before choosing fields or a connection. New scenarios remain inactive until the user approves activation after testing.

For learned-payload webhooks, create only the trigger, collect one representative test payload through the supported learning path, inspect its live schema, and then add downstream mappings. Do not invent a schema from an example.

### Troubleshoot

Inspect execution history narrowly; distinguish a current blueprint from the one that ran when the execution occurred. Inspect the failing module only after locating it in the execution flow. Preserve evidence classifications: a returned error is confirmed; an absence of data or unknown response shape is not evidence of a healthy scenario.

### Document

Write a human-operable runbook with purpose, trigger, owners, data boundaries, preconditions, normal flow, error/retry behavior, alerting, controlled test, rollback, and change history. Redact credentials, webhook URLs, identifiers, and raw payloads. If a required field is unknown, mark it for live discovery rather than guessing.

## Change-control minimum

Before any Make mutation, provide:

- target organization/team/private space and scenario ID;
- the exact intended change and what remains untouched;
- known external effects and duplicate/replay risk;
- current-state/concurrency check and rollback path;
- test data, expected result, and monitoring/alert path;
- activation state before and after;
- explicit user approval for that exact scope.

Use a local plan for review and collaboration. Local plans are not Make blueprints and are not execution authorization.

## Learning and update boundaries

Personal learning is opt-in and stored only in `~/.make-com-skills/`. It keeps generic, sanitized findings and promotes a pattern to private guidance only after the user confirms a safe resolution. It retains neither scenario detail nor free-text verification notes.

Public learning is a separate, version-controlled process based on official Make documentation and reproducible, sanitized evaluations. An upstream change creates a review candidate; it does not silently edit skill guidance, publish a package, or alter a user’s automation. See the public knowledge-update reference when maintaining the repository.
