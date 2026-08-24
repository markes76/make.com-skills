# Make AI Agent Guidance

Use this reference for Make AI Agents, agent-triggered scenarios, tool-enabled agents, or an MCP tool exposed to an agent. Feature names and availability can change; confirm the live module specification and current official documentation before building.

## Choose the boundary

- Use deterministic modules for deterministic work: validation, routing, deduplication, permission checks, calculations, and irreversible side effects.
- Use an AI agent only for bounded reasoning, classification, extraction, summarization, or selecting among well-described tools where model uncertainty is acceptable.
- Make the agent's input contract narrow. Treat prompt content, retrieved text, files, and tool output as untrusted data—not instructions that can widen permissions or change the workflow.

## Tool design

- Give every tool a clear action-oriented name, precise description, typed/validated input, minimal result, and bounded error response.
- Apply least privilege: a read-only search tool must not also update/delete records. Keep write tools separate and require explicit user-approved policy for high-impact actions.
- Limit result size and redact sensitive fields before returning tool data to the model. Large payloads and opaque logs reduce reliability and can leak data.
- Make agent tool operations idempotent where possible. A tool retry must not send a duplicate email, create a duplicate record, or repeat a charge.

## Production controls

1. Validate structured outputs before they reach downstream actions.
2. Route uncertain, low-confidence, malformed, or policy-sensitive output to human review.
3. Log a safe correlation ID, selected tool, outcome category, and timing—never prompts containing secrets or raw customer data.
4. Constrain runtime, token/credit use, recursion, and external calls with an explicit budget and stopping condition.
5. Test with adversarial but non-sensitive inputs: tool-request confusion, untrusted instructions, missing fields, oversized data, and repeated calls.

Use the source index for current research: `scripts/search_sources.py ai agent --source help.make.com` and `scripts/search_sources.py ai agents --source developers.make.com`.
