# Draft upstream issue: expected rejection after URL elicitation closes SSE request

Do not submit this draft without reproducing it against a minimal standalone server and checking for an existing upstream issue.

## Environment

- `mcp==2.3.0`
- Python 3.12
- Streamable HTTP over local HTTPS
- Client: `mcp.client.session.ClientSession`
- Server: `mcp.server.mcpserver.MCPServer`

## Observed behavior

After a URL-mode elicitation is approved, a retry with a changed identity causes the tool's domain layer to raise an expected `ValueError`. If the adapter does not convert that exception to `ToolError`, the client receives:

```text
mcp.shared.exceptions.MCPError: SSE stream ended without a response
code: -32000
```

## Expected behavior

Documentation should make clear that expected domain rejections during an elicitation retry must be translated to `ToolError`, and the stream should remain usable. A server-side test or example should cover this sequence:

1. Tool raises `UrlElicitationRequiredError` (`-32042`).
2. Client completes the external interaction.
3. Client retries with changed scope.
4. Tool deliberately rejects the changed scope.
5. Client receives a normal tool error rather than a closed SSE request.

## Repository reproduction

Before the adapter fix, run the claimed-identity parameter of:

```powershell
python -m pytest "tests/alexa_mcp/test_phase2.py::test_changed_scope_is_rejected[mutation2]" -vv
```

The project workaround catches expected approval failures at the MCP boundary and raises `ToolError` with a non-sensitive stable reason code. This draft does not claim the SDK itself is defective until a standalone reproduction shows that a deliberate `ToolError` also terminates the stream.

