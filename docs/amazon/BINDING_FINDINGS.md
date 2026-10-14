# MCP adapter binding findings

Review target: `amazon/mcp-phase2`. D5 was later approved.

## Conclusion

The current v1 proof already signs a `resource` string and the MCP adapter already computes that resource as SHA-256 over `{tool, arguments}`. The gate verifies equality between the signed resource and the resource recomputed at execution. Therefore exact parsed tool/argument changes are already scope mismatches.

This is **not** the requested complete canonical binding. Unicode NFC is not applied, duplicate JSON keys are not rejected at the adapter boundary, and the format has no explicit commitment version. Stable subject identity is also not inside the v1 signed claim.

## Code evidence

- `amazon/mcp-phase2:integrations/alexa_mcp/server/app.py:24-28`: `operation_resource` hashes the tool name and argument object with sorted JSON keys and SHA-256.
- `amazon/mcp-phase2:integrations/alexa_mcp/server/approval.py:51-52`: approval creation places that resource into the confirmation request.
- `amazon/mcp-phase2:callgate/confirmation.py:106-108`: credential issuance copies the confirmed resource into the v1 claim.
- `amazon/mcp-phase2:callgate/verification.py:40-42, 50`: the full claim, including `resource`, is signed.
- `amazon/mcp-phase2:callgate/verification.py:70-74`: signature and resource equality are checked before execution.
- `amazon/mcp-phase2:callgate/replay_store.py`: nonce consumption uses an atomic SQLite insert under a write lock.

## Gap and recommendation

The complete requested adapter-only change is not feasible at the current MCP tool boundary: the SDK parses JSON before the tool function receives arguments, so duplicate raw keys have already been collapsed and cannot be rejected honestly. No partial implementation was applied to RC1. The approved `amazon/commitment-v2-retry` branch instead signs operation type, canonical parameter hash, stable simulated subject, and commitment version, but it remains outside RC1 until its regression gate passes.

