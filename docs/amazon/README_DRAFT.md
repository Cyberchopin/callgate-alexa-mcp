# CallGate MCP — submission README draft

## What it is

CallGate MCP is a self-hosted safety gateway for simulated high-risk actions from a
simulated voice assistant. It exposes three MCP tools: `send_money`, `place_order`,
and the permanently blocked canary `share_verification_code`. No tool moves money,
places a real order, shares a real verification code, or connects to a real account.

## Run it in one command

Phase 1, from the repository root after installing
`integrations/alexa_mcp/requirements.txt`:

```powershell
py -3.12 -m integrations.alexa_mcp.server --replay-db .local/callgate-mcp-replay.sqlite3
```

Phase 2 local HTTPS URL-elicitation demo:

```powershell
py -3.12 -m integrations.alexa_mcp.phase2 --replay-db .local/phase2.sqlite3 --contact-token local-demo-contact
```

{{TBD: replace the demonstration-only contact credential and verify the final public repository command after approved branches are combined.}}

## Architecture

The Streamable HTTP MCP adapter delegates signature checks, policy approval, and
nonce consumption to CallGate's existing `DemoVerificationGate`. The existing
`SQLiteReplayStore` keeps consumed nonces across process restarts. Phase 2 adds a
thin adapter around the existing v1 operation commitment and an independent local
HTTPS review page. The approval URL contains only a random elicitation ID; amount,
destination, identity, and contact credentials are not embedded in it.

The approved v1 credential and pending-operation record remain server-side. The
local adapter rejects a changed amount, destination, identity, contact, session,
expired request, self-approval attempt, or replay in the tested flow. This is not
yet a cryptographic claim that v1 binds the tool name or stable subject; the final
submission must wait for an approved v2 commitment before making that claim.

## MCP details

- Specification behavior: URL-mode elicitation from MCP **2025-11-25**.
- Negotiated SDK protocol in tests: **2026-07-28**.
- Transport: **Streamable HTTP**.
- Python SDK: **mcp==2.3.0**.
- Missing approval: JSON-RPC **-32042** using the SDK's native
  `UrlElicitationRequiredError` wire shape.
- Completion: `notifications/elicitation/complete` is sent to the initiating MCP
  session after the saved-contact simulation approves.
- Observed phase-1 MCP tests: **3 passed**.
- Observed phase-2 MCP tests: **9 passed** across phase-1 and phase-2 integration tests.

## Alexa+ track note

The project supplies a real self-hosted MCP server and a **simulated voice-assistant
experience**. It is not integrated with the real Alexa+ runtime, and this project
does not claim that Alexa+ currently supports this URL-elicitation flow. The demo
client explicitly declares URL elicitation capability.

## Security boundaries and what we do not claim

- All money, orders, contacts, identities, and approval actions are simulated.
- There is no bank, merchant, payment-network, phone, or real assistant integration.
- No LLM output is an authorization decision.
- The local contact header is a demonstration credential, not proof of an
  independently enrolled human.
- The self-signed local certificate is for development only.
- Commitment v2 is awaiting owner approval. Phase 2 isolates current v1 commitment
  construction behind a thin adapter and does not claim subject binding inside the
  signed v1 credential.
- Full-history scanning found **3** redacted `generic-api-key` findings in one
  historical file/commit. The repository history must not be published or migrated
  until the owner resolves them.
- Current full-suite runs retain **3** pre-existing failures in this sandbox: two
  Windows child-process pipe failures and one frozen-manifest mismatch. No green CI
  claim is made.

## What was significantly updated after the submission period starts

The Amazon cutoff report is generated directly from Git with cutoff
`2026-08-31T10:15:00-07:00`. The isolated work branches add:

- a Streamable HTTP MCP server with three simulated tools;
- mandatory SQLite replay protection and restart replay tests;
- a permanently blocked verification-code canary;
- native `-32042` URL-mode elicitation for `send_money`;
- a local HTTPS saved-contact review and completion notification;
- real MCP client integration tests; and
- Git-derived pre-existing-work, friction, and submission-check tooling.

{{TBD: insert final merged commit range and public repository URL only after the
history-scan finding is resolved and branches are approved for merge.}}

