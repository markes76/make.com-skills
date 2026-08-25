# Source Index and Provenance

`make-docs-index.json` is a metadata-only index built from a user-authorized public Make documentation corpus. It includes each document title, canonical URL, source host, and content hash so agents can locate a relevant official page without redistributing article text.

The corpus used to create the initial index covered 4,422 sitemap-listed documents:

- `apps.make.com`: 3,572
- `help.make.com`: 388
- `developers.make.com`: 462

The raw corpus is intentionally excluded from this repository. Rebuild the index with `python3 scripts/build_source_index.py /path/to/make_public_docs.jsonl` only where you are authorized to collect and retain that content.

When live MCP discovery is unavailable or a capability needs confirmation, search the generated metadata before opening the relevant official page:

```bash
python3 scripts/search_sources.py webhook --source help.make.com
python3 scripts/search_sources.py api token --source developers.make.com
```

## Recent community resolutions

`community-solved-patterns.json` is a deliberately small, metadata-plus-paraphrase ledger of public Make Community resolutions. It is not a documentation corpus or an authority source. Every entry must have an accepted answer or explicit confirmed outcome, be no more than 365 days old when validated, link to the exact public answer, and link to current official Make documentation used for revalidation.

Do not add raw posts, screenshots, blueprints, execution data, credentials, personal data, or a thread that merely offers a suggestion. When an entry expires, remove or revalidate it; do not retain it as timeless guidance.
