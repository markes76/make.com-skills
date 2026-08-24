# Learning Loop

The project learns from solved failures without converting production errors into unreviewed instructions.

```text
authorized incident → sanitized candidate → maintainer review → validation + test
                   → approved lesson → reviewed PR → published reference
```

Use `python3 scripts/record_lesson.py --help` to create a local candidate. The script requires explicit consent and redacts common secrets and URL query strings. Do not feed it raw execution exports.

Promotion is explicit: `python3 scripts/promote_lesson.py <candidate-id> --approve`. It changes a local reference file only; it never commits, pushes, merges, activates scenarios, or changes root instructions.

See [continuous learning](../references/continuous-learning.md) for policy and [error playbook](../references/error-playbook.md) for the curated troubleshooting baseline.
