# Amazon RC1 handoff

## Integration status

- `release/amazon-rc1` contains `amazon/tools` only.
- Phase 1 was merged, failed its runtime gate twice, and was reverted.
- Phase 2, evaluation, red-team, UI, and pitch were not merged because they depend on the failed phase-1 gate or occur later in the required sequence.
- `main` remains at `f18eda5`.

## Owner action

Run `powershell -ExecutionPolicy Bypass -File scripts/run_rc1_phase1_gate.ps1` from the repository root. It now creates an isolated environment with the pinned MCP requirements. No push or branch deletion is required.

## Decisions

The owner later set D1–D6 to YES. Approved UI hardening is isolated on `amazon/ui`; the approved v2 retry is isolated on `amazon/commitment-v2-retry`. Neither is merged into RC1 before its own regression gate passes.

The read-only R3 finding is in `BINDING_FINDINGS.md`: exact parsed tool/argument binding exists through the signed v1 resource, but the requested canonicalization and stable subject/version binding do not.

