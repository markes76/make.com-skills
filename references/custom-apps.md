# Custom Make App Guidance

Use a custom Make app when the integration will be reused, needs a native module experience, or requires stable typed mappings beyond a one-off HTTP module.

## Design decisions

- Model authentication separately from module behavior. Choose the narrowest supported connection type and avoid placing secrets in a module field.
- Select the module type that matches the upstream API: action, search, polling trigger, instant/webhook trigger, responder, or universal module.
- Give every emitted object a stable typed interface. Avoid “JSON blob” outputs when consumers need individual mapping fields.
- Make list/search pagination explicit, and use RPCs for dynamic options, dynamic fields, and dynamic samples.
- Treat API and output-schema changes as compatibility changes. Version and test them before publishing.

## Pagination boundary

For a reusable custom-app list/search module, use the request-level `pagination` collection rather than recreating stateful looping in every consuming scenario. It supports request/query overrides and a response-driven continuation condition; the current limits and examples are documented in [Make's Custom Apps pagination reference](https://developers.make.com/custom-apps-documentation/component-blocks/api/pagination).

Choose a page/offset design when the API supplies a stable count or an empty-page contract. Choose a token/next-URL design when the API returns an opaque continuation value. Preserve that value exactly and stop only when the documented continuation field is absent/empty. Validate against a public or sandbox response before publishing; a scenario Repeater is a teaching or bounded-batch tool, not a substitute for custom-app pagination.

## Boundary with MCP

The Make MCP scenario surface can design and operate connected scenarios, but it may not expose custom-app provisioning, deployment, reauthorization, data-store authoring, user-defined types, or incomplete-execution repair. State this boundary plainly; do not claim a scenario operation publishes an app.

When the user supplies an authorized Make API credential, follow [CLI delivery](cli-delivery.md) and confirm the actual endpoint support in that Make zone before implementing deployment commands.
