# MCP Capability Log

This log records the evidence format for MCP-dependent guidance. It deliberately contains no raw customer data, credentials, scenario exports, or webhook addresses.

## Current interoperability baseline

The Make ChatGPT connector has been used as the initial naming reference for environment discovery, app/module discovery, connections, scenario lifecycle, execution inspection, and generic-webhook learning. These names are not a cross-client contract. A different Make MCP server may expose different names, parameters, scopes, or no write operations at all.

| Area | Evidence required before a behavioral claim | Current package stance |
| --- | --- | --- |
| Environment and scope | Sanitized `environment` response or official source | Discover scope before a targeted read or write. |
| Module fields and options | Live module specification/options response | Never guess field paths or option values. |
| Scenario create/patch | Safe sandbox or user-authorized inactive scenario observation | Create inactive; fresh-read before minimal patch. |
| Webhook learning | Learned schema from a representative test delivery | Build the trigger first and wait for actual schema. |
| Runs and executions | Controlled test with declared side effects | Inspect the narrowest execution state before retrying. |
| API/CLI capabilities | Official endpoint documentation for the user's zone | Do not imply MCP operations are API endpoints. |

## Entry template

```text
Date / client / connector version:
Capability:
Sanitized input shape:
Observed outcome and limits:
Official source URL (if applicable):
Follow-up guidance / expiration date:
```

Record a new entry only after a reproducible check. If the behavior is security-sensitive, revalidate within 30 days; revalidate MCP/API behavior within 90 days.
