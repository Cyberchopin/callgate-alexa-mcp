# Amazon RC1 handoff

## Current RC1 status — 2026-10-11

- `release/amazon-rc1` now contains the requested phase 1, phase 2, dependency, evaluation, red-team, and UI changes.
- `main` remains unchanged at `f18eda5`.
- Run `powershell -ExecutionPolicy Bypass -File scripts/verify_local.ps1` from the repository root. It tests phase 1, phase 2, full Python, and Node directly in RC1.
- The current sandbox did not clear the real-client startup gate: phase 1 and phase 2 timed out starting their test server, and UI/TestClient tests hung. Do not claim the RC1 acceptance gate passed until the local command completes.

## Stabilization status — 2026-10-11

- `amazon/stabilize` replaces the MCP tests' in-thread Uvicorn launch with a test-only subprocess, an operating-system-assigned temporary port, `/health` polling for up to 60 seconds, and failure output containing stdout, stderr, and exit code.
- This sandbox denied loopback access with WinError 10013, so the real-client gate remains **pending local execution**; no pass is claimed.
- The three historical failures were reproduced individually and classified in `BASELINE_FAILURES.md`. The two review-process failures occur in Windows spawn bootstrap before application logic. The evaluation-v2 mismatch is caused by working-tree line-ending conversion: the committed blob still matches the frozen manifest.
- Red-team and UI HTTP tests also hung twice in this sandbox. Their test-layer ASGI client update requires local confirmation; core code was not changed.
- Owner rerun confirmed the two spawned-process tests pass outside the sandbox. It also exposed two integration-test issues now corrected on this branch: the red-team suite still expected no subject rate limit, and unknown-contact rejection is surfaced by MCP SDK 2.3.0 as `-32000`/closed SSE rather than `-32042`.
- The generic `-32000` result is still a protocol-quality gap. The test records it as a rejection, not as successful URL elicitation; changing adapter behavior is outside this test-only stabilization branch.
- Owner acceptance run passed the regression subset, Node, phase 1, phase 2, and both pip-audit manifests. The only full-suite failure was the already diagnosed evaluation-v2 checkout conversion.
- Two Bandit medium findings introduced by the test health probe were removed without suppressions; one pre-existing accepted XML-parser medium remains.
- Final owner-side MCP gate on commit `2804f8a`: **10 passed in 20.66 seconds**. The test launcher has **0 medium/high Bandit findings**, 2 accepted subprocess-related low findings, and no suppressions.

## Historical integration attempt (superseded by Current RC1 status above)

- `release/amazon-rc1` contains `amazon/tools` only.
- Phase 1 was merged, failed its runtime gate twice, and was reverted.
- Phase 2, evaluation, red-team, UI, and pitch were not merged because they depend on the failed phase-1 gate or occur later in the required sequence.
- `main` remains at `f18eda5`.

## Owner action

Run `powershell -ExecutionPolicy Bypass -File scripts/run_rc1_phase1_gate.ps1` from the repository root. It now creates an isolated environment with the pinned MCP requirements. No push or branch deletion is required.

The latest automated retry did not reach pytest: the first environment failed `ensurepip`; the second installed MCP dependencies but revealed that the phase-1 requirements omit pytest. The script now installs pinned pytest, but was not run a third time because of the two-failure stop rule.

## Decisions

The owner later set D1–D6 to YES. Approved UI hardening is isolated on `amazon/ui`; the approved v2 retry is isolated on `amazon/commitment-v2-retry`. Neither is merged into RC1 before its own regression gate passes.

The read-only R3 finding is in `BINDING_FINDINGS.md`: exact parsed tool/argument binding exists through the signed v1 resource, but the requested canonicalization and stable subject/version binding do not.

## Dependency-upgrade gate

- Branch: `amazon/dependency-upgrade-rc1`, based on `release/amazon-rc1`.
- Selected version: `cryptography 50.0.0`; it was released more than 14 days before the decision and is the first version covering all six unique owner-reported advisories.
- Dependency manifests, an old-version Ed25519 vector, HTTPS compatibility test, pip-audit CI, Dependabot configuration, and Bandit triage are prepared.
- **PASS:** dependency compatibility tests passed 3/3 under `cryptography 50.0.0`; phase1 passed 3/3; phase2 passed 10/10; Node passed 3/3.
- Full Python produced **249 passed, 3 failed, 3 skipped**. The same three baseline failures remain; the regression subset excluding those three produced **249 passed, 3 skipped, 1 deselected**, so no previously passing test became a failure.
- **PASS:** the owner-run root and MCP pip-audit commands each returned `No known vulnerabilities found` for the unchanged manifests.
- Agent Scan remains postponed and is not claimed as passed.
- The current Bandit medium is in a local JUnit report parser, not core safety code; it was accepted with the bounded rationale in `BANDIT_TRIAGE.md`. No `nosec` was added.
- Remaining known conditions: the isolated dependency environment skips two optional `onnxruntime` tests and one optional `pipecat` test; the three pre-existing baseline failures are not caused by this upgrade.
## Evaluation branch

- Status: DONE with disclosed baseline failures.
- Branch: `amazon/eval`.
- Outputs: `evaluation_checkout/results.json`, `REPORT.md`, `safety_utility.svg`, and `sensitivity_scan.svg`.
- The experiment is explicitly a seeded author simulation, not human research.
- No decision is required for the evaluation implementation.

- Historical secret-scanner classification remains a prerequisite before any migration, publication, or push.
## Red-team status

- Branch: `amazon/redteam`.
- Red-team task: DONE for the current phase-2/v1 prototype, with explicit untestable boundaries.
- Core security code changed: no.

## Red-team decisions subsequently approved by the owner

- Decide whether the MCP adapter may reuse the existing trusted challenge-rate limiter; the current path has only a global pending-capacity bound.
- Decide whether the local review endpoint should require Origin validation and a CSRF token in addition to its bearer header.
- Decide whether to add a restrictive `Referrer-Policy` header before any non-local deployment.
- Commitment v2 remains reverted; this report must not be used as evidence that v2 binding passed.
## Approved hardening gate

- D2/D3/D4 changes are now integrated into RC1 but require a fresh local regression run.
- Run `powershell -ExecutionPolicy Bypass -File scripts/run_ui_hardening_gate.ps1` from the repository root.

- Branch: `amazon/ui`.
- Status: PARTIAL because implementation/tests passed but screenshots could not be captured.
- Open `/demo` on the local phase-2 server for the fixed offline simulated voice-assistant fixture.
- Use `python -m scripts.run_ui_preview` only for local screenshots; it clearly serves HTTP and is not security evidence. The protected approval demonstration must use the HTTPS phase-2 command.
- Owner action: capture the three screenshots listed in `UI_ACCESSIBILITY.md` outside this environment and visually verify contrast with an accessibility tool.
- No bilingual toggle was added; it was optional and did not displace security or accessibility work.

