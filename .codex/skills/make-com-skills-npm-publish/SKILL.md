---
name: make-com-skills-npm-publish
description: Prepare, validate, publish, or troubleshoot a new @markesai/make-com-skills version from this repository through its protected GitHub Actions workflow. Use only for maintainer-initiated releases of this repository.
---

# Make.com Skills npm publishing

Use this project-local maintainer skill only when work concerns publishing the npm bridge for this repository. It is not guidance for arbitrary npm packages or Make scenarios.

## Preserve the release boundary

- Treat source changes, version changes, Git tags/releases, workflow dispatches, environment approval, and npm publication as separate actions. A request to prepare or review a release does not authorize publishing it.
- Publish routine releases only through `.github/workflows/publish-npm.yml`, using npm trusted publishing with GitHub OIDC. Do not run local `npm publish`, add `NPM_TOKEN`, print credentials, or weaken the protected `npm-publish` environment. The runbook's one-time bootstrap exception for a new package identity is never a recovery path for a tagged release of this package.
- npm versions are immutable. Confirm that the intended version is new before creating a release; never retry by publishing the same version blindly.
- Keep the repository identity distinct from the npm scope: GitHub is `markes76/make.com-skills`; the public package is `@markesai/make-com-skills`.
- Do not include personal scenarios, private learning, credentials, terminal authentication URLs, or local artifacts in source changes or release notes.

## Choose the mode

1. For a release-status question, inspect Git, GitHub Actions, and the registry without changing state.
2. For a verification-only exercise, use the manual `publish-npm.yml` workflow with `publish` left `false`. It runs checks only and must not publish.
3. For a new release, obtain explicit approval for the exact version and external actions, then read [the release runbook](../../../docs/NPM_RELEASE.md) before proceeding.
4. For a failed run, inspect the exact workflow failure first. Do not bypass protections, add an npm token, force-update a tag, or make configuration broad just to unblock a release.

## Routine release outcome

Before any mutation, confirm the Git root, clean worktree, intended semantic version in `VERSION`, current registry state, and the exact release commit. Run the repository validation suite and package dry run described in the runbook.

For an approved publication, commit and push the validated version change, create a GitHub Release named `v<VERSION>` for that exact commit, and let the release event trigger the workflow. The designated human reviewer must approve the `npm-publish` environment; never approve it on the user's behalf or enable an administrative bypass. After the workflow succeeds, verify the registry version and the npm bridge's `--help` command. A short registry-scanning delay can occur; inspect the dist-tags and wait before considering a retry.

## Fragile recovery rules

- The `npm-publish` environment's `v*` deployment policy must be a **Tag** rule, not a Branch rule. Preserve the reviewer gate while correcting this configuration.
- Use `workflow_dispatch` with `publish: true` only as an approved recovery path from the exact existing `v<VERSION>` tag. The workflow verifies that the tag, version, and selected commit agree.
- If a failure is ambiguous after the publish step, check npm first. Never assume no package was created and republish.

## References

Read [npm release and update model](../../../docs/NPM_RELEASE.md) for the exact checks, metadata files, environment configuration, recovery steps, and user update behavior. Read [development policy](../../../docs/DEVELOPMENT.md) for evaluation and source-data rules, and treat the checked-in workflow as the executable source of truth.
