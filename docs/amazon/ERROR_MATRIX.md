# MCP error matrix

All operations are simulated. The table distinguishes observed output from pending verification; an unrun case is never presented as a result. Client-visible messages contain reason codes only, never amount, destination, contact identity, or transcript text.

## Before the adapter fix

| Case | Actual client result | Status |
|---|---|---|
| Changed `claimed_identity` after approval | JSON-RPC `-32000`, `SSE stream ended without a response` | Observed in the owner-side MCP 2.3.0 run on 2026-10-11 |
| Unknown contact on initial call | Not separately run before the fix | Not claimed |
| Expired proof | Existing gate rejected it, but this exact real-client matrix case was not run before the fix | Not claimed |
| Replayed proof | Existing phase-1 real-client replay test passed, but its old message was implementation text rather than a stable code | Observed indirectly |
| Cross-contact approval | Wrong contact token returned HTTP 403 in the existing phase-2 real-client test | Observed indirectly |

The changed-identity path raised an expected `ValueError` outside the MCP adapter's `ToolError` boundary. MCPServer therefore treated it as an unexpected tool failure and the client saw a closed SSE request.

## After the adapter fix

| Case | Required client result | Test |
|---|---|---|
| Changed `claimed_identity` after approval | Tool error containing `CG_CONTACT_NOT_REGISTERED`; no `SSE stream ended` | `test_changed_identity_has_stable_tool_error_without_sse_termination` |
| Unknown contact on initial call | Tool error containing `CG_CONTACT_NOT_REGISTERED` | `test_unknown_contact_has_stable_tool_error` |
| Expired proof | Tool error containing `CG_PROOF_EXPIRED_OR_NOT_YET_VALID` | `test_expired_proof_has_stable_tool_error` |
| Replayed proof | Tool error containing `CG_PROOF_REPLAYED` | `test_replayed_proof_has_stable_tool_error` |
| Cross-contact approval | Approval HTTP 403; retry still receives JSON-RPC `-32042` | `test_cross_contact_approval_keeps_url_elicitation_required` |

The five after-fix rows are implemented but remain **pending owner-side execution** because the restricted sandbox denied loopback access. Replace this sentence with the actual pytest summary only after running:

```powershell
python -m pytest tests/alexa_mcp/test_error_mapping.py -q -rs --basetemp .test-tmp/error-mapping
```

## Server logging review

- Expected proof failures are reduced to the allowlisted `CG_*` code before raising `ToolError`.
- Expected approval failures are caught at `send_money`'s MCP boundary and reduced to an allowlisted `CG_*` code.
- MCPServer logs deliberate ToolError text; that text now contains only tool name, HTTP-style status, and stable reason code.
- Unexpected exceptions retain server-side stack traces, but the new tests require all five expected rejection cases to avoid that path.
- Client tests use conspicuous private fixture values and assert that amount and destination never appear in returned error content.

