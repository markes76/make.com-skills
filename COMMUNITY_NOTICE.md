# Community Companion Notice

`make-skills`, the skill bundle, and the npm/npx bridge in this repository are independent community software. They are **not** a Make.com product, are not the official `make-cli`, and are not affiliated with, endorsed by, or supported by Make.com unless Make.com states otherwise.

The project invokes the separately installed official `make-cli` rather than reimplementing its API. It can prepare plans, reports, and agent handoffs from the public skill knowledge and authenticated official CLI reads. It must not imply that a Make MCP tool, Make API operation, or app capability exists until the active MCP surface or official CLI documents it.

Users are responsible for reviewing every proposed automation, permission, credential connection, test, Make CLI command, and production effect before approving it. Automations can create, change, send, delete, duplicate, or expose data in third-party systems. Test in a non-production scope where practical, use controlled data, keep new scenarios inactive, and maintain rollback/monitoring plans.

This software is provided “as is,” without warranties or guarantees of correctness, availability, compatibility, security, or fitness for a particular purpose, to the maximum extent permitted by law. See [LICENSE](LICENSE). A local plan, report, or skill suggestion is not a guarantee and is never authorization to mutate a Make scenario.
