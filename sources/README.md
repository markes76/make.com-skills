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
