<p align="center">
  <img src="assets/make-skills-cli-mark.svg" width="132" alt="Make Skills CLI community mark: a terminal prompt and routing nodes" />
</p>

<h1 align="center">Make.com Skills</h1>

<p align="center"><strong>AI-first Make automation guidance, an official-CLI companion, and portable skills for modern agent tools.</strong></p>

<p align="center"><strong>Unofficial community companion · use at your own risk</strong></p>

<p align="center">
  <img src="assets/make-skills-cli-hero.png" alt="Abstract terminal prompt connected to automation routing nodes" />
</p>

An open, portable Make.com skill pack for designing, building, testing, debugging, and operating reliable [Make](https://www.make.com/) automations. Its canonical router is `make-automation-guru`; it supports the Make MCP connector when available and provides a disciplined fallback design workflow when MCP cannot answer or perform an operation.

Current release: [`v0.7.1`](https://github.com/markes76/make.com-skills/releases/tag/v0.7.1) / [`@markesai/make-com-skills@0.7.1`](https://www.npmjs.com/package/@markesai/make-com-skills).

It is an AI instruction package with a terminal companion—not a replacement for Make authorization, module schemas, connections, or user approval. The official [`make-cli`](https://github.com/integromat/make-cli) remains the API runtime; this repository adds AI-led guidance, review, planning, and governed learning on top.

> Community notice: this is independent community software, not an official Make.com package or a replacement for the official CLI. Review every plan and command before approving it; no automation outcome is guaranteed. See [COMMUNITY_NOTICE.md](COMMUNITY_NOTICE.md).

| Use it for | Primary path | Safe fallback |
| --- | --- | --- |
| Live schemas, connections, scenario design, and approved changes | Make MCP in the active agent client | Official CLI capability check + local skill handoff |
| Authenticated account/scenario reads | Official `make-cli` through `make-skills` | Make's documented editor/API path |
| Review, troubleshooting, documentation, and enterprise change plans | AI client with `make-automation-guru` installed | Read-only official-CLI report and a human-approved plan |

## What it provides

- Schema-first Make MCP workflows: discover the exact app/module and inspect its fields before building.
- Production automation architecture: webhooks, schedules, routing, arrays, idempotency, state, retries, rate limits, error recovery, and observability.
- Pagination design and review: total/page, offset, token, next-URL, and empty-page contracts; bounded execution, duplicate/gap checks, and safe iterator/aggregator boundaries.
- Safe scenario lifecycle guidance: create inactive, test with controlled input, inspect executions, then activate only on request.
- Explicit custom-app and API/CLI boundaries, so agents do not pretend an MCP scenario tool can publish a Make app.
- A 4,422-document official-source index, generated from Make’s public Apps, Help, and Developer Hub sitemaps. The index contains titles, URLs, source IDs, and hashes—never copied article bodies.
- A small, freshness-gated community-resolution ledger: only public, accepted or explicitly confirmed outcomes that are rechecked against official docs or live schema. It never stores raw posts, screenshots, blueprints, or user data.
- Evaluation scenarios, MCP capability-log discipline, and a reproducible release builder so the guidance can mature without turning anecdotes into facts.
- An AI-first engagement protocol: when a scenario is mentioned, the agent performs live due diligence, distinguishes evidence from hypotheses, then leads review, fix, build, troubleshooting, or documentation work.
- `make-skills`, an installable companion for the official CLI: secure authentication, minimized read-only evidence, and explicitly consented private-learning storage.
- A versioned npm/npx bridge that installs the portable AI skill for Codex, Claude Code, Cursor, Gemini CLI, GitHub Copilot, OpenClaw, and agents that support `AGENTS.md`, then offers opt-in update notification and protected trusted publishing.

## Install the AI skill

The primary interface is your AI client—not a terminal menu. From a GitHub clone, use the portable installer shown below. From npm, install the bridge and place the AI skill into the client you use:

```bash
npm install --global @markesai/make-com-skills
make-com-skills skill install --target codex
```

Choose `--target claude`, `cursor`, `gemini`, `copilot`, `openclaw`, or `agents` as appropriate. Cursor, Gemini, Copilot, and generic-agent installs are project-scoped, so provide `--project /path/to/project` when you are not already in that project. Restart/open the target AI client and ask it to review, troubleshoot, build, or document a Make automation. It will ask the relevant questions and do the due diligence in the conversation.

### Terminal companion prerequisites

- Python 3.9 or newer.
- Make's official `make-cli`, authenticated through its own secure `make-cli login` flow or its documented environment variables.
- A Make API token scoped for the reads you intend to perform. The AI skill asks the official CLI to authenticate only when the MCP control plane is unavailable or insufficient.

### Start from a GitHub clone or release zip

After cloning/downloading this repository, install the skill for your AI client:

```bash
python3 scripts/install.py --target codex --scope user --apply
```

Use the terminal companion only to check the official connection or obtain a minimized read-only report:

```bash
python3 scripts/start_wizard.py doctor
```

### Optional terminal companion

Install Make's official `make-cli` first, then install this package from GitHub:

```bash
python3 -m pip install --user "git+https://github.com/markes76/make.com-skills.git"
python3 -m make_skills doctor
```

If your Python scripts directory is on `PATH`, the equivalent short command is `make-skills doctor`.

If the official binary is not on `PATH`, provide its location without copying it into this repository:

```bash
make-skills --make-cli /path/to/make-cli doctor
```

The legacy terminal `wizard` remains available for non-AI environments, but it is not the primary experience. In an AI client, `SKILL.md` directs the agent to ask the questions, retrieve live evidence, classify findings, and collaborate on the next step. The terminal companion never creates or activates a Make scenario from a vague request.

For an exact, non-interactive read-only review:

```bash
make-skills review 1905530 --json
```

Add `--save` only if the minimized local report should be written to the private default `~/.make-com-skills/reviews/` (or to an explicitly selected `--reviews-dir`).

### Run with npx

The public npm package is `@markesai/make-com-skills`. Run it without a global installation:

```bash
npx --yes @markesai/make-com-skills@latest skill install --target codex
```

or install it globally and opt into update notices:

```bash
npm install --global @markesai/make-com-skills
make-com-skills make-cli install
make-com-skills skill install --target codex
make-com-skills notifications enable
```

The bridge packages the AI skill and only launches the bundled Python companion for `doctor`, read-only `review`, legacy `wizard`, or explicit `learn` storage. `make-cli install` is a separate, confirmed action that downloads a pinned Make release from Make's official GitHub source, verifies its SHA-256, and installs it only in the user's local tools directory; npm installation itself never downloads the official CLI. It never installs an update automatically. See the [npm release and update model](docs/NPM_RELEASE.md) before publishing.

## Install / use

Clone this repository, then choose the adapter for your tool.

| Tool | Adapter |
| --- | --- |
| Codex | Run `python3 scripts/install.py --target codex --scope user --apply`, then invoke `$make-automation-guru`. |
| Claude Code | Run `python3 scripts/install.py --target claude --scope project --apply`, or work directly from this repository. |
| Cursor | Run `python3 scripts/install.py --target cursor --scope project --apply`. |
| Gemini CLI | Run `python3 scripts/install.py --target gemini --scope project --apply`. |
| GitHub Copilot | Run `python3 scripts/install.py --target copilot --scope project --apply`. It adds a project `AGENTS.md` and `.github/copilot-instructions.md` adapter. |
| OpenClaw | Run `python3 scripts/install.py --target openclaw --scope project --apply`. |
| Other coding agents | Run `python3 scripts/install.py --target agents --scope project --apply`. It adds `AGENTS.md` pointing at the portable bundle; verify that the client recognizes `AGENTS.md`/Skill files before relying on it. |
| ChatGPT | A hosted ChatGPT conversation cannot load a local npm skill automatically. Use the Make ChatGPT app/MCP when available, or provide this repository's `SKILL.md` and references as conversation context. |

Install is dry-run by default, copies rather than symlinks, and refuses to overwrite files unless `--force` is supplied. The adapters follow their documented project-instruction conventions: [Cursor Rules](https://docs.cursor.com/context/rules), [Claude Code memory](https://code.claude.com/docs/en/memory), [Gemini CLI context files](https://geminicli.com/docs/cli/gemini-md/), and [GitHub Copilot custom instructions](https://docs.github.com/en/copilot/reference/custom-instructions-support).

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

Recent public Community resolutions are advisory research only and have a 365-day expiry. They are source-linked, must show a confirmed outcome, and are never used in place of Make's current docs or live MCP schema. See [community source provenance](sources/README.md).

## Contributing

Contributions should improve decision quality, not merely restate vendor documentation. Please read [CONTRIBUTING.md](CONTRIBUTING.md), [development guidance](docs/DEVELOPMENT.md), and keep examples generic, secret-free, and safe by default.

## Build a portable release

```bash
python3 scripts/build_release.py
```

This creates a clean zip under `dist/`, excluding git data, local learning candidates, and any raw corpus.

## License

[MIT](LICENSE)
