# Amazon red-team handoff

## Status

- Branch: `amazon/redteam`.
- Red-team task: DONE for the current phase-2/v1 prototype, with explicit untestable boundaries.
- Core security code changed: no.

## Owner decisions

- Decide whether the MCP adapter may reuse the existing trusted challenge-rate limiter; the current path has only a global pending-capacity bound.
- Decide whether the local review endpoint should require Origin validation and a CSRF token in addition to its bearer header.
- Decide whether to add a restrictive `Referrer-Policy` header before any non-local deployment.
- Commitment v2 remains reverted; this report must not be used as evidence that v2 binding passed.

