# Product feedback draft

This draft contains only observations reproduced during development. Keep the raw entries in `FRICTION_LOG.md` attached to the final combined branch.

## Tools, APIs, and SDKs used

- Model Context Protocol specification 2025-11-25: Streamable HTTP, URL-mode elicitation, and `notifications/elicitation/complete`.
- MCP Python SDK `mcp==2.3.0`: self-hosted server, typed tools, Streamable HTTP client/server sessions, and URL-elicitation error structures.
- SQLite through CallGate's existing replay store: durable one-time proof consumption across server restarts.
- Python `cryptography`: local Ed25519 signatures and a short-lived, self-signed development certificate. No real identity, payment, or account credential is used.

## What worked well

- Streamable HTTP client/server interoperability was testable end to end with the real SDK rather than mocked JSON-RPC.
- The SDK exposes the URL-elicitation server error and completion-notification primitives needed to implement the 2025-11-25 flow.
- Typed tool schemas made the three simulated actions visible through a normal MCP `tools/list` call.
- Pinning the SDK version made the demo and tests reproducible.

## What needs work

### Server-class migration discoverability

In MCP Python SDK 2.x, the familiar FastMCP import path no longer exists; the server is imported as `MCPServer` from `mcp.server.mcpserver`. The initial import produced:

```text
ModuleNotFoundError: No module named 'mcp.server.fastmcp'. This is mcp 2.x, where FastMCP was renamed to MCPServer (from mcp.server.mcpserver import MCPServer) and other APIs changed; see the migration guide at https://py.sdk.modelcontextprotocol.io/v2/migration/#fastmcp-renamed-to-mcpserver or pin 'mcp<2' to keep running v1 code.
```

Workaround: use the v2 import and pin `mcp==2.3.0`. Suggestion: put the v2 import path directly beside current Streamable HTTP quickstart examples.

### Expected policy denials

Raising a normal application exception hid the policy reason behind a generic tool error:

```text
TextContent(type='text', text='Error executing tool send_money', annotations=None, meta=None)
mcp.server.mcpserver.exceptions.UnexpectedToolError: Error executing tool send_money
```

Workaround: raise an SDK `ToolError` subtype for expected policy denials. Suggestion: document a policy-denial example that distinguishes expected tool errors from unexpected failures.

### URL-elicitation client reconstruction

The server emitted the SDK's URL-elicitation error, but the real client surfaced it as:

```text
mcp.shared.exceptions.MCPError: URL elicitation required
```

Workaround: verify error code `-32042`, then call `UrlElicitationRequiredError.from_error(error.error)`. Suggestion: reconstruct the specialized error automatically, or document this conversion next to the server example.

## Onboarding experience

The path from installation to a basic Streamable HTTP server was short after identifying the SDK 2.x server rename. Moving from a basic tool to specification-native URL elicitation required reading the 2025-11-25 specification directly and adding a real-client integration test because the specialized client error behavior was not apparent from the server API alone.

## Would we build with it again?

`{{OWNER CONFIRM: Yes/No and personal wording. Suggested answer: Yes — the protocol provides the right separation for out-of-band approval, while the Python SDK would benefit from clearer v2 migration and URL-elicitation client examples.}}`
