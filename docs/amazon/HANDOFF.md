# Amazon handoff — local PR #20 integration

## Current status — 2026-10-13

The owner explicitly approved merging inspected main `1d1069169e4fd10b5ac887bdcdc827b77b195b92`
into local `amazon/ci-repair`, with documentation-only conflict resolution and
regression tests. This does not authorize a push, a GitHub PR merge, a main
update, core-security changes, or frozen-data edits.

- The three document conflicts are resolved locally. Fresh post-resolution
  verification: 21 focused tests passed; full Python 290 passed, 3 skipped,
  1 warning; Node 3 passed; claims registered=39 unresolved_or_inconsistent=0.
  These match the pre-merge regression counts; no skip or xfail was added.
- Preserve the current portable environment guidance in REUSE_PLAN.
- Preserve both branches' build logs; incoming historical handoff is retained
  below, not treated as current deployment instructions.
- v2 is not implemented by importing its proposal. Do not apply that patch.
- Existing exact secret-scan ignore entries are unchanged. Historical warnings
  below describe prior stages; publication remains a separate owner decision.
- Incoming pitch/story documents remain drafts, not proof that every described
  scene runs. Their placeholders and capability claims require final review.
- Linux CI and the replacement Linux Gitleaks installation remain unverified
  after local repair. Remote PR #20 is unchanged until an authorized publication.

## Decisions still required

Choose how to publish the verified local merge to the existing PR branch, then
run and inspect GitHub CI. No push or remote merge is authorized by this task.
Keep main unchanged. See [PR20_CONFLICT_PLAN.md](PR20_CONFLICT_PLAN.md) for the
original plan and [CI_REPAIR_REPORT.md](CI_REPAIR_REPORT.md) for CI repair evidence.

## Historical repair-branch handoff (superseded where noted above)

Source: `6133361`. Statements below such as "no merge started", old main hashes,
pending tests, and unrun workflows describe earlier stages, not current status.
Security limitations remain relevant unless explicitly resolved with evidence.

# Amazon RC1 handoff

## PR #20 conflict decision — 2026-10-13 UTC

Read-only merge-tree analysis found exactly three document conflicts:
`docs/REUSE_PLAN.md`, `docs/amazon/BUILD_LOG.md`, and this handoff.
No merge was started. See [PR20_CONFLICT_PLAN.md](PR20_CONFLICT_PLAN.md).
The owner must explicitly extend the earlier release-only merge permission to
allow merging inspected main `1d10691` into the local `amazon/ci-repair` branch.
Do not push, merge the PR, or modify main under this proposed authorization.


## Local CI repair — 2026-10-13 UTC

Local branch `amazon/ci-repair` in an isolated clone fixes missing MCP CI
dependencies, platform-dependent checkout-report encoding, and the unusable
Gitleaks container reference. See [CI_REPAIR_REPORT.md](CI_REPAIR_REPORT.md)
for actual commands/results and remaining limits. Full local Python regression:
290 passed, 3 existing optional skips. Node: 3 passed. No core/frozen files changed.

**OWNER DECISION / NOT READY TO MERGE:** approve a separate conflict-resolution
plan against current remote main and, later, publication of the repair commit.
Only PR #20 is open; the other unmerged PRs were closed with owner authorization
and all branches retained. No push or merge has been performed in this repair.
Linux workflow execution and remote history scanning remain pending publication.


## RC2 merchant gate pending

Run `powershell -ExecutionPolicy Bypass -File scripts/run_merchant_gate.ps1` from the repository root. The offline injected-product comparison and two isolated tests pass in the restricted environment, but the complete merchant approval test did not finish within the sandbox command window. Do not claim the networked end-to-end gate passed until this command completes locally.

The first owner run reached the replay assertion and confirmed the gateway returned
the stable `CG_PROOF_REPLAYED` reason. The test still expected the superseded
`already consumed` text, and the standalone script used an unpinned global
interpreter. Both test-layer issues are corrected; rerun the gate on the latest
`amazon/final-gate` commit.

The corrected owner rerun passed all 3 merchant tests in 0.76 seconds. The merchant
gate is now complete; only the full Python suite and local-path repository check
remain open in the submission checklist.

## Final local decisions and gates

- D7, D8, and D9 were recorded as YES. The frozen evaluation files were not changed.
- The three historical scanner findings are ignored only by exact fingerprint and owner-classified reason; no broad rule suppression was added.
- Run `scripts/verify_local.ps1`, then `scripts/run_merchant_gate.ps1`, before recording a demo or merging to the submission branch.
- The error-mapping real-client matrix remains pending an unrestricted local run; the sandbox result must not be presented as a pass.
- The owner approved removal of the local absolute paths from `START_HERE.md` and `docs/REUSE_PLAN.md`; both now use portable guidance.
- **FINAL GATE PENDING:** rerun `scripts/submission_check.py` with the pinned environment and Gitleaks 8.30.1 on the exact final commit.
- The latest full owner run had 288 passed, 3 optional-dependency skips, and only the diagnosed evaluation-v2 working-tree byte conversion failure. The final checker validates committed frozen blobs directly and separately runs every other test; it does not modify or waive the frozen manifest.

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

