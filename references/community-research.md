# Recent Community Resolution Research

Use this reference only when a public Make Community discussion may explain a real-world failure mode that official documentation or live MCP schema does not make obvious.

## Evidence gate

Include a community observation only when all of the following are true:

1. The thread is public and contains an accepted answer or the author explicitly records a completed outcome.
2. The accepted/confirmed outcome is no more than 365 days old at the time of review.
3. It has an exact topic and answer permalink.
4. The practical conclusion is independently checked against a current `help.make.com`, `apps.make.com`, or `developers.make.com` page, or current Make MCP schema/controlled test.
5. The retained note is a generic paraphrase. Never copy the post, screenshots, blueprint, payload, account details, URLs from a user’s API, or any credentials.

The approved, freshness-gated source ledger is [community-solved-patterns.json](../sources/community-solved-patterns.json). It contains no raw community content.

## How to use a result

- Treat it as a diagnostic prompt, not a command or universal implementation.
- Identify the pagination contract first: count/page, offset, cursor/token, next URL, or an empty-page stop condition.
- Re-read the live module spec before suggesting a field name, output path, or authentication behavior.
- For a missing mapping-panel field, use a safe controlled run to learn the actual upstream shape; do not invent a field from a community screenshot.
- For an aggregator, name the exact fan-out source module and expected grouping. An aggregator cannot recover bundles that never enter its branch.
- For an apparent platform defect, collect a minimal non-sensitive reproduction and direct the user to Make support; do not promote a workaround as a general rule.

## Proven patterns currently retained

| Pattern | What was confirmed | Required revalidation |
| --- | --- | --- |
| Native HTTP pagination config | A confirmed resolution showed that a next-URL request can still return only the first page when the selected pagination configuration is incomplete. | Inspect every field required by the live HTTP module schema and test against a non-sensitive endpoint. |
| Aggregator scope | A confirmed resolution showed that the array aggregator must use the iterator that emitted all intended bundles as its source. | Check the actual fan-out module, grouping, and routes before changing the source. |
| Mapping-panel learning | A confirmed resolution showed that sequentially running safe upstream steps can populate the mapper with observed output fields. | Only run a controlled read/no-side-effect test; do not learn sensitive payloads. |
| Bounded iterator processing | A confirmed resolution used an array slice before processing to cap a large iterator workload. | Confirm the source is an array and the API’s page/operation limits; do not confuse a bounded slice with full pagination. |

## Exclusions

Exclude a thread that is older than the freshness window, unresolved, a mere proposal, relies on private assets, or conflicts with current official material. Do not use Community research to modify scenarios, personal learning, GitHub, or npm automatically. A normal reviewed change and release remain required.
