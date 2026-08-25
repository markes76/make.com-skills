# Companion Package Test Plan and Results

## Plan

### Inventory

- `test_learning.py`: consent and redaction behavior.
- `test_official_cli.py`: official binary bridge, read-only doctor, scenario-ID selection, derived scenario review, and local design handoff.

### Unit coverage

- The bridge must invoke the supplied official binary without credentials in arguments.
- `doctor` must call only `--version` and `users me`, and must not print user payload data.
- The wizard's new-scenario path must produce a local design-only handoff with no Make write command.
- A selected scenario must be retrieved by ID and reduced to a derived review report without saving the raw blueprint.

### End-to-end boundary

The tests use a temporary fake official CLI. Live Make calls are intentionally not part of repository CI because they require a user-owned credential. A user-authorized smoke test is `make-skills doctor`, followed by `make-skills wizard` against the installed official CLI.

## Results

Version 0.3.0 validation completed locally:

```text
Ran 6 tests in under one second
OK
```

The package was also built and installed with macOS's bundled pip, then invoked as `python3 -m make_skills --version`. Live API testing remains user-authorized and is deliberately not part of CI.
