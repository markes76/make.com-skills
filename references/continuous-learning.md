# Continuous Learning Governance

“Self-evolving” means automatic detection and drafting of sanitized lessons, followed by human review and validation. It does not mean autonomous modification of production scenarios, credentials, skills, commits, or public documentation.

## Candidate lifecycle

1. After a user-authorized run or postmortem is resolved, the agent may ask to capture a lesson.
2. With explicit `--consent`, `scripts/record_lesson.py` sanitizes the supplied summary and writes a local candidate to `.learning/candidates.jsonl`, which is ignored by git.
3. A maintainer reviews the candidate, checks official sources or a reproducible safe test, and runs project validation.
4. `scripts/promote_lesson.py <id> --approve` creates a narrowly scoped addition to `references/approved-lessons.md`.
5. A normal reviewed pull request and CI are the only way that published guidance changes.

Candidates are not loaded by the root skill. Only approved lessons are authoritative.

## Data policy

Never capture raw request/response headers, credential values, connection configuration, webhook URLs, scenario exports, customer records, payloads, emails, phone numbers, or account IDs. Record a generalized symptom, categorical operation, root cause, resolution, and sanitized verification evidence.

Reject a candidate when redaction is uncertain. Prefer an official documentation URL and a controlled reproduction over a detailed production trace.

## Revalidation and decay

Use the candidate schema in [`learning/schemas/candidate.schema.json`](../learning/schemas/candidate.schema.json). Add a source URL and last-verified date when promoting platform-sensitive guidance. Revalidate MCP/API behavior at least every 90 days, security/credential material every 30 days, and conceptual patterns every 180 days. Expired guidance is a prompt to re-check; it is not a license to fabricate a replacement.
