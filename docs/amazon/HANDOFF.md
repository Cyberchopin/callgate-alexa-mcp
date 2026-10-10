# Amazon commitment-v2 handoff

## Status

> 🔴 **BLOCKED:** the approved v2 attempt was reverted after existing MCP tests stopped starting their local Uvicorn servers. The same timeout remained after the revert, so the current environment cannot distinguish an implementation regression from a local-listener/runtime failure.

- Proposal approved: `1fbb196035f327568902475b3e4c95499d4597d2`.
- Attempt: `afc5e02`.
- Required revert: `a05f675`.
- Branch HEAD contains no applied v2 implementation.
- No push, merge, history rewrite, frozen-evaluation edit, or secret inspection occurred.

## Owner decision required

Run the existing Phase 2 MCP tests outside this environment. If the pre-v2 branch `amazon/mcp-phase2` passes there, authorize a fresh implementation attempt in a clean worktree or provide the server startup diagnostics. Do not merge or record the final demo while v2 remains unapplied.

The downstream `amazon/merchant-injection`, `amazon/ui`, `amazon/resume`, and final-gate work that depends on a passing v2 branch was not started. Building those branches on a reverted or unverified authorization core would invalidate their acceptance evidence.
