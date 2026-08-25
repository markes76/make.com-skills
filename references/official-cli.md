# Official Make CLI Companion

`make-skills` augments the official Make CLI. It never replaces it.

## Install and authenticate

Install Make's supported `make-cli` using the official instructions. Then use one of its approved authentication paths:

- `make-cli login` is the recommended interactive path and stores credentials in the official CLI configuration.
- For a short-lived shell session, set `MAKE_API_KEY` using a hidden terminal prompt and set `MAKE_ZONE` to a hostname such as `eu1.make.com`.

Do not pass an API key with `--api-key` in shell history, commit it, send it to an agent chat, or put it in a scenario field.

## Use the companion

```bash
make-skills doctor
make-skills wizard
```

The wizard checks the official binary, verifies authentication with a read-only user request, selects an organization and team, then offers:

1. Review the selected team's scenarios.
2. Generate conservative enhancement review prompts from scenario metadata.
3. Create a local design handoff for a new scenario, ready for MCP/live-schema work.

The wizard performs no Make write or activation in this version. Its local plan is deliberately an input to a skilled agent or a separately approved official `make-cli` command—not a guessed blueprint.

## Agent handoff

Claude, ChatGPT, Codex, Cursor, Gemini, and OpenClaw can read the plan file created by the wizard, load `SKILL.md`, then use Make MCP to discover exact modules, connections, options, and live data shapes. If MCP is unavailable, they should identify the required official CLI/API research and return a reviewable design rather than inventing a scenario.
