# Automation Architecture for Make

## Choose the trigger deliberately

- Use an instant/webhook trigger when the upstream system can push a complete event and low latency matters. Verify the payload with learning before building mappings.
- Use polling when push is unavailable or a periodic scan is inherently the requirement. Choose the schedule from freshness, source limits, and the consequences of delayed work.
- Avoid mixing an ingestion trigger with unrelated batch remediation in the same scenario; use a separate scheduled scenario for repairs/backfills.

## Model the data flow

Write the contract at each boundary: one bundle or many, required fields, optional fields, source identifier, and downstream side effect. Add filters immediately after the decision that determines whether a bundle should proceed.

- Use an iterator when every array item must run independently through later modules.
- Use an aggregator when a later module needs one combined payload. Specify the grouping key and expected aggregate size.
- Use a filter for a one-way guard, an if/else plus merge when processing must converge, and a router when routes have intentionally different side effects or ownership.
- Make pagination explicit for list/search APIs; do not assume a single page represents the complete result.
- Use module outputs only after `make_module_spec` or a test run shows the actual shape.

## Make side effects idempotent

Duplicate events and retries are normal. Choose one of these patterns before creating an external record:

- Search then create/update using a stable business key.
- Use an upstream event ID as an idempotency key when the target supports it.
- Store completed event IDs or cursors in a data store for a defined retention window.
- Split irrecoverable side effects from retriable work so a rerun cannot repeat a charge, email, or provisioning action.
- Keep a dead-letter/review route for malformed input; include a safe correlation ID and reason, not the entire sensitive payload.

## Error and recovery design

| Failure type | Preferred response |
| --- | --- |
| Transient API/network failure | Bounded retry or incomplete-execution recovery; preserve the original input. |
| Rate limit | Reduce burst/schedule, batch if the module supports it, and honor the source’s retry direction. |
| Validation/data-quality issue | Filter or route to a review queue with the offending ID and reason. |
| Authentication/permission issue | Stop the affected path; repair the connection or scope rather than retrying blindly. |
| Non-repeatable side effect uncertain | Do not replay until idempotency can be established. |

Use error handlers and incomplete-execution settings intentionally. A path that “continues” without recording the failure is normally a data-loss bug.

## Observability

Every production scenario should make it easy to answer: What event was processed? Which module failed? Was a side effect performed? Can it be replayed safely?

- Preserve stable source IDs and target IDs in the run’s relevant outputs/logging path.
- Start debugging with execution inspection, not an unbounded collection of module payloads.
- Keep a controlled test event and a known expected result.
- Revisit schedules, connections, and module options after source API changes.
- Measure backlog, retries, and recovery age. Ordered delivery may intentionally serialize work; do not increase concurrency until ordering requirements are understood.

## Custom Make apps

Use a custom app when an integration will be reused, needs a native module experience, or requires stable typed mappings beyond a one-off HTTP call. Design connections separately from module behavior; expose action/search/polling/instant/responder modules according to API semantics; provide typed interfaces and pagination; use RPCs for dynamic options/fields/samples. Treat a changed output schema as a versioned compatibility change.

The installed Make MCP connector is optimized for connected scenarios. It may not expose custom-app provisioning/deployment operations; do not imply that a scenario tool can publish an app. Use the Make developer workflow or the future API-key-backed CLI phase when the needed API capability is confirmed.
