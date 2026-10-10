# Commitment v2 core-change proposal

Status: **AWAITING OWNER APPROVAL — NOT APPLIED**

The executable core was not changed. `docs/amazon/proposals/commitment_v2.patch` is a review artifact only. Applying it requires explicit approval in a later turn.

## Intended scope

- Add `commitment_version=2`, `operation_type`, a canonical substantive-parameter hash, and `subject` to a v2 signed claim.
- Bind the v2 claim to an operation commitment while retaining `session_id` as transport/session scope; `subject` is a separate stable authorization scope and must not be derived from an MCP session identifier.
- Normalize mapping key order and JSON numbers before hashing. Booleans remain booleans; non-finite numbers and non-JSON values fail closed.
- Preserve the v1 claim, signing bytes, Ed25519 algorithm, contact selection, policy decisions, and replay store behavior.
- Add focused tests for cross-tool use, merchant/cart mutation, subject mutation, numeric/key normalization, and v1 verification.

## Risk

- Canonicalization is security-critical and needs independent review for cross-language equivalence.
- Adding fields to an existing Pydantic model can silently change legacy signing bytes. The proposal therefore uses separate discriminated v1/v2 claim models rather than nullable fields on v1.
- The workflow adapter must not infer `subject` from `session_id`; the caller must provide a trusted stable subject.

## Test impact

No proposal tests were run because the core diff was not approved for application. Existing T0 baseline remains **245 passed, 3 failed, 1 skipped** for Python and **3 passed, 0 failed, 0 skipped** for Node.

