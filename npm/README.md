# Make.com Skills npm bridge

This directory contains a zero-runtime-dependency Node bridge for the Make.com Skills AI skill and Python companion. Its intended public package name is `@markesai/make-com-skills`. A package configuration in Git is not itself a publication: check the npm registry before telling users that a release exists.

> **Unofficial community companion · use at your own risk.** This is not an official Make.com package or the official `make-cli`. Review every proposed command and third-party side effect. See [NOTICE.md](NOTICE.md).

The bridge does not implement Make API operations itself. Its primary job is to install the bundled `skill/` into an AI client; the AI skill carries the conversation and uses MCP as the live control plane. It invokes the Python companion only for official-CLI authentication, minimized read-only reports, legacy non-AI handoffs, and explicit private-learning storage. On supported desktop platforms, the optional `make-cli install` command can fetch a pinned official Make release only after the user reviews and confirms its source, SHA-256, and local destination.

## Local development

From this directory:

```sh
npm run bundle-python
node bin/make-com-skills.js --version
node bin/make-com-skills.js doctor --make-cli /absolute/path/to/make-cli
node bin/make-com-skills.js skill install --target codex
node bin/make-com-skills.js review 1905530 --json --make-cli /absolute/path/to/make-cli
node bin/make-com-skills.js learn --consent --status verified --code GENERIC_CHECK --summary "Use a live check." --recommendation "Revalidate before changes."
node bin/make-com-skills.js make-cli status
node bin/make-com-skills.js make-cli install
node bin/make-com-skills.js update
node bin/make-com-skills.js notifications enable
npm test
```

`npm install ./npm` also runs the local `prepare` hook, which creates the generated `python/make_skills` bundle. The generated bundle is deliberately ignored by Git; `npm pack` runs the same bundle step before it creates a tarball.

The bridge checks `MAKE_SKILLS_PYTHON` first, then checks `python3`, `python`, and the system Python on macOS/Linux; Windows checks `py -3`, then `python3` and `python`. Set `MAKE_SKILLS_MAKE_CLI` or pass `--make-cli` to select the official Make CLI. A CLI installed through `make-cli install` is discovered automatically by this npm bridge; it is stored outside the package and never added to `PATH`.

## Commands and update behavior

Once a public release exists, the intended end-user entry points are:

```sh
npx --yes @markesai/make-com-skills@latest skill install --target codex
npx --yes @markesai/make-com-skills@latest doctor
npx --yes @markesai/make-com-skills@latest review 1905530 --json
npx --yes @markesai/make-com-skills@latest make-cli install
npx --yes @markesai/make-com-skills@latest update
npx --yes @markesai/make-com-skills@latest notifications enable
make-skills-npx wizard
```

Running no command prints AI-first setup rather than opening a terminal wizard. `skill install` copies public skill guidance only and refuses to overwrite existing files unless `--force` is explicit. `update` makes one HTTPS request to the npm registry, displays a version comparison and prints optional install commands. `make-cli install` is the only command that downloads the official CLI: it displays a pinned version, official GitHub source, SHA-256, and local destination, then requires confirmation (or explicit `--yes` in an already-reviewed non-interactive use). No package postinstall hook downloads Make CLI, changes `PATH`, modifies Make resources, or sends scenario data to npm.

### Opt-in update notifications

Update notifications are off by default. Users who want a lightweight update notice can explicitly opt in:

```sh
make-com-skills notifications status
make-com-skills notifications enable
make-com-skills notifications disable
```

`status` does not create a file. `enable` creates a small local preference containing only the opt-in state and last registry-check timestamp; `disable` removes that preference file. The default location is `~/.config/make-com-skills` on macOS/Linux and `%APPDATA%/make-com-skills` on Windows. Set `MAKE_COM_SKILLS_CONFIG_DIR` to override the location, including in managed environments and tests.

After a user enables notifications, `doctor` and `wizard` make at most one registry check every 24 hours. If a newer package exists, the bridge writes a notice to stderr (so `doctor --json` remains valid) with one explicit `npm install --global ...` command. It never installs, downloads, or changes a Make resource automatically. Failed or unavailable registry checks are silent and do not block the command.

## Required release work before publishing

Before users can run the public npx command, maintainers need to:

1. Confirm that `npm whoami` reports the publishing account as `markesai`. A registry `404` does not reserve the name.
2. Complete the one-time trusted-publisher configuration described in [`../docs/NPM_RELEASE.md`](../docs/NPM_RELEASE.md), including the protected `npm-publish` GitHub environment.
3. Publish a versioned tarball that includes `python/make_skills`; do not depend on a parent repository path at runtime.
4. Publish release notes and keep update checks opt-in (for example, users run `make-com-skills update` or select an update check in the wizard). Never silently install an update.

The `prepack` script refreshes `npm/python/make_skills` from the root `src/make_skills` in a repository checkout. In a packed or installed release, the root source is absent and the already-bundled copy remains untouched, so all runtime paths remain relative to the package root.
