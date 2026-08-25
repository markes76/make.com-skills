# Official Make CLI Companion

`make-skills` augments the official Make CLI. It never replaces it.

## Install and authenticate

Install Make's supported `make-cli` using the official instructions. npm/npx bridge users on a supported desktop platform may instead run `make-com-skills make-cli install`: it displays the exact official Make release, source URL, checksum, and user-local destination, then downloads only after confirmation. It verifies the archive checksum, does not change `PATH`, and does not run during `npm install`. Then use one of the official authentication paths:

- `make-cli login` is the recommended interactive path and stores credentials in the official CLI configuration.
- For a short-lived shell session, set `MAKE_API_KEY` using a hidden terminal prompt and set `MAKE_ZONE` to a hostname such as `eu1.make.com`.

Do not pass an API key with `--api-key` in shell history, commit it, send it to an agent chat, or put it in a scenario field.

## Use the companion

```bash
make-skills doctor
make-skills wizard
make-skills review <scenario-id> --json
```

The wizard checks the official binary, verifies authentication with a read-only user request, selects an organization and team, then offers:

1. List the selected team's scenarios, choose one by displayed number or scenario ID (including an ID not in the current list), retrieve its current detail, classify confirmed versus needs-validation findings, and save a minimized derived review report.
2. Ask what the user wants to change, adapt, fix, expand, troubleshoot, or document; create a local approval-gated plan that routes to MCP/live-schema work.
3. Generate conservative team-wide enhancement prompts from scenario metadata.
4. Create a local design handoff for a new scenario, ready for MCP/live-schema work.

If API authentication is missing, the wizard offers the official `make-cli login` flow, which guides the user through creating/connecting a Make API key. If the official binary is missing, the npm bridge directs the user to its confirmation-gated `make-cli install` command; other distributions explain the prerequisite and exit without attempting an unsafe platform-specific installation.

The wizard performs no Make write or activation in this version. Its local plan is deliberately an input to a skilled agent or a separately approved official `make-cli` command—not a guessed blueprint.

With explicit consent, the wizard can continuously record sanitized generic review candidates in the user's private personal-learning directory. It updates the local personal skill only after the user confirms a verified resolution; it never changes this repository or GitHub.

`make-skills review <scenario-id> --json` is the non-interactive equivalent for one exact scenario. It performs a single scenario read and returns a minimized, evidence-qualified report. It does not save a file unless `--save` is given and never makes a Make mutation.

## Agent handoff

Claude, ChatGPT, Codex, Cursor, Gemini, and OpenClaw can read the plan file created by the wizard, load `SKILL.md`, then use Make MCP to discover exact modules, connections, options, and live data shapes. If MCP is unavailable, they should identify the required official CLI/API research and return a reviewable design rather than inventing a scenario.

The terminal companion cannot itself turn a local terminal into an MCP client. It provides a safe handoff; the agent client must discover the MCP surface it actually has before proposing or executing a schema-dependent change. For end-to-end governance, use [enterprise operations](enterprise-operations.md).

## MCP-unavailable fallback

If the active MCP surface lacks a required operation, identify the missing operation first. Then use the installed official CLI only if its current help/reference exposes the exact capability. The companion can combine that confirmed CLI capability with this repository's public skill knowledge to build a local, reviewable plan, but it must not invent an API request, derive credentials, or treat an old reference as a live schema.

Only read/help commands are automatic. A supported official CLI mutation requires a shown side-effect/rollback/test plan and explicit user approval for that exact action. If the official CLI also lacks it, direct the user to the documented Make editor path. This project is an independent community companion, not an official Make.com package; see [COMMUNITY_NOTICE.md](../COMMUNITY_NOTICE.md).