## CI status — 2026-10-11

- `amazon/ci` adds an Ubuntu/Windows Python 3.12 matrix for full Python, Node, and both pip-audit manifests.
- Full-history Gitleaks runs separately with a version-and-digest-pinned image and `--redact`.
- The workflow has not run because no push was performed. Follow `CI.md` after pushing RC1 to the private repository.

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

## Historical main handoff (not current instructions)

Source: `1d1069169e4fd10b5ac887bdcdc827b77b195b92`. Preserved for audit, including original warnings
and decisions. Do not treat old branch hashes, test counts, or pending statuses
as current. The local integration and publication boundary above takes priority.

# Amazon unattended batch handoff

> 🔴 **禁止公开或迁移历史：T2 在完整 Git 历史中发现 3 个 `generic-api-key` 命中。不要 push、公开或迁移历史，直到人工确认并完成合规处置。**

## Task status

| Task | Status | Result/reason |
|---|---|---|
| T0 | DONE | Baseline recorded: Python 245 passed, 3 failed, 1 skipped; Node 3 passed. |
| T1 | BLOCKED | Required temporary clone failed twice with Git/MSYS `0xC0000022`; no `.gitattributes` change. |
| T2 | DONE | gitleaks 8.30.1 scanned 43 commits and found 3 redacted `generic-api-key` findings in one path/commit. |
| T3 | SKIPPED | Required by T2 findings; no migration helper was created. |
| T4 | PARTIAL | Approval gate prohibited applying core code. Review-only design proposal committed; no core test claim. |
| T5 | DONE | Streamable HTTP MCP server, three simulated tools, permanent canary block, SQLite restart replay test, real client tool-list/denial test. |
| T6 | PARTIAL | Native `-32042`, local HTTPS page, completion notification, exact one-time retry, mutation/expiry/self/contact checks pass. Still uses v1 proof and a simulated local contact credential pending commitment-v2 approval. |
| T7 | DONE | Friction logger, submission checker, and separate boundary reports; follow-up commit now uses Git author date and tests rebase-safe classification. |
| T8 | DONE | English submission README draft with all required sections and explicit limitations. |
| T9 | DONE | This handoff, branch inventory, comparisons, decisions, commands, and risks. |

## Branches and latest commits

| Branch | Latest commit |
|---|---|
| `main` | `f18eda53965a349a46c37cc243a7a86e90151f91` |
| `proposal/commitment-v2` | `1fbb196035f327568902475b3e4c95499d4597d2` |
| `amazon/mcp-phase1` | `4b48feb4aa8544844cf13b58cccaa5dd2f7cd4be` |
| `amazon/mcp-phase2` | `bff4e3679026585c93bd306f92f046a7f1aeb7ff` |
| `amazon/tools` | `720681ca776a5933227542045e5882924b5aaee4` |
| `feat/amazon-alexa-mcp-phase1` | T9 self-reference; resolve with `git rev-parse HEAD` |

No branch was pushed, deleted, rebased, reset, or merged. `main` was not modified.

## Test comparison to T0

| Branch/task | Passed | Failed | Skipped | Comparison |
|---|---:|---:|---:|---|
| T0 baseline Python | 245 | 3 | 1 | Baseline |
| T5 full Python | 246 | 3 | 3 | Same 3 failures; isolated environment had 2 more optional skips; 3 MCP targeted tests passed separately. |
| T6 full Python | 252 | 3 | 3 | Same 3 failures; 9 combined MCP tests passed separately. |
| T7 follow-up full Python | 248 | 3 | 1 | Same 3 failures; 3 author-date/tool tests passed. |
| T6 private-key cleanup full Python | 253 | 3 | 3 | Same failures/skips; 10 combined MCP tests passed. |
| Node at T0/T5/T6/T7 | 3 | 0 | 0 | Unchanged. |

The recurring failures are the two Windows spawned-process pipe failures and
`evaluation_v2` manifest mismatch for `blind/scenarios.jsonl`. No new failure
replaced a baseline pass, so no task commit required a revert.

The baseline skip is `test_pipecat_actual_pipeline_and_transcript_boundary` because
the optional `pipecat` package is absent. T5/T6 used an isolated environment that
also lacked optional `onnxruntime`, so `test_silero_real_model_silence_and_isolation`
and `test_sensor_failure_preserves_audio` were the two additional skips. No MCP test
was skipped.

