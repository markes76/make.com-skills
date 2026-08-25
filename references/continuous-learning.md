# Continuous Learning Governance

“Self-evolving” means automatic detection and drafting of sanitized lessons, followed by human review and validation. It does not mean autonomous modification of production scenarios, credentials, skills, commits, or public documentation.

## Candidate lifecycle

1. After a user-authorized run or postmortem is resolved, the agent may ask to capture a lesson.
2. With explicit `--consent`, `scripts/record_lesson.py` accepts only generic text and an allowlisted official Make documentation URL, then writes a local candidate under `~/.make-com-skills/` (or `MAKE_SKILLS_PUBLIC_CANDIDATES`). It rejects credentials, URLs in prose, personal data, identifiers, unknown fields, and uncertain redactions.
3. A maintainer independently reviews that exact official source or a reproducible safe test, runs project validation, and keeps the candidate private until the normal Git review is ready.
4. `scripts/promote_lesson.py <id> --approve --reviewed-source-url <same-official-url>` creates a narrowly scoped addition to `references/approved-lessons.md` only after source and schema validation.
5. A normal reviewed pull request and CI are the only way that published guidance changes.

Candidates are not loaded by the root skill. Only approved lessons are authoritative.

## Private personal learning

The companion wizard can also maintain a separate, opt-in store under `~/.make-com-skills/` (or `MAKE_SKILLS_PERSONAL_DIR`). It is never inside the Git repository and is never pushed. Each reviewed scenario can add a sanitized generic **candidate** with no scenario name/ID, blueprint, module label, connection identifier, payload, URL, credential, or customer data.

Only after the user confirms that a change was safely implemented and verified does the wizard update `PERSONAL_SKILL.md`. The confirmation is stored as a generic status, not as user-supplied free text. Agents may read its **Verified personal lessons** section as advisory context, but must revalidate against live MCP/official CLI state before acting. The candidates section remains non-authoritative.

## Data policy

Never capture raw request/response headers, credential values, connection configuration, webhook URLs, scenario exports, customer records, payloads, emails, phone numbers, account IDs, scenario names, or free-text verification details. Record only a generalized symptom, categorical operation, root cause, resolution category, and verification status.

Reject a candidate when redaction is uncertain. Prefer an official documentation URL and a controlled reproduction over a detailed production trace.

## Revalidation and decay

Use the candidate schema in [`learning/schemas/candidate.schema.json`](../learning/schemas/candidate.schema.json). Add a source URL and last-verified date when promoting platform-sensitive guidance. Revalidate MCP/API behavior at least every 90 days, security/credential material every 30 days, and conceptual patterns every 180 days. Expired guidance is a prompt to re-check; it is not a license to fabricate a replacement.
