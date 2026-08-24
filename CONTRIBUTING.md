# Contributing

Keep the project portable, factual, and safe to apply in a live Make account.

- Do not commit API keys, connection payloads, webhook URLs, customer data, or execution data.
- Do not copy proprietary/full documentation into the repository. Link to official sources or add an original summary.
- Preserve the discovery-first rule: module names, fields, connections, and schemas must come from Make MCP or an official current source.
- Any example that creates a scenario must keep it inactive by default and name its external side effects.
- Run `python3 scripts/validate_project.py` before submitting changes.
- Add or update a representative scenario evaluation when changing behavioral guidance; see `docs/DEVELOPMENT.md`.
- Record MCP behavior only as reproducible, sanitized capability evidence; do not imply support that has not been observed in the relevant client.
- Refresh the source index only from a user-authorized local corpus; do not add article Markdown to git.
