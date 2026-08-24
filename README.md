# Make Automation Guru

An open, portable skill for designing, building, testing, debugging, and operating reliable [Make](https://www.make.com/) automations. It supports the Make MCP connector when available and provides a disciplined fallback design workflow when MCP cannot answer or perform an operation.

It is an instruction package—not a replacement for Make authorization, module schemas, connections, or user approval.

## What it provides

- Schema-first Make MCP workflows: discover the exact app/module and inspect its fields before building.
- Production automation architecture: webhooks, schedules, routing, arrays, idempotency, state, retries, rate limits, error recovery, and observability.
- Safe scenario lifecycle guidance: create inactive, test with controlled input, inspect executions, then activate only on request.
- Explicit custom-app and API/CLI boundaries, so agents do not pretend an MCP scenario tool can publish a Make app.
- A 4,422-document official-source index, generated from Make’s public Apps, Help, and Developer Hub sitemaps. The index contains titles, URLs, source IDs, and hashes—never copied article bodies.

## Install / use

Clone this repository, then choose the adapter for your tool.

| Tool | Adapter |
| --- | --- |
| Codex | Run `python3 scripts/install.py --target codex --scope user --apply`, then invoke `$make-automation-guru`. |
| Claude Code | Run `python3 scripts/install.py --target claude --scope project --apply`, or work directly from this repository. |
| Cursor | Run `python3 scripts/install.py --target cursor --scope project --apply`. |
| Gemini CLI | Run `python3 scripts/install.py --target gemini --scope project --apply`. |
| OpenClaw / other agent CLIs | Run `python3 scripts/install.py --target openclaw --scope project --apply`, or copy `AGENTS.md`, `SKILL.md`, and `references/`. |

Install is dry-run by default, copies rather than symlinks, and refuses to overwrite files unless `--force` is supplied. The Cursor, Claude Code, and Gemini adapters follow their current project-instruction conventions: [Cursor Rules](https://docs.cursor.com/context/rules), [Claude Code memory](https://docs.anthropic.com/en/docs/claude-code/memory), and [Gemini CLI context files](https://geminicli.com/docs/cli/gemini-md/).

## Start an automation

Give your agent a concise outcome and constraints, for example:

> Use the Make Automation Guru skill to create an inactive scenario. When a signed webhook event indicates a paid order, deduplicate by order ID, create/update the CRM deal, notify Slack, and route malformed events to a review queue. Show the exact modules and mappings before creating anything.

The skill directs the agent to discover the team, apps, module fields, valid connections, and actual webhook schema rather than making assumptions.

## MCP versus API/CLI

Use Make MCP first when it is available: it provides live module specifications, connections, scenario state, creation, patching, execution inspection, and webhook learning.

When MCP cannot support an operation, use the official documentation index to identify the right Make capability. A future API-key-backed CLI belongs in a separate authenticated phase and must not store a token in source, logs, or command history. See [CLI delivery plan](references/cli-delivery.md).

## Source index

Run the following only with a local copy of the user-authorized corpus:

```bash
python3 scripts/build_source_index.py /path/to/make_public_docs.jsonl
```

This refreshes `sources/make-docs-index.json`. See [sources/README.md](sources/README.md) for scope and provenance.

## Contributing

Contributions should improve decision quality, not merely restate vendor documentation. Please read [CONTRIBUTING.md](CONTRIBUTING.md) and keep examples generic, secret-free, and safe by default.

## License

[MIT](LICENSE)
