# npm/npx Release and Update Model

The npm distribution is a thin, zero-dependency Node bridge around the bundled Python companion. It does not reimplement Make's API. The companion continues to call the official `make-cli`, and an MCP-capable agent remains the schema-aware control plane.

## End-user experience

After the first public npm publication, users can run the newest released companion without a global install:

```bash
npx --yes @markesai/make-com-skills@latest wizard
```

For a reusable global command:

```bash
npm install --global @markesai/make-com-skills
make-com-skills make-cli install
make-com-skills wizard
make-com-skills update
```

`update` makes a read-only request to the npm registry, compares versions, and prints an install command only when a newer version exists. It never installs, updates, or runs a package by itself. Users can explicitly opt into a once-per-day notification on later `doctor` or `wizard` runs with `make-com-skills notifications enable`; disable it with `make-com-skills notifications disable`.

`npx ...@latest` is the simplest choice for occasional use: it resolves the current `latest` release when invoked. The npx bridge needs Node 18+ and Python 3 because it bundles and launches the Python companion. For a supported desktop platform, `make-com-skills make-cli install` explicitly displays and confirms the pinned official Make CLI release, verifies its SHA-256, and writes it to user-local storage. It does not run during npm install, alter `PATH`, or save credentials; the official CLI's own `login` flow remains responsible for authentication.

## What a release updates

Each accepted public knowledge change is reviewed in Git, validated, assigned a semantic version in `VERSION`, and released as a GitHub Release/tag. The `publish-npm.yml` workflow tests the Python companion and npm bridge, then publishes that exact version only through the protected `npm-publish` environment. The npm package’s provenance links it to this public GitHub repository and release workflow.

An update delivers public, version-controlled guidance and code only. It does not include or upload a user’s scenarios, blueprints, plans, private learning overlay, API key, official CLI credentials, or execution data.

## Maintainer release skill

When this repository is opened as the project root in Codex, use the local `$make-com-skills-npm-publish` skill for a routine publication, verification-only workflow run, or release failure triage. It applies only to `@markesai/make-com-skills` in this repository and preserves the protected GitHub Actions/OIDC path. This document remains the portable runbook for maintainers using another tool.

## One-time maintainer setup

The intended public package is `@markesai/make-com-skills`. Before the first release, the maintainer must confirm that `npm whoami` reports the `markesai` publishing account; a registry `404` only proves that no public package can currently be read, not that the name is reservable.

1. Enable npm two-factor authentication for the `markesai` publishing account and confirm `npm whoami` reports `markesai`.
2. From a clean, validated checkout, make the initial public publish using npm’s interactive authentication and `npm publish --access public` from `npm/`. This establishes the package record; do not paste an npm token into this repository or GitHub Actions.
3. Configure npm trusted publishing for `markes76/make.com-skills` and the exact workflow filename `publish-npm.yml`. npm’s current CLI can configure the same relationship with a command similar to:

   ```bash
   npm trust github @markesai/make-com-skills \
     --repo markes76/make.com-skills \
     --file publish-npm.yml \
     --environment npm-publish \
     --allow-publish
   ```

4. Create the GitHub `npm-publish` environment and require maintainer approval. Protect release tags and only create a release after its tests pass.
5. After trusted publishing succeeds once, remove/restrict any legacy npm publish token. The repository workflow uses short-lived GitHub OIDC credentials, not an `NPM_TOKEN` secret.

Current npm trusted publishing requires a recent npm/Node runtime and GitHub-hosted Actions runner. See [npm’s trusted publishing documentation](https://docs.npmjs.com/trusted-publishers/) for current setup requirements and [npm’s npx documentation](https://docs.npmjs.com/cli/commands/npx/) for invocation behavior.

## Normal release checklist (after bootstrap)

1. Review public-source watch candidates and merge only evidence-backed guidance changes.
2. Confirm the working tree is clean and that the intended version is not already in the registry. Update `VERSION`, Python package metadata, `plugin.json`, and `npm/package.json` together; use `python3 scripts/sync_npm_version.py --write` only after reviewing the version change, then run `python3 scripts/sync_npm_version.py --check`.
3. Run `python3 scripts/validate_project.py`, `python3 scripts/validate_evaluations.py`, `PYTHONPATH=src python3 -m unittest discover -s tests -v`, `npm --prefix npm test`, and `(cd npm && npm pack --dry-run --json)`.
4. Commit and push the validated release commit. Create GitHub Release/tag `v<version>` on that exact commit. The protected workflow validates the tag/version relationship and asks the configured GitHub environment for approval before publishing.
5. The `npm-publish` environment must keep its reviewer gate and allow a **Tag** deployment rule matching `v*`. A Branch rule with the same pattern does not allow a tag-triggered release. Do not remove protection or enable a bypass to ship a release.
6. After GitHub Actions succeeds, verify `npm view @markesai/make-com-skills version dist-tags --json` and `npx --yes @markesai/make-com-skills@latest --help`. If metadata is not immediately public, inspect the dist-tags and allow npm's scanning/propagation time before retrying.
7. Publish concise release notes. Existing global users see the next opt-in notification; npx users select the new `latest` version when they invoke it.

## Recovery and verification-only runs

For a verification-only manual run, dispatch `publish-npm.yml` with `publish` left `false`; its publish job does not run. GitHub still requires the `release_tag` form field, but the workflow ignores it in this mode; supply an existing tag as a clear test label. For an approved recovery publication, dispatch from the exact existing `v<version>` tag with `publish` set to `true` and `release_tag` set to that tag. The workflow verifies that the selected ref, tag, and `VERSION` resolve to the same release commit.

If a publish run fails, inspect the workflow logs and registry state before retrying. Do not run local `npm publish`, add `NPM_TOKEN`, force-update a release tag, or republish a version that might already exist. The normal workflow uses short-lived GitHub OIDC credentials and the `npm-publish` protection gate.

Never mutate an existing npm version. Publish a new version, then move only the `latest` dist-tag through the reviewed release workflow.
