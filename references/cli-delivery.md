# Official Make CLI Extension Plan

The official [`make-cli`](https://github.com/integromat/make-cli) is the API runtime. This project deliberately does **not** fork, reimplement, or shadow it. The installed AI skill is the guided interface; `make-skills` is an additive terminal companion that calls the installed official binary.

## Boundary

- `make-cli`: authenticated Make API commands, generated from Make's supported API surface.
- `make-skills`: official-CLI authentication and read-only evidence handoffs, plus explicit local learning storage.
- Make MCP: preferred live schema discovery when it is available in the agent client.

## Companion command policy

- `make-skills doctor` calls only `make-cli --version` and `make-cli users me`.
- `make-skills wizard` is a legacy account/scenario-read handoff for environments without an AI client. It can invoke the official `make-cli login` wizard only after the user chooses that step.
- “Create a scenario” produces a local, reviewable design handoff. It never fabricates a Make blueprint or creates/activates a scenario from a vague request.
- Future write helpers must call the official binary, default to a dry-run/plan, name side effects, require explicit confirmation, and preserve the root skill’s inactive-by-default rule.

## Extending safely

Add a companion command only when the official CLI exposes the needed operation and an evaluation proves the user-facing guardrails. Do not accept an API key as a command-line argument; use official CLI login or environment variables and rely on the official CLI's credential storage. Never add tokens, webhook URLs, raw execution data, or customer data to package configuration, candidate lessons, or test fixtures.
