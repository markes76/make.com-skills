# Installation

The repository root is the canonical skill bundle. `SKILL.md` is the router; its linked references are part of the bundle and must remain beside it.

## Safe installer

From a clone, preview an install first:

```bash
python3 scripts/install.py --target codex --scope user
python3 scripts/install.py --target cursor --scope project --project /path/to/project
```

Add `--apply` only after confirming the printed destination. The installer copies files (never symlinks) and refuses replacement unless `--force` is explicit.

## Terminal wizard

`make-skills` is a Python companion package, while `make-cli` is Make's official API CLI. Install the official CLI first using its official release/install guidance, then install this package from GitHub:

```bash
python3 -m pip install --user "git+https://github.com/markes76/make.com-skills.git"
make-skills doctor
make-skills wizard
```

The wizard uses `make-cli login` when authentication is missing. It never receives a token as a command argument and it does not persist a token itself. If `make-cli` is installed outside `PATH`, pass its executable with `make-skills --make-cli /path/to/make-cli wizard` or set `MAKE_SKILLS_MAKE_CLI`.

For a downloaded GitHub clone/release zip, no package install is required before first use:

```bash
python3 scripts/start_wizard.py doctor
python3 scripts/start_wizard.py wizard
```

`doctor` is read-only and checks the official CLI version plus authenticated-user access. The wizard guides the user through login, organization/team selection, scenario review, enhancement prompts, and local design handoff creation.

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

For terminal use, `make-skills doctor` should report an official CLI version and verified authentication. `make-skills wizard` should offer reads and local plan creation only; it must not make a Make write during onboarding.
