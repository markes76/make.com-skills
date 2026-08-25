# Companion Package Test Plan and Results

## Plan

### Inventory

- `test_learning.py`: consent and redaction behavior.
- `test_official_cli.py`: official binary bridge, read-only doctor, arbitrary scenario-ID selection, minimized derived review, local design handoff, private-learning redaction, private file permissions, and safe report filenames.
- `test_upstream_sources.py`: upstream watch allowlisting, metadata-only persistence, and safe redirect handling.
- `test_release_boundaries.py`: release/install exclusion of local artifacts and generated npm bundles.
- `npm/test/bridge.test.cjs`: Python discovery, command forwarding, npm update checks, and opt-in notification behavior.

### Unit coverage

- The bridge must invoke the supplied official binary without credentials in arguments.
- `doctor` must call only `--version` and `users me`, and must not print user payload data.
- The wizard's new-scenario path must produce a local design-only handoff with no Make write command.
- A selected scenario must be retrieved by ID and reduced to a derived review report without saving the raw blueprint.
- Private learning must omit scenario identity and redact secrets before it writes candidates or verified personal guidance.
- The public source watch must retain only approved public-source metadata and never automatically edit guidance.
- The npm bridge must remain a thin launcher: it may offer an explicit update command or opt-in notice, but it must never install an update or mutate a Make resource.
- A portable archive and installer must exclude private plans, reviews, local learning, raw corpora, generated npm bundles, and symlinks.
- Public-learning candidates must be generic, source-verified, and reject uncertain private data before a maintainer can promote them.

### End-to-end boundary

The tests use a temporary fake official CLI. Live Make calls are intentionally not part of repository CI because they require a user-owned credential. A user-authorized smoke test is `make-skills doctor`, followed by `make-skills wizard` against the installed official CLI.

## Results

Version 0.4.0 validation completed locally:

```text
Python unit tests: 24 passed
Node bridge tests: 10 passed
Project and evaluation validation: passed
npm pack --dry-run: passed with the bundled Python companion and NOTICE
```

The Python package and packed npm archive are also installed into fresh temporary locations before release. The npm archive is invoked from a hostile working directory containing a fake `make_skills` module to verify that only its isolated bundled companion is used. Live Make API testing remains user-authorized and is deliberately not part of CI.
