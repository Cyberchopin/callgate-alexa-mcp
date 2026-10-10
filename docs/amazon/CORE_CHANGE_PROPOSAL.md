# Commitment v2 core-change proposal

Status: **AWAITING OWNER APPROVAL — NOT APPLIED**

The executable core was not changed. `docs/amazon/proposals/commitment_v2.patch` is a review artifact only. Applying it requires explicit approval in a later turn.

## Intended scope

- Add `commitment_version=2`, `operation_type`, a canonical substantive-parameter hash, and `subject` to a v2 signed claim.
- Put all four fields inside both the reviewer-signed request and the issuer-signed verification claim. They are inputs to the existing `signing_bytes`; none may be appended after signing.
- Bind the v2 claim to an operation commitment while retaining `session_id` as transport/session scope; `subject` is a separate stable authorization scope and must not be derived from an MCP session identifier.
- Normalize mapping key order, JSON numbers, and Unicode strings/keys to NFC before hashing. Booleans remain booleans; non-finite numbers, duplicate raw JSON keys, post-normalization key collisions, and non-JSON values fail closed.
- Preserve the v1 claim, signing bytes, Ed25519 algorithm, contact selection, policy decisions, and replay store behavior.
- Preserve v1 verification only for existing non-MCP callers. Every protected MCP tool must explicitly require v2 and reject a valid v1 credential to prevent downgrade.
- Add focused tests for cross-tool use, merchant/cart mutation, subject mutation, integer/float and key-order equivalence, Unicode equivalence/collision, duplicate keys, v1 compatibility, and MCP v1 downgrade rejection.

## Risk

- Canonicalization is security-critical and needs independent review for cross-language equivalence.
- Adding fields to an existing Pydantic model can silently change legacy signing bytes. The proposal therefore uses separate discriminated v1/v2 claim models rather than nullable fields on v1.
- The workflow adapter must not infer `subject` from `session_id`; the caller must provide a trusted stable subject.
- A generic core API that silently accepts v1 is unsafe for MCP. The MCP adapter must pass an explicit `required_commitment_version=2` (or call a v2-only entry point) before any policy or replay decision.
- Duplicate keys cannot be detected after a JSON object has become a Python `dict`; the MCP boundary must reject them while parsing raw arguments, before constructing the commitment.

## Test impact

No proposal tests were run because the core diff was not approved for application. Existing T0 baseline remains **245 passed, 3 failed, 1 skipped** for Python and **3 passed, 0 failed, 0 skipped** for Node.

## Approval checklist

- [ ] The four v2 fields are visible in the exact bytes covered by both signatures.
- [ ] MCP `send_money` and `place_order` reject v1 even though legacy core callers still verify v1.
- [ ] `subject` comes from trusted account context, never MCP session ID or tool arguments.
- [ ] Duplicate raw keys and Unicode-normalized key collisions fail before hashing.
- [ ] No signing, contact-selection, replay, or policy-decision algorithm changes.
- [ ] The implementation patch contains no ellipses and all new and legacy tests have actual output.

