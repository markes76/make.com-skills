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

For a single exact scenario ID without the interactive menu, use:

```bash
make-skills review 1905530 --json
```

It reads only the selected scenario and emits a minimized report. Add `--save` to create a private local report under `~/.make-com-skills/reviews/` by default (or pass `--reviews-dir`); it never edits, runs, or activates Make resources.

## npm / npx bridge

After the maintainer completes the one-time public npm publish, users can invoke the packaged bridge with:

```bash
npx --yes @markesai/make-com-skills@latest wizard
```

or install it globally:

```bash
npm install --global @markesai/make-com-skills
make-com-skills make-cli install
make-com-skills doctor
make-com-skills notifications enable
make-com-skills wizard
```

The bridge needs Node 18+ and Python 3, bundles this companion, and delegates Make API work to the official `make-cli`. `make-cli install` is an explicit, confirmation-gated download from Make's official GitHub release and verifies a pinned SHA-256 before writing only to the user-local tools directory. npm installation itself never downloads the official CLI, changes `PATH`, or saves credentials. Update checking is opt-in and notification-only; it never installs a package without an explicit user command. The exact publication and security setup is documented in [NPM release](NPM_RELEASE.md).

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
