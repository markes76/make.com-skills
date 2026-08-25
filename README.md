<p align="center">
  <img src="assets/make-skills-cli-mark.svg" width="132" alt="Make Skills CLI community mark: a terminal prompt and routing nodes" />
</p>

<h1 align="center">Make.com Skills</h1>

<p align="center"><strong>Schema-aware automation guidance, an official-CLI companion, and portable skills for modern agent tools.</strong></p>

<p align="center"><strong>Unofficial community companion · use at your own risk</strong></p>

<p align="center">
  <img src="assets/make-skills-cli-hero.png" alt="Abstract terminal prompt connected to automation routing nodes" />
</p>

An open, portable Make.com skill pack for designing, building, testing, debugging, and operating reliable [Make](https://www.make.com/) automations. Its canonical router is `make-automation-guru`; it supports the Make MCP connector when available and provides a disciplined fallback design workflow when MCP cannot answer or perform an operation.

It is an instruction package and companion wizard—not a replacement for Make authorization, module schemas, connections, or user approval. The official [`make-cli`](https://github.com/integromat/make-cli) remains the API runtime; this repository adds guidance, review, planning, and governed learning on top.

> Community notice: this is independent community software, not an official Make.com package or a replacement for the official CLI. Review every plan and command before approving it; no automation outcome is guaranteed. See [COMMUNITY_NOTICE.md](COMMUNITY_NOTICE.md).

| Use it for | Primary path | Safe fallback |
| --- | --- | --- |
| Live schemas, connections, scenario design, and approved changes | Make MCP in the active agent client | Official CLI capability check + local skill handoff |
| Authenticated account/scenario reads | Official `make-cli` through `make-skills` | Make's documented editor/API path |
| Review, troubleshooting, documentation, and enterprise change plans | `make-skills wizard` / `review` + the skill bundle | Read-only report and a human-approved plan |

## What it provides

- Schema-first Make MCP workflows: discover the exact app/module and inspect its fields before building.
- Production automation architecture: webhooks, schedules, routing, arrays, idempotency, state, retries, rate limits, error recovery, and observability.
- Safe scenario lifecycle guidance: create inactive, test with controlled input, inspect executions, then activate only on request.
- Explicit custom-app and API/CLI boundaries, so agents do not pretend an MCP scenario tool can publish a Make app.
- A 4,422-document official-source index, generated from Make’s public Apps, Help, and Developer Hub sitemaps. The index contains titles, URLs, source IDs, and hashes—never copied article bodies.
- Evaluation scenarios, MCP capability-log discipline, and a reproducible release builder so the guidance can mature without turning anecdotes into facts.
- `make-skills`, an installable companion that checks the official CLI, guides secure authentication, reviews scenarios, produces conservative enhancement prompts, and creates safe local design handoffs for new scenarios.
- A versioned npm/npx bridge that bundles the companion, offers opt-in update notification, and is released through protected npm trusted publishing after its one-time publisher setup.

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

The wizard invokes the official CLI's own login flow when needed, then starts read-only. Scenario review asks for the displayed number or exact scenario ID, retrieves that one scenario, classifies its findings, asks what the user wants to change/adapt/fix/build/document, and saves a derived report plus a reviewable local plan under `~/.make-com-skills/` by default. It can also maintain an explicitly consented, private personal skill there; none of those artifacts are committed or pushed. It never creates or activates a Make scenario from a vague request.

For an exact, non-interactive read-only review:

```bash
make-skills review 1905530 --json
```

Add `--save` only if the minimized local report should be written to the private default `~/.make-com-skills/reviews/` (or to an explicitly selected `--reviews-dir`).

### Run with npx (after the first public npm release)

The public npm package is configured as `@markesai/make-com-skills`. Once the maintainer has completed the initial npm trusted-publisher setup, users can run:

```bash
npx --yes @markesai/make-com-skills@latest wizard
```

or install it globally and opt into update notices:

```bash
npm install --global @markesai/make-com-skills
make-com-skills notifications enable
make-com-skills wizard
```

The bridge detects Python 3, launches the bundled companion, and still uses the separately installed official Make CLI. It never installs an update automatically. See the [npm release and update model](docs/NPM_RELEASE.md) before publishing; until the initial publish completes, use the GitHub clone/Python path above.

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

Use Make MCP first when it is available. The active client may expose live module specifications, connections, scenario state, creation, patching, execution inspection, and webhook learning; discover its actual tools and permissions before relying on any capability.

When MCP cannot support an operation, use the official Make CLI as the authenticated API runtime and use this package as the guardrail layer. See [official CLI companion](references/official-cli.md) and [extension plan](references/cli-delivery.md).

The fallback does not mean “try random API calls.” The agent identifies the missing MCP capability, checks whether the installed official CLI supports the exact action, creates a minimal approval-gated plan from live CLI/MCP data and this skill bundle, and otherwise directs the user to Make's documented editor path. The community companion never takes responsibility for a third-party change simply because it suggested it.

## Source index

Run the following only with a local copy of the user-authorized corpus:

```bash
python3 scripts/build_source_index.py /path/to/make_public_docs.jsonl
```

This refreshes `sources/make-docs-index.json`. See [sources/README.md](sources/README.md) for scope and provenance.

The repository also has a weekly metadata-only watch of a small allowlist of official Make URLs. It opens a GitHub review issue when an upstream signal changes; a maintainer validates the page and ships a normal versioned update only if the guidance actually needs to change. See [the public source watch](docs/UPSTREAM_SOURCE_WATCH.md).

## Contributing

Contributions should improve decision quality, not merely restate vendor documentation. Please read [CONTRIBUTING.md](CONTRIBUTING.md), [development guidance](docs/DEVELOPMENT.md), and keep examples generic, secret-free, and safe by default.

## Build a portable release

```bash
python3 scripts/build_release.py
```

This creates a clean zip under `dist/`, excluding git data, local learning candidates, and any raw corpus.

## License

[MIT](LICENSE)
