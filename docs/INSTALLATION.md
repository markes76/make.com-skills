# Installation

The repository root is the canonical skill bundle. `SKILL.md` is the router; its linked references are part of the bundle and must remain beside it.

## Safe installer

From a clone, preview an install first:

```bash
python3 scripts/install.py --target codex --scope user
python3 scripts/install.py --target cursor --scope project --project /path/to/project
```

Add `--apply` only after confirming the printed destination. The installer copies files (never symlinks) and refuses replacement unless `--force` is explicit.

## AI-first installation

Install the skill into the AI client that will reason about your Make work. The AI carries the conversation, scenario due diligence, review, design, troubleshooting, and explicitly consented personal learning; the terminal does not replace it with a numbered menu.

From the public npm package:

```bash
npm install --global @markesai/make-com-skills
make-com-skills skill install --target codex
```

Replace `codex` with `claude`, `cursor`, `gemini`, `openclaw`, or `agents`. Cursor, Gemini, and generic agents use project scope; pass `--project /path/to/project` when needed. The command refuses to overwrite an existing skill or adapter unless `--force` is explicit.

Restart/open the AI client and ask it to review a named scenario, troubleshoot an error, build a new flow, or document an automation. It should load `SKILL.md` and lead the work in conversation.

## Terminal companion (not the AI wizard)

`make-skills` is a Python companion package, while `make-cli` is Make's official API CLI. Install the official CLI first using its official release/install guidance, then install this package from GitHub:

```bash
python3 -m pip install --user "git+https://github.com/markes76/make.com-skills.git"
make-skills doctor
make-skills doctor
```

The terminal companion uses `make-cli login` when authentication is missing. It never receives a token as a command argument and it does not persist a token itself. If `make-cli` is installed outside `PATH`, pass its executable with `make-skills --make-cli /path/to/make-cli doctor` or set `MAKE_SKILLS_MAKE_CLI`.

For a downloaded GitHub clone/release zip, no package install is required before first use:

```bash
python3 scripts/start_wizard.py doctor
python3 scripts/install.py --target codex --scope user --apply
```

`doctor` is read-only and checks the official CLI version plus authenticated-user access. `wizard` remains a legacy terminal handoff for environments without an AI client; the installed AI skill is the preferred guided interface.

For a single exact scenario ID without the interactive menu, use:

```bash
make-skills review 1905530 --json
```

It reads only the selected scenario and emits a minimized report. Add `--save` to create a private local report under `~/.make-com-skills/reviews/` by default (or pass `--reviews-dir`); it never edits, runs, or activates Make resources.

## npm / npx bridge

After the maintainer completes the one-time public npm publish, users can invoke the packaged bridge with:

```bash
npx --yes @markesai/make-com-skills@latest skill install --target codex
```

or install it globally:

```bash
npm install --global @markesai/make-com-skills
make-com-skills make-cli install
make-com-skills doctor
make-com-skills skill install --target codex
make-com-skills notifications enable
```

The bridge needs Node 18+ and bundles the AI skill plus its Python companion. The terminal companion delegates Make API reads to the official `make-cli`; the AI client performs the guided reasoning and uses Make MCP first where available. `make-cli install` is an explicit, confirmation-gated download from Make's official GitHub release and verifies a pinned SHA-256 before writing only to the user-local tools directory. npm installation itself never downloads the official CLI, changes `PATH`, or saves credentials. Update checking is opt-in and notification-only; it never installs a package without an explicit user command. The exact publication and security setup is documented in [NPM release](NPM_RELEASE.md).

| Target | User scope | Project scope |
| --- | --- | --- |
| Codex | `~/.codex/skills/make-automation-guru/` | `.codex/skills/make-automation-guru/` |
| Claude Code | `~/.claude/skills/make-automation-guru/` | `.claude/skills/make-automation-guru/` |
| Cursor | Not installed globally | `.agents/skills/make-automation-guru/` plus a thin `.cursor/rules/` adapter |
| Gemini CLI | Not installed globally | `.agents/skills/make-automation-guru/` plus a root `GEMINI.md` import adapter |
| OpenClaw | `~/.openclaw/skills/make-automation-guru/` | `.agents/skills/make-automation-guru/` |

Do not use `--force` against an existing project-level `GEMINI.md` without first merging its contents manually: it may contain the project's own instructions.

## Manual install

Copy the whole repository to the target tool's skill directory. For an agent that supports only project instructions, retain `AGENTS.md`, `SKILL.md`, `references/`, `scripts/`, `sources/`, and `evaluations/` together, then point its instruction file at `SKILL.md`.

## Verify

Ask the agent to read `SKILL.md`, then request a **design-only** Make scenario. A correct response declares capabilities, asks for or discovers live schema, shows an inactive blueprint, and does not invent modules or credentials.

For terminal use, `make-skills doctor` should report an official CLI version and verified authentication. `make-skills wizard`, if used in a non-AI environment, offers reads and local plan creation only; it must not make a Make write during onboarding.
