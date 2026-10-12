# Product feedback draft

This draft contains only observations reproduced during development. Keep the raw entries in `FRICTION_LOG.md` attached to the final combined branch.

## Tools, APIs, and SDKs used

- Model Context Protocol specification 2025-11-25: Streamable HTTP, URL-mode elicitation, and `notifications/elicitation/complete`.
- MCP Python SDK `mcp==2.3.0`: self-hosted server, typed tools, Streamable HTTP client/server sessions, and URL-elicitation error structures.
- SQLite through CallGate's existing replay store: durable one-time proof consumption across server restarts.
- Python `cryptography`: local Ed25519 signatures and a short-lived, self-signed development certificate. No real identity, payment, or account credential is used.

## What worked well

- In the recorded successful integration run, a real `ClientSession` discovered all three typed tools over Streamable HTTP; this was not a mocked JSON-RPC exchange.
- Raising `UrlElicitationRequiredError` produced protocol code `-32042`, and `send_elicit_complete` delivered the matching completion notification in the real-client test.

## What needs work

### Server-class migration discoverability

In MCP Python SDK 2.x, the familiar FastMCP import path no longer exists; the server is imported as `MCPServer` from `mcp.server.mcpserver`. Importantly, the initial error message itself already contained the correct migration link and pinning alternative:

```text
ModuleNotFoundError: No module named 'mcp.server.fastmcp'. This is mcp 2.x, where FastMCP was renamed to MCPServer (from mcp.server.mcpserver import MCPServer) and other APIs changed; see the migration guide at https://py.sdk.modelcontextprotocol.io/v2/migration/#fastmcp-renamed-to-mcpserver or pin 'mcp<2' to keep running v1 code.
```

Workaround: follow that diagnostic, use the v2 import, and pin `mcp==2.3.0`. The diagnostic is already actionable; the only suggestion is to repeat the v2 import path directly in the Streamable HTTP quickstart so users can avoid the error.

### Documentation example for expected policy denials

Raising a normal application exception hid the policy reason behind a generic tool error:

```text
TextContent(type='text', text='Error executing tool send_money', annotations=None, meta=None)
mcp.server.mcpserver.exceptions.UnexpectedToolError: Error executing tool send_money
```

The SDK behavior is consistent with treating an ordinary exception as unexpected. Workaround: raise an SDK `ToolError` subtype for an expected policy denial. This is a documentation request: add one policy-denial example showing when to use `ToolError`, without changing exception behavior.

### URL-elicitation client reconstruction

The server emitted the SDK's URL-elicitation error, but the real client surfaced it as:

```text
mcp.shared.exceptions.MCPError: URL elicitation required
```

Workaround: verify error code `-32042`, then call `UrlElicitationRequiredError.from_error(error.error)`. Suggestion: reconstruct the specialized error automatically, or document this conversion next to the server example.

Retest on the latest available release, `mcp==2.3.0`, reproduced the same type boundary: `MCPError.from_error_data(...)` returned `MCPError` with code `-32042`; manual conversion returned `UrlElicitationRequiredError`. Related upstream issues [#1768](https://github.com/modelcontextprotocol/python-sdk/issues/1768) and [#1788](https://github.com/modelcontextprotocol/python-sdk/issues/1788) are closed and do not exactly cover automatic client-side specialization in 2.3.0.

## Onboarding experience

The path from installation to a basic Streamable HTTP server was short after identifying the SDK 2.x server rename. Moving from a basic tool to specification-native URL elicitation required reading the 2025-11-25 specification directly and adding a real-client integration test because the specialized client error behavior was not apparent from the server API alone.

## Would we build with it again?

`{{OWNER CONFIRM: Yes/No and personal wording. Suggested answer: Yes — the protocol provides the right separation for out-of-band approval, while the Python SDK would benefit from clearer v2 migration and URL-elicitation client examples.}}`
