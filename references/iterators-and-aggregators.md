# Iterators, Aggregators, and Data-Shape Boundaries

Read this before splitting an array, collecting bundles, or sending a collection to an app/API.

## Start with a proven shape

1. Inspect a live module schema, a minimized controlled execution, or a learned webhook structure. Identify the exact array path and the fields within each item.
2. Decide whether the next step is **one action per item**, **one action for a group of items**, or **one action for the entire source event**. Do not select modules from their names alone.
3. Define the output contract before mapping: the receiving module may expect individual bundles, a mapped array, a JSON string, or a file/binary object.
4. Test zero, one, and multiple items. Include missing optional fields, an item-level failure, and a retry case in the test plan.

If a mapping panel does not expose an expected field after Parse JSON or a webhook, do not invent a path. Run only the upstream module with controlled, non-sensitive data (or trigger schema learning), then re-inspect the output. Make documents this as the way downstream mapping metadata becomes available. [Iterator troubleshooting](https://help.make.com/iterator)

## Iterator: one array item becomes one bundle

Use an Iterator when every member of a confirmed array must be processed independently: for example, create one line item, upload one attachment, validate one record, or make one request per item.

- Map the precise array field, not a JSON-text lookalike or an object that merely contains an array.
- Place filters as close as possible to the item-level effect; explicitly decide whether an invalid item should be skipped, quarantined, or stop the run.
- Add rate limiting, retry behavior, and a stable per-item idempotency key before a per-item external action.
- Preserve the parent event ID and the item ID where downstream reconciliation needs both.
- Prefer an app's specialized iterator only after confirming it represents the same input array and output shape as the general Iterator.

An Iterator changes cardinality from one bundle containing an array to many bundles. A later action runs once per emitted bundle. [Make Iterator](https://help.make.com/iterator)

## Aggregator: many bundles become one output bundle

Use an aggregator when a downstream action needs a collection or combined artifact: a single bulk API request, one digest, a generated file/archive, or an array-valued destination field.

- Select the **Source Module** deliberately. It defines which part of the route contributes bundles to the aggregation boundary.
- Configure the aggregated fields to carry every value required after the boundary. Earlier bundles and intermediate module outputs are no longer individually available after aggregation unless included in the aggregate.
- For independent source events, use **Group by** only with a stable grouping key. Verify that unrelated parents cannot be combined.
- State empty-input behavior. Decide whether an empty array, no output, or an explicit no-op is correct for the destination.
- Establish a maximum group size and a chunking policy when the destination has payload, record-count, or execution-time limits.

An aggregator receives bundles within one source-module operation and emits a single bundle containing the collected items (or one output per group). [Make Aggregator](https://help.make.com/aggregator)

## Common pipeline patterns

| Intent | Safe shape transition | Essential checks |
| --- | --- | --- |
| Per-record update | source array → Iterator → item action | item ID, parent ID, rate limit, retry dedupe |
| Bulk write | source/search bundles → Aggregator → bulk action | group key, batch cap, payload size, partial-failure plan |
| Produce a digest | item processing → Aggregator → message/file | exact fields aggregated, empty result behavior, recipient approval |
| Transform a list but keep one request | direct array mapping or array functions | destination expects a real array, not JSON text |
| Reuse a collection after a side effect | persist/return the needed fields into aggregate | do not rely on pre-aggregator mapping after the boundary |

## Review and troubleshooting checklist

- Does the observed input actually contain an array at the mapped path?
- Does each item have the identifier needed to make a retry safe?
- Does the aggregator source start at the intended module rather than too early or too late?
- If grouping is enabled, can two distinct parent records share the same key accidentally?
- What happens with zero items, one item, a partial item failure, and a destination-size limit?
- Are fields needed after the aggregator explicitly included in its output?
- Is a per-item action accidentally placed after aggregation, or is an aggregate being sent once per item?

## Agent operating rule

Use live Make MCP schema and controlled execution evidence before proposing exact field paths or module settings. If MCP cannot expose the needed schema, use the official Make CLI only for a supported, read-first capability; otherwise provide a reviewable editor plan. Creating, patching, running, or activating a scenario remains user-approved work.

This guide is original operational guidance informed by publicly documented Make behavior. It does not reproduce Academy lessons, course media, exercises, or answers.
