# Competition-tool friction log

Use `py -3.12 scripts/friction.py add ...` at the time a real competition-tool
problem occurs. Do not backfill hypothetical issues. Local machine and sandbox
problems belong in `docs/amazon/BUILD_LOG.md`.

Only real issues involving MCP SDK/specification, voice-assistant track documentation,
Devpost, or other competition tooling belong here.

## FRICTION-001 — MCP Python SDK 2.x server rename — 2026-10-10

- Task: T5 Streamable HTTP server.
- Step: Import the familiar FastMCP server class while checking the pinned SDK API.
- Expected: Server class import succeeds.
- Actual (raw):

```text
ModuleNotFoundError: No module named 'mcp.server.fastmcp'. This is mcp 2.x, where FastMCP was renamed to MCPServer (from mcp.server.mcpserver import MCPServer) and other APIs changed; see the migration guide at https://py.sdk.modelcontextprotocol.io/v2/migration/#fastmcp-renamed-to-mcpserver or pin 'mcp<2' to keep running v1 code.
```

- Severity: medium.
- Workaround: Import `MCPServer` from `mcp.server.mcpserver` and pin `mcp==2.3.0`.
- Actionable suggestion: Put the v2 import path beside Streamable HTTP examples in the SDK quickstart.

## FRICTION-002 — Expected tool failures need SDK ToolError — 2026-10-10

- Task: T5 unauthorized-call and canary tests.
- Step: Raise an integration-specific `ValueError` containing the policy code.
- Expected: MCP client receives the policy code as tool error content.
- Actual (raw):

```text
TextContent(type='text', text='Error executing tool send_money', annotations=None, meta=None)
mcp.server.mcpserver.exceptions.UnexpectedToolError: Error executing tool send_money
```

- Severity: medium.
- Workaround: Subclass `mcp.server.mcpserver.exceptions.ToolError` for expected policy failures.
- Actionable suggestion: Add a documented policy-denial example that distinguishes `ToolError` from an unexpected exception.

## FRICTION-003 — Client does not specialize URL-elicitation error — 2026-10-10

- Task: T6 URL-mode elicitation integration test.
- Step: Catch the SDK's `UrlElicitationRequiredError` from a real `ClientSession.call_tool` request after the server raised that exact SDK exception.
- Expected: Client reconstructs the specialized error type and exposes its `elicitations` property.
- Actual (raw):

```text
mcp.shared.exceptions.MCPError: URL elicitation required
```

- Severity: medium.
- Workaround: Verify code `-32042`, then call `UrlElicitationRequiredError.from_error(error.error)` before reading the URL-mode fields.
- Actionable suggestion: Have the Python client dispatcher reconstruct `UrlElicitationRequiredError` automatically when it receives `-32042`, or document the manual conversion next to the server example.



## 2026-10-11T18:29:57-07:00 — MCP SDK expected rejection transport

- Step: Call send_money with a changed claimed_identity after approval using ClientSession.call_tool on MCP Python SDK 2.3.0
- Expected: A deliberate ToolError result with a stable rejection reason, without terminating the stream.
- Actual (raw):

```text
mcp.shared.exceptions.MCPError: SSE stream ended without a response
client code: -32000; expected URL-elicitation code assertion: -32042
```

- Severity: medium
- Workaround: Catch expected approval ValueError subclasses at the MCP adapter boundary and raise SDK ToolError with a stable reason code.
- Actionable suggestion: Document how tool authors should map expected domain rejections during URL-elicitation retry; add an SDK regression test that an expected rejection never closes the SSE stream.
