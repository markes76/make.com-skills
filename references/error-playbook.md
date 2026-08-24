# Make Error Playbook

Classify the failure before retrying. Capture only sanitized summaries and inspect the narrowest live state needed to resolve it.

| Signal | Likely cause | Inspect next | Safe remediation |
| --- | --- | --- | --- |
| 403 or missing scope | Connected Make app grant is incomplete | Tool response and environment scope | Reconnect/reauthorize the Make app; do not hunt for a tool-specific bypass. |
| Module or field validation error | Guessed module name, field path, or data shape | `make_app_find`, `make_module_spec` | Use the exact returned module/path and submit one complete atomic change. |
| Empty dynamic options | Dependency input/context is absent or source has no choices | Module spec and `make_module_options_get` | Set the required dependency context; use opaque option values, never labels. |
| Connection missing or expired | Wrong team connection, removed grant, token expiry | Scenario/module spec and connection status | Ask the user to reauthorize or select a valid connection; do not blind-retry. |
| Patch conflict | Scenario was edited after it was read | Fresh `make_scenario_get` | Rebase the requested minimal edit on fresh state; never force overwrite. |
| Activation refused | A required module configuration is invalid | Scenario issues and module spec | Resolve the issue, revalidate, then ask again before activation. |
| Webhook mappings are absent/wrong | Payload was assumed instead of learned | Trigger learning + trigger inspect | Learn one representative delivery, inspect shape, then patch mappings. |
| Webhook queue grows | Inactive/paused scenario, rate limit, or ordered processing waits | Trigger/scenario state and incomplete execution status | Resolve state or source pressure; do not blame mappings without evidence. |
| Execution not found yet | Run ingestion lag or overly broad filter | Filtered execution list after a short wait | Retry inspection with the same narrow time/status scope. |
| Top-level success but module warning | Error is per-module/cycle | `make_scenario_execution_inspect` | Drill into the reported module/cycle before altering the blueprint. |
| 429 / source rate limit | Burst too high or upstream quota | Error payload and source limit documentation | Lower concurrency/cadence, batch/aggregate, use bounded recovery; avoid immediate retry loops. |
| Partial external side effect | Target system is non-transactional | Target ID and execution ordering | Add idempotency/upsert/compensation before replaying. |
| Current blueprint differs from failed run | Scenario changed after the execution began | `lastEdit` versus execution start time | Treat the failure as historical; reproduce against current state only when safe. |
| Withheld/truncated/confidential value | Privacy or size policy | Tool response metadata | Use a user-approved minimal reproduction; never infer missing data. |

## Diagnostic ladder

1. Identify the exact scenario, execution, and intended behavior.
2. Read execution summary or inspection map.
3. Isolate one failing module/cycle and retrieve only that data.
4. Re-read the current module configuration only after comparing run time to last edit.
5. Make one minimal, fully specified patch and test it with controlled input.
6. If solved, offer a sanitized candidate lesson; never write an unreviewed lesson into the skill.
