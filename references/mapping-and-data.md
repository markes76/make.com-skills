# Mapping and Data in Make

Read this before adding a transform, formula, iterator, aggregator, variable, or custom function to a scenario.

## Establish the actual shape

- A Make scenario processes bundles; a field may be scalar, collection/object, array, binary, or absent. Confirm the observed output through `make_module_spec`, a controlled execution, or learned webhook schema before mapping it.
- Filter for required fields before an action. For optional fields, define the fallback or route explicitly rather than relying on implicit conversion.
- Perform type coercion deliberately. Dates, numbers, booleans, text, and empty values can have different downstream semantics; verify the destination module field type.
- Use Make's current mapping/functions documentation for function syntax and names. Never invent a function name or rely on a remembered signature.

## Arrays and bundles

| Need | Pattern | Design check |
| --- | --- | --- |
| Process every array item independently | Iterator | Confirm per-item idempotency and rate-limit behavior. |
| Send a group as one destination request | Aggregator | State the grouping key, source module, size limit, and empty-group behavior. |
| Keep one event as one record | Map direct fields | Preserve the source event ID/correlation ID. |
| Produce a compact list from fields | Array mapping/functions | Confirm whether the target expects an array, JSON text, or a repeated request. |

An aggregator changes execution shape. Do not put a per-item side effect after it unless the aggregate is intentionally expanded again.

## Variables and state

- Use scenario variables for run-local coordination only when their lifecycle matches the run.
- Use a data store or another durable system for idempotency, cursors, deduplication, and cross-run state. Define retention, contention behavior, and recovery before depending on it.
- Do not put API keys, access tokens, raw personal data, or webhook URLs in variables. Connections and approved secret mechanisms own credentials.

## Transform safety checklist

1. What concrete source bundle/schema proves the input shape?
2. What exact destination field specification proves the output shape?
3. What happens for absent, null, empty, malformed, and oversized input?
4. Does the transform change one bundle into many or many into one?
5. Can a retry duplicate an external effect, and which stable ID prevents it?

For detailed official research, use `scripts/search_sources.py mapping --source help.make.com`, `array`, `iterator`, `aggregator`, or `functions` and open the relevant official result.