## Decisions required

1. Inspect and resolve the three T2 findings before any public release or history migration. Finding metadata: rule `generic-api-key`, path `scambench/local-check.json`, commit `3b4525ff0ce85beab9bd541f377b442f44e7d27c`.
2. Re-run T1 outside this sandbox. If the clean `core.autocrlf=false` clone still fails its manifest, inspect the differing paths and `git log -- <path>` before deciding whether frozen data or its manifest is wrong.
3. Proposal `1fbb196` was approved. Review the reverted attempt and rerun the original MCP tests outside this environment before authorizing a clean replacement implementation.
4. Decide whether phase 2 may be merged while its stable subject binding remains server-side around a v1 signed proof, or whether merge must wait for commitment v2.
5. Decide the final branch-combination order. No merge was performed automatically.
6. Classify the three historical `generic-api-key` findings as SHA-256 false positives or revoke/rotate them. Until then, the publication gate stays closed.

## Commands to run after return

```powershell
# 1. Reproduce T1 outside the sandbox.
git clone -c core.autocrlf=false <local-repository-path> <temporary-path>
Set-Location <temporary-path>
py -3.12 -m evaluation_v2.verify_inputs

# 2. Re-run a redacted full-history scan before any migration.
gitleaks git --no-banner --redact=100 --report-format json --report-path <outside-repo-report.json>

# 3. Review each isolated branch locally.
git show proposal/commitment-v2
git show amazon/mcp-phase1
git show amazon/mcp-phase2
git show amazon/tools

# 4. Re-run targeted tests on their branches.
git switch amazon/mcp-phase1
py -3.12 -m pytest tests/alexa_mcp/test_phase1.py -q
git switch amazon/mcp-phase2
py -3.12 -m pytest tests/alexa_mcp -q
git switch amazon/tools
py -3.12 -m pytest tests/alexa_mcp/test_tools.py -q
```

Do not run migration or push commands while the red warning at the top remains unresolved.

## Known risks

- Historical possible secrets block public migration.
- A 2026-10-10 redacted all-branch rescan still reports exactly 3 findings at the same rule/path/commit and no new finding.
- The frozen v2 manifest could not be independently validated in the required clean clone.
- Commitment v2 is a design proposal only; its `.patch` intentionally contains marked implementation points and is not apply-ready.
- The MCP adapter must reject v1 to prevent downgrade; Phase 2 must not be described or recorded as cryptographically binding tool name or stable subject until v2 is approved and implemented.
- Phase 2's contact credential, page, certificate, identities, money, and approvals are local simulations, not production identity or payment controls.
- The phase-2 proof is v1; stable `subject` is held in the adapter state rather than signed into the credential.
- The self-signed certificate is suitable only for local development.
- Phase 2 now writes its generated certificate/private key only below Git-ignored `.test-tmp/` and removes the temporary directory on normal exit; no key/certificate extension is tracked on any Amazon work branch.
- The Python SDK client required manual conversion from generic `MCPError` code `-32042` to its specialized URL-elicitation error type.

## 2026-10-10 commitment-v2 follow-up

> 🔴 **Commitment v2 remains unapplied.** Owner approval for proposal `1fbb196` was received, but the implementation attempt on `amazon/commitment-v2` made existing MCP tests time out while starting Uvicorn. The attempt was committed for audit and then reverted as required. The same timeout remained when the original pre-v2 tests were rerun after the revert, so the current environment cannot attribute the failure to v2.

- `amazon/commitment-v2` HEAD: `1385767`.
- Attempt: `afc5e02`; required revert: `a05f675`.
- Owner decision/action: run `amazon/mcp-phase2` MCP tests outside this environment. If they pass, authorize a fresh v2 attempt in a clean worktree or provide startup diagnostics.
- Dependent merchant-injection, UI, resume, and final-gate branches were not started.
- Latest SDK retest confirmed `mcp==2.3.0` still reconstructs `-32042` as generic `MCPError`; the detailed retest and related upstream issues are on the commitment branch's `FRICTION_LOG.md`.

## 2026-10-10 pitch package

- Status: DONE as an evidence-gated draft on `amazon/pitch`.
- Added `DEVPOST.md`, `DEMO_SCRIPT.md`, `QA_BANK.md`, and `WE_WILL_NOT_CLAIM.md`.
- The script explicitly blocks final recording of v2, merchant-injection, and UI scenes until those implementations exist and pass.
- Owner action: provide one primary/public-authority impact source to replace `{{SOURCE_NEEDED}}`; resolve all `{{TBD}}` fields only from the final combined run.
