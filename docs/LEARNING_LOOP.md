# Learning Loop

The project learns from solved failures without converting production errors into unreviewed instructions.

```text
authorized incident → sanitized candidate → maintainer review → validation + test
                   → approved lesson → reviewed PR → published reference
```

Use `python3 scripts/record_lesson.py --help` to create a private candidate. It requires explicit consent, a query-free allowlisted official Make documentation URL, and generic text. It rejects rather than redacts credentials, URLs in prose, personal data, resource identifiers, and uncertain source material. Do not feed it raw execution exports.

Promotion is explicit: `python3 scripts/promote_lesson.py <candidate-id> --approve --reviewed-source-url <same-official-url>`. It validates the exact candidate schema and source again, then changes a local reference file only; it never commits, pushes, merges, activates scenarios, or changes root instructions.

See [continuous learning](../references/continuous-learning.md) for policy and [error playbook](../references/error-playbook.md) for the curated troubleshooting baseline.
