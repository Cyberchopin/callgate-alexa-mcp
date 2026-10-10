# Amazon RC1 handoff

## Integration status

- `release/amazon-rc1` contains `amazon/tools` only.
- Phase 1 was merged, failed its runtime gate twice, and was reverted.
- Phase 2, evaluation, red-team, UI, and pitch were not merged because they depend on the failed phase-1 gate or occur later in the required sequence.
- `main` remains at `f18eda5`.

## Owner action

Run `powershell -ExecutionPolicy Bypass -File scripts/run_rc1_phase1_gate.ps1` on the local machine. If it succeeds, explicitly authorize retrying R1 in a new turn. No push or branch deletion is required.

## Decisions

The D1–D6 values were left as `<YES/NO>`. They are treated as not approved. No rate-limit, Origin/CSRF, referrer-policy, adapter-binding, or v2-retry change was applied to RC1.

The read-only R3 finding is in `BINDING_FINDINGS.md`: exact parsed tool/argument binding exists through the signed v1 resource, but the requested canonicalization and stable subject/version binding do not.

