# Competition-tool friction log

Only real issues involving MCP SDK/specification, Alexa+ documentation, Devpost,
or other competition tooling belong here. Local machine and sandbox issues belong
in `BUILD_LOG.md`.

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

