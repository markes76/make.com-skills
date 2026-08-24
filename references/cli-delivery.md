# API-key-backed Make CLI Delivery Plan

Begin this phase only after the user provides the required Make API credential and authorizes real API use.

## Credential handling

- Accept the credential through an approved secret/input mechanism, not a command argument or source file.
- Keep it out of terminal output, logs, fixtures, test snapshots, and git.
- Confirm the Make zone, organization/team scope, and the intended API permissions before making a write.
- Provide a `doctor` command that verifies authentication and reports the resolved zone/scope without revealing the token.

## Product shape

Build a typed CLI with a read-only default, `--dry-run` for planned writes, JSON output for automation, and human-readable tables for operators. Use subcommands such as:

- `make-cli doctor`, `teams list`, `apps find`, `modules spec`
- `scenarios list|get|create|patch|activate|deactivate|run`
- `executions list|inspect|module`
- `connections list|create` (secret-safe)
- `apps develop|validate|test|deploy` only after confirming which official API endpoints support custom-app development in the user’s Make zone.

## Delivery milestones

1. Scaffold configuration, credential loading, HTTP client, response/error model, and `doctor`.
2. Implement read-only discovery and scenario inspection with snapshot-based tests.
3. Add guarded scenario creation/patching/running with dry-run and explicit confirmation semantics.
4. Add execution diagnostics and webhook-learning support where the API exposes it.
5. Add custom-app development commands only against documented, authorized endpoints; otherwise provide a local developer-workflow helper rather than pretending deployment is supported.

Use the Make MCP connector as the behavior oracle while building the CLI, but do not depend on MCP at runtime unless the user explicitly wants a wrapper around it.
