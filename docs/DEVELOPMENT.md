# Development and Evidence Policy

## Evaluation-first changes

For any new behavioral claim or specialist reference, add or update at least three evaluations where practical: a normal request, a common failure, and a safety-sensitive or advanced case. An evaluation defines observable behavior; it is not a prompt injection or a source of platform truth.

1. Write the evaluation cases in `evaluations/<topic>/`.
2. Confirm the relevant Make behavior with an official current source or a sanitized live MCP observation.
3. Make the smallest guidance change that addresses the cases.
4. Run `python3 scripts/validate_project.py`, `python3 scripts/validate_evaluations.py`, and the unit tests.
5. Update `docs/MCP_CAPABILITY_LOG.md` when the change depends on client-specific MCP behavior.

## Evidence standard

Use live MCP schema and behavior over memory. Do not commit raw calls, responses, scenario exports, webhook URLs, IDs, connection fields, tokens, or personal data. A capability-log entry should identify the client/connector, date, operation category, sanitized input shape, observed outcome, and a stable official URL where applicable.

If live behavior conflicts with the skill, the live surface wins for that run. Report the difference and create a review-required learning candidate only after the failure is resolved.

## Scope discipline

Keep the router concise and place conditional detail in a focused reference. Do not duplicate large vendor manuals or add a rule because of one anecdote. New scenario examples must name side effects, define an idempotency plan, and remain inactive by default.

The companion package must call the official `make-cli` binary rather than reconstructing Make API requests. Its default actions remain read-only; preserve a clear boundary between a local design handoff and a Make write.
