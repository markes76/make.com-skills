# Make.com Skills

An open, portable Make.com skill pack for designing, building, testing, debugging, and operating reliable [Make](https://www.make.com/) automations. Its canonical router is `make-automation-guru`; it supports the Make MCP connector when available and provides a disciplined fallback design workflow when MCP cannot answer or perform an operation.

It is an instruction package and companion wizard—not a replacement for Make authorization, module schemas, connections, or user approval. The official [`make-cli`](https://github.com/integromat/make-cli) remains the API runtime; this repository adds guidance, review, planning, and governed learning on top.

## What it provides

- Schema-first Make MCP workflows: discover the exact app/module and inspect its fields before building.
- Production automation architecture: webhooks, schedules, routing, arrays, idempotency, state, retries, rate limits, error recovery, and observability.
- Safe scenario lifecycle guidance: create inactive, test with controlled input, inspect executions, then activate only on request.
- Explicit custom-app and API/CLI boundaries, so agents do not pretend an MCP scenario tool can publish a Make app.
- A 4,422-document official-source index, generated from Make’s public Apps, Help, and Developer Hub sitemaps. The index contains titles, URLs, source IDs, and hashes—never copied article bodies.
- Evaluation scenarios, MCP capability-log discipline, and a reproducible release builder so the guidance can mature without turning anecdotes into facts.
- `make-skills`, an installable companion that checks the official CLI, guides secure authentication, reviews scenarios, produces conservative enhancement prompts, and creates safe local design handoffs for new scenarios.

## Install the companion wizard

### Prerequisites

- Python 3.9 or newer.
- Make's official `make-cli`, authenticated through its own secure `make-cli login` flow or its documented environment variables.
- A Make API token scoped for the reads you intend to perform. The wizard needs only read scope for onboarding and review.

### Start from a GitHub clone or release zip

After cloning/downloading this repository, run one command:

```bash
python3 scripts/start_wizard.py wizard
```

It performs the prerequisite/connection journey interactively. To check setup without starting the menu:

```bash
python3 scripts/start_wizard.py doctor
```

### Install as a reusable terminal command

Install Make's official `make-cli` first, then install this package from GitHub:

```bash
python3 -m pip install --user "git+https://github.com/markes76/make.com-skills.git"
python3 -m make_skills wizard
```

If your Python scripts directory is on `PATH`, the equivalent short command is `make-skills wizard`.

If the official binary is not on `PATH`, provide its location without copying it into this repository:

```bash
make-skills --make-cli /path/to/make-cli wizard
```

The wizard invokes the official CLI's own login flow when needed, then starts read-only. Scenario review asks for the displayed number or exact scenario ID, retrieves that one scenario, and saves a derived report without storing its raw blueprint. It can also generate a local design handoff, but it never creates or activates a Make scenario from a vague request.

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

When MCP cannot support an operation, use the official Make CLI as the authenticated API runtime and use this package as the guardrail layer. See [official CLI companion](references/official-cli.md) and [extension plan](references/cli-delivery.md).

## Source index

Run the following only with a local copy of the user-authorized corpus:

```bash
python3 scripts/build_source_index.py /path/to/make_public_docs.jsonl
```

This refreshes `sources/make-docs-index.json`. See [sources/README.md](sources/README.md) for scope and provenance.

## Contributing

Contributions should improve decision quality, not merely restate vendor documentation. Please read [CONTRIBUTING.md](CONTRIBUTING.md), [development guidance](docs/DEVELOPMENT.md), and keep examples generic, secret-free, and safe by default.

## Build a portable release

```bash
python3 scripts/build_release.py
```

This creates a clean zip under `dist/`, excluding git data, local learning candidates, and any raw corpus.

## License

[MIT](LICENSE)
