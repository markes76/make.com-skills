# npm/npx Release and Update Model

The npm distribution is a thin, zero-dependency Node bridge around the bundled Python companion. It does not reimplement Make's API. The companion continues to call the official `make-cli`, and an MCP-capable agent remains the schema-aware control plane.

## End-user experience

After the first public npm publication, users can run the newest released companion without a global install:

```bash
npx --yes @markes76/make-com-skills@latest wizard
```

For a reusable global command:

```bash
npm install --global @markes76/make-com-skills
make-com-skills wizard
make-com-skills update
```

`update` makes a read-only request to the npm registry, compares versions, and prints an install command only when a newer version exists. It never installs, updates, or runs a package by itself. Users can explicitly opt into a once-per-day notification on later `doctor` or `wizard` runs with `make-com-skills notifications enable`; disable it with `make-com-skills notifications disable`.

`npx ...@latest` is the simplest choice for occasional use: it resolves the current `latest` release when invoked. The npx bridge needs Node 18+ and Python 3 because it bundles and launches the Python companion. It still requires the separately installed official Make CLI for authenticated Make reads.

## What a release updates

Each accepted public knowledge change is reviewed in Git, validated, assigned a semantic version in `VERSION`, and released as a GitHub Release/tag. The `publish-npm.yml` workflow tests the Python companion and npm bridge, then publishes that exact version only through the protected `npm-publish` environment. The npm package’s provenance links it to this public GitHub repository and release workflow.

An update delivers public, version-controlled guidance and code only. It does not include or upload a user’s scenarios, blueprints, plans, private learning overlay, API key, official CLI credentials, or execution data.

## One-time maintainer setup

The intended public package is `@markes76/make-com-skills`. Before the first release, the maintainer must confirm that the corresponding npm account or organization controls that scope; a registry `404` only proves that no public package can currently be read, not that the name is reservable.

1. Enable npm two-factor authentication for the publishing account and claim/create the `@markes76` scope if necessary.
2. From a clean, validated checkout, make the initial public publish using npm’s interactive authentication and `npm publish --access public` from `npm/`. This establishes the package record; do not paste an npm token into this repository or GitHub Actions.
3. Configure npm trusted publishing for `markes76/make.com-skills` and the exact workflow filename `publish-npm.yml`. npm’s current CLI can configure the same relationship with a command similar to:

   ```bash
   npm trust github @markes76/make-com-skills \
     --repo markes76/make.com-skills \
     --file publish-npm.yml \
     --environment npm-publish \
     --allow-publish
   ```

4. Create the GitHub `npm-publish` environment and require maintainer approval. Protect release tags and only create a release after its tests pass.
5. After trusted publishing succeeds once, remove/restrict any legacy npm publish token. The repository workflow uses short-lived GitHub OIDC credentials, not an `NPM_TOKEN` secret.

Current npm trusted publishing requires a recent npm/Node runtime and GitHub-hosted Actions runner. See [npm’s trusted publishing documentation](https://docs.npmjs.com/trusted-publishers/) for current setup requirements and [npm’s npx documentation](https://docs.npmjs.com/cli/commands/npx/) for invocation behavior.

## Normal release checklist

1. Review public-source watch candidates and merge only evidence-backed guidance changes.
2. Update `VERSION`, Python package metadata, `plugin.json`, and `npm/package.json` together; run `python3 scripts/sync_npm_version.py --check`.
3. Run Python validations, unit tests, `npm --prefix npm test`, and `(cd npm && npm pack --dry-run --json)`.
4. Create Git tag `v<version>` and a GitHub Release. The protected workflow validates that tag/version relationship and asks the configured GitHub environment for approval before publishing.
5. Publish concise release notes. Existing global users see the next opt-in notification; npx users select the new `latest` version when they invoke it.

Never mutate an existing npm version. Publish a new version, then move only the `latest` dist-tag through the reviewed release workflow.
