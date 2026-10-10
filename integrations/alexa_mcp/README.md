# CallGate simulated voice-assistant MCP server

This is a **simulated voice-assistant path**. It is not connected to Alexa+, Amazon,
any payment provider, or any real account. Every reported completion is simulated.

## Run it in one command

From the repository root, after installing `integrations/alexa_mcp/requirements.txt`:

```powershell
py -3.12 -m integrations.alexa_mcp.server --replay-db .local/callgate-mcp-replay.sqlite3
```

The self-hosted Streamable HTTP endpoint is `http://127.0.0.1:8000/mcp`.
The server uses MCP Python SDK **2.3.0** and advertises the SDK's
**2026-07-28** protocol version, which is newer than the required 2025-11-25
version.

## Phase 1 scope

- `send_money` and `place_order` require a signed CallGate proof. Without one,
  they fail with `403 POLICY_PROOF_REQUIRED`.
- `share_verification_code` is a canary tool. It is permanently blocked, including
  when a valid proof is supplied.
- All tools delegate authorization to the existing `DemoVerificationGate`; this
  integration does not copy signature, policy, or replay decisions.
- The existing `SQLiteReplayStore` is mandatory. Its file survives process restart,
  so a consumed proof cannot be replayed by a new server process.

Phase 1 does not implement URL elicitation, contact approval pages, durable pending
requests, a merchant server, AWS services, or UI. Those are separate later phases.
