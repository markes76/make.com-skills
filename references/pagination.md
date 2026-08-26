# Pagination Patterns for Make

Use this reference when a Make scenario, HTTP request, or reusable custom-app module must retrieve more than one page of an upstream API. This is a design and review aid, not permission to make API calls or change a scenario.

## Establish the contract before choosing modules

Read the upstream API's current pagination documentation and make one controlled, non-sensitive first request. Record only the information needed to reason about the flow:

- request method and stable endpoint;
- page size/limit, server maximum, indexing convention (zero- or one-based), and required sort order;
- response item array path and the unique record identifier used for duplicate detection;
- exactly one continuation model: `totalPages`/`totalCount`, `offset`, cursor/token, next-page URL, `hasMore`, or an empty-page contract;
- termination behavior, rate limits, and whether the data can change while pages are being read.

Do not infer a field path, continuation value, or page numbering rule from an example. Inspect the live Make module schema and controlled response first.

## Select the pagination mechanism

| Upstream contract | Preferred Make design | Critical guardrail |
| --- | --- | --- |
| Total page or total item count is returned | A bounded flow can calculate `ceil(totalCount / pageSize)`; set an explicit maximum approved by the user. | Preserve the first request when it supplies the count; prevent a zero/invalid page size and verify the index base. |
| Page/limit or offset/limit | Advance deterministically: for a one-based page use the repeat index; for offset use `(repeatIndex - 1) * limit` when the API defines that contract. | Keep `limit` stable for the run, use a stable upstream sort/snapshot where available, and cap the run. |
| Opaque cursor/token or next-page URL | Prefer the HTTP module's native response-driven pagination or a custom-app `pagination` directive. Pass the continuation value unchanged. | A Repeater does not advance an opaque token by itself. Stop only on the documented empty/absent continuation signal, plus a safety cap. |
| `hasMore` flag or empty-page stop condition | Use response-driven pagination with the API's documented stop condition. | Detect a repeated cursor/URL or a non-empty duplicate page as a loop/error, not success. |

For a reusable custom-app List/Search module, use Make's request-level `pagination` collection. It can make response-driven follow-up calls using a page, offset, token, or next URL and includes finite request/record/time limits. Do not recreate this stateful behavior in every consuming scenario. See [Make Custom Apps pagination](https://developers.make.com/custom-apps-documentation/component-blocks/api/pagination) and [debugging pagination in list/search modules](https://developers.make.com/custom-apps-documentation/debug-your-app/debugging-of-pagination-in-list-search-modules).

## Scenario review checklist

1. Confirm the first request, its response shape, and the continuation contract with a controlled read/no-side-effect execution.
2. Set a user-approved maximum pages/items/operations and account for the source API's rate limits.
3. Check two or more pages, a final page, and the no-results case. Compare unique IDs across pages for gaps, overlaps, and duplicate processing.
4. Separate page retrieval from per-record work. Use an Iterator only after the response array is known; it converts each array item into a bundle. Choose the aggregator's source as the module that actually fan-outs those bundles. See [Iterator](https://help.make.com/iterator).
5. Before a mutable downstream action, add idempotency/deduplication based on the source record ID. A retry or data shift between pages must not create duplicate side effects.
6. Treat a repeating continuation value, an unexpected empty page, a count mismatch, or an HTTP pagination UI/schema mismatch as a diagnosable failure. Stop, retain only non-sensitive diagnostics, and re-check the live module schema and upstream docs.

## Important boundaries

- A Repeater is appropriate only for a known bounded count or a deliberately capped teaching/batch flow. It is not a general replacement for native pagination.
- A first request is not redundant when it establishes the count, cursor, page size, or response schema needed by later requests.
- Keep page-level and item-level aggregation distinct. An array of items from one page is not evidence that every page was retrieved.
- Course material or community examples may help frame a question, but implement only after confirmation from current official docs and the live schema. Do not copy course blueprints, credentials, or course text into this skill or a public repository.
