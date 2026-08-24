# Installation

The repository root is the canonical skill bundle. `SKILL.md` is the router; its linked references are part of the bundle and must remain beside it.

## Safe installer

From a clone, preview an install first:

```bash
python3 scripts/install.py --target codex --scope user
python3 scripts/install.py --target cursor --scope project --project /path/to/project
```

Add `--apply` only after confirming the printed destination. The installer copies files (never symlinks) and refuses replacement unless `--force` is explicit.

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
