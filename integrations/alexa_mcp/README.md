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

The restricted development sandbox could not verify loopback networking. An
owner-side run on `amazon/stabilize` commit `2804f8a` completed the combined
phase 1 and phase 2 real-client suite with **10 passing tests in 20.66 seconds**.
Run `powershell -ExecutionPolicy Bypass -File scripts/verify_local.ps1` again
after subsequent changes; do not carry this result forward to changed code.

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

## Phase 2 URL elicitation demo

Phase 2 is integrated into `release/amazon-rc1` for `send_money` only:

```powershell
py -3.12 -m integrations.alexa_mcp.phase2 --replay-db .local/phase2.sqlite3 --contact-token local-demo-contact
```

Open `/demo` for the fixed offline **simulated voice assistant** fixture. The
no-build HTML/CSS/JavaScript interface explains why an action paused, what it
protected, and what happens next. Review pages fetch their transaction fields
from server-held pending state by request ID; URL query parameters are ignored.
The local contact credential is a simulation, not proof of a person.

It serves MCP and the independent simulated-contact review page over local HTTPS
with a generated, short-lived self-signed certificate. The certificate and private
key are created below the Git-ignored `.test-tmp/` runtime directory and removed
when the server exits, so an interrupted demo still cannot add them to Git. The MCP endpoint is
`https://127.0.0.1:8443/mcp`. The approval URL contains only a random elicitation
ID; the simulated contact credential is sent separately in the
`X-CallGate-Contact-Token` header. The page displays the full amount, destination,
and requested saved-contact identity.

The SDK's native `UrlElicitationRequiredError` supplies JSON-RPC code `-32042` and
the 2025-11-25 URL-mode fields. Approval sends
`notifications/elicitation/complete` only to the initiating MCP session. The
server keeps the resulting v1 proof out of the MCP/LLM context and consumes it on
the exact retry. `subject` is server configuration and is not derived from the MCP
session. This is a thin compatibility boundary pending owner approval of
commitment v2; it is not production identity or payment authorization.

## Simulated merchant and injection experiment

`python -m integrations.alexa_mcp.merchant` starts an independent Streamable HTTP
merchant MCP server with `search_products`, `get_product`, `add_to_cart`, and
`view_cart`. `python -m scripts.run_amazon_services` launches both local services.
For a network-free deterministic comparison, run
`powershell -ExecutionPolicy Bypass -File scripts/demo.ps1 -Offline`. Omit
`-Offline` to launch the two MCP servers, assistant page, and contact-review
routes on temporary local ports. Development certificates and private keys are
created in a temporary directory and removed when the process exits.

The vulnerable demo agent is an intentionally unsafe scripted test double. It is
not a real assistant, uses no LLM, and never participates in authorization. The
offline command prints raw attempted and executed counts for both modes. Do not
quote those counts until the command completes in the final environment. They are
fixture counts, not a security rate or human-study result. The committed offline
fixture result is **2/2 simulated unauthorized actions without CallGate and 0/2
with CallGate**; its machine-readable evidence is
`docs/amazon/merchant_injection_results.json`.
