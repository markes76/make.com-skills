# Make MCP Operations

Use the connector as a schema-aware control plane. Its available operations, names, and parameters are authoritative; this reference uses the names exposed by the Make ChatGPT app and may need capability-based translation in another client.

## Discovery and scope

| Objective | MCP operation | Decision rule |
| --- | --- | --- |
| Find permitted scope | `make_environment_get` | Call first for scoped work; retain the returned zone, organization ID, and team/private-space ID. |
| Find apps/modules | `make_app_find` | Send the user’s outcome verbatim. Treat returned names and module types as exact. |
| Learn requirements/output | `make_module_spec` | Batch every planned `app:moduleName`; use it to obtain fields, constraints, output shape, webhooks, and valid connections. |
| Resolve dynamic choices | `make_module_options_get` | Call when a module field exposes options that cannot be safely guessed. |
| Inspect/create a connection | `make_connection_get`, `make_connection_create` | Prefer an existing fitting connection. Never expose or paste credential values. Creation needs explicit user authority. |

If the connector does not expose an operation, say so and move to a documented fallback; never approximate a missing write operation. Narrow list results to the requested app, folder, team, status, or time window and do not assume pagination behavior without inspecting the response.

## Scenario lifecycle

| Objective | MCP operation | Guardrail |
| --- | --- | --- |
| Find containers/scenarios | `make_scenario_folder_list`, `make_scenario_list`, `make_scenario_get` | Use the requested team. Read the target before any edit. |
| Create | `make_scenario_create` | Supply only modules/specs discovered above. The connector validates the blueprint; default to inactive. |
| Edit safely | `make_scenario_patch` | Describe only the requested changes. It applies operations atomically and detects stale blueprints; re-read and retry only with fresh state. |
| Enable/disable | `make_scenario_activate`, `make_scenario_deactivate` | Activation must be expressly requested; report the final state. |
| Test | `make_scenario_run` | Use a controlled, non-production input when possible. Explain side effects before running an action scenario. |

Read the current configuration before a targeted config replacement, preserve unrelated settings, and include any dependent repairs in the same validated patch. Do not force a conflicting patch. A generic webhook waits for a real delivery; invoking a scheduled or polling scenario has different input semantics, so inspect the trigger type before testing.

## Debugging and webhook learning

1. Use `make_scenario_execution_list` to locate the relevant execution.
2. Use `make_scenario_execution_get` for a concise result, or `make_scenario_execution_inspect` for the complete flow map and first failure.
3. Use `make_scenario_execution_module_get` only for the affected module’s concrete input/output/error data. Avoid collecting unrelated run data.
4. Fix the minimal defect with `make_scenario_patch`; then repeat the controlled test.

For generic webhooks:

1. Use `make_scenario_trigger_learn`; it captures the next request without running the scenario.
2. Tell the user to send one representative payload to the returned webhook URL.
3. Use `make_scenario_trigger_inspect` to obtain the learned data structure.
4. Patch downstream mappings only after inspecting that structure.

## Build decisions that commonly matter

- Choose instant/webhook for event delivery and polling/scheduling for deliberate scans; do not treat these as interchangeable run modes.
- Apply a filter for a simple guard, an if/else followed by a merge when both outcomes must continue, and a router for distinct paths. Use an iterator for per-item work and an aggregator only when the target needs a grouped payload.
- For dynamic fields or choices, retain the returned opaque value rather than substituting the human label.
- Reconnect the whole authorized Make app for a scope failure; a scenario-level retry cannot add OAuth scope.
- Treat runs as potentially delayed or partially completed. Inspect execution state before resubmitting work, especially after rate limits or non-idempotent side effects.

## Implementation handoff format

Before a state-changing call, present a compact plan containing:

- Scope: organization/team/private space and target folder
- Trigger and schedule/webhook behavior
- Exact modules and why each is needed
- Required connections and their existing/new status
- Input/output contract and key mappings
- Filters/routes, retries/error path, idempotency/state handling
- Test event and expected observable result
- Whether the scenario will remain inactive or be activated

If the user asks only for a design or explanation, stop before mutation and return this plan instead.
