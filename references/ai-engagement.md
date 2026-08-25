# AI-first Make Engagement

The terminal can authenticate and fetch evidence; the active AI client owns the conversation, due diligence, reasoning, and collaboration. Do not present a numbered terminal wizard as the primary interface.

## Start in the conversation

First establish what the user wants: review, fix/adapt, expand/build, troubleshoot, or document. Ask for only missing facts that materially change the work: intended outcome, target organization/team or private space, the named scenario or app, production side-effect tolerance, and desired success signal.

If the user mentions a scenario:

1. Resolve it narrowly through live Make MCP. If only a name is given and results are ambiguous, show the small matching set and ask the user to select; never choose based only on a title.
2. Read the selected scenario before diagnosing or proposing a change. For an incident, inspect the narrowest relevant execution and failing module after locating it.
3. State what is confirmed by the live response, what needs validation, and what cannot be evaluated. Do not call a generic reliability checklist a defect.
4. Offer the next useful choice in natural language: review only; adapt/fix; expand/build; troubleshoot; or document.
5. For a proposed mutation, discover exact module schemas, options, connections, and current state, then show the minimal change, external effects, idempotency/replay risk, test, rollback, and activation state. Wait for approval before mutating.

For a new automation, use the event contract before selecting any modules: trigger, source data, expected output/effects, data classification, idempotency key, retry/error path, observability, controlled test event, and inactive/active state. Use live app/module discovery; do not infer a module or mapping from documentation or memory.

## Use the right control plane

Use Make MCP first whenever it is available for scope, scenario reads, live schemas, dynamic options, connections, execution inspection, and approved mutations. If MCP is absent or lacks one exact capability, say which capability is missing and use the official Make CLI only after confirming its current supported command. The CLI can produce a minimized evidence handoff:

```sh
make-com-skills review <scenario-id> --json --save
```

Treat that report as a lead, not a complete health verdict. It intentionally omits raw blueprints, mappings, payloads, connection identifiers, and raw provider diagnostics. Do not reconstruct missing data or invent a raw API request.

## Personal learning without public leakage

After a resolution is implemented and verified, ask whether the user wants to retain a generic personal lesson. Only after clear consent, record a generalized code, summary, and preferred check with the local command below. Never include scenario names or IDs, app/module labels, blueprints, payloads, customer data, URLs, credentials, tokens, or raw error text.

```sh
make-com-skills learn --consent --status verified \
  --code ERROR_HANDLING_REQUIRES_LIVE_CHECK \
  --summary "Error handling needed a current execution review." \
  --recommendation "Inspect the relevant execution before changing retry behavior."
```

The resulting `~/.make-com-skills/PERSONAL_SKILL.md` is private advisory context. Read only its verified lessons, revalidate them against the live surface, and never copy it to GitHub, another chat, an issue, or public documentation. A candidate is never an instruction and cannot grant permission for a Make mutation.

## Finish well

Return a concise evidence-based result: scope, observed facts, recommendations, remaining unknowns, and—only if a change is approved—the exact post-change verification. Create a redacted local runbook or plan when useful. This is an unofficial community companion; it never guarantees a third-party automation outcome.
