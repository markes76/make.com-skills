# Official Source Metadata Watch

`sources/upstream-manifest.json` is a small allowlist of representative public Make pages. It covers only `developers.make.com`, `apps.make.com`, and `help.make.com`, including official Make CLI, MCP, app-reference, and scenario-lifecycle pages.

The watch is deliberately a change signal, not a crawler and not a source of truth. It never authenticates to Make, invokes Make MCP, runs the Make CLI, accesses scenarios, or writes to Make. It reads and persists only a narrow metadata set: HTTP status, canonical scheme/host/path after an allowlisted HTTPS redirect, ETag, Last-Modified, Content-Length, and Content-Type. Manifest and redirect URLs with credentials, query strings, or fragments are rejected; it never reads or stores page bodies, cookies, authorization headers, credentials, tokens, scenario data, connection data, or customer data.

Run a read-only comparison locally:

```bash
python3 scripts/check_upstream_sources.py --report /tmp/make-upstream-report.json
```

The JSON report labels results as **candidate metadata signals**. A changed ETag, length, redirect, or status can be caused by CDN behavior and does not prove that Make documentation changed. Review the linked official page and the impact on this repository before changing any skill guidance.

After that human review, a maintainer may explicitly accept the current metadata as the new baseline:

```bash
python3 scripts/check_upstream_sources.py --write-state \
  --report /tmp/make-upstream-report.json
git diff -- sources/upstream-source-state.json
```

`--write-state` only replaces the committed metadata baseline atomically. It does not scrape content, edit skill files, commit, push, create pull requests, open issues, use an API key, or mutate Make.

The scheduled GitHub workflow produces the same report as an artifact. If it sees candidate metadata changes, it creates or updates one review-request issue. It never auto-merges guidance, updates the baseline, or creates/changes a Make scenario. The issue is intentionally a reminder for maintainers to inspect public documentation and decide whether a normal reviewed contribution is warranted.
