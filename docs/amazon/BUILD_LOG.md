# Amazon build log

## BUILD-PR20-MERGE-001 — 2026-10-13

- Owner approved local main-to-`amazon/ci-repair` integration only; no push,
  GitHub PR merge, main change, or security implementation was authorized.
- Ran `git merge --no-ff --no-commit 1d1069169e4fd10b5ac887bdcdc827b77b195b92`.
  Raw conflict diagnostics:
  `CONFLICT (content): Merge conflict in docs/REUSE_PLAN.md`;
  `CONFLICT (add/add): Merge conflict in docs/amazon/BUILD_LOG.md`;
  `CONFLICT (add/add): Merge conflict in docs/amazon/HANDOFF.md`.
- Preserved repair-branch REUSE_PLAN guidance, both complete build logs, and
  both handoffs with explicit historical labels and current-status precedence.
  Automatically imported pitch documents remain drafts, not runtime evidence.
- No unmerged index entries or conflict markers remain in the resolved files.
  Staged differences are documentation only. Core and frozen-evaluation diff
  check returned exit 0 (no differences).
- Existing incoming whitespace warnings were retained: eight final blank-line
  warnings and one Markdown two-space line break in DEMO_SCRIPT_DRAFT.md.
  `git diff --cached --check` is therefore not claimed clean. No content or
  executable proposal patch was rewritten merely to remove these warnings.
- Ran `scripts/verify_ci_repair.ps1` with the existing pinned environment:
  `21 passed in 13.04s` focused; `290 passed, 3 skipped, 1 warning in 30.06s`
  full Python; Node `3 passed, 0 failed`; claims
  `registered=39 unresolved_or_inconsistent=0`; script exit 0.
- The three skips remain optional onnxruntime/pipecat tests. The warning remains
  the AnyIO BlockingPortal deprecation. No prior pass regressed.
- Pre-commit local Gitleaks 8.30.1 scanned 113 reachable commits with complete
  redaction and unchanged exact fingerprint ignores: `no leaks found`, exit 0.
  The new merge's history requires a post-commit scan before handoff.
- Remote main was rechecked as `1d1069169e4fd10b5ac887bdcdc827b77b195b92`.
  GitHub CI has not been rerun. No remote write was made.


## BUILD-PR20-CONFLICT-001 — 2026-10-13 UTC

- Read-only fetch first failed under the sandbox:
  `fatal: unable to access '<repository-url>': getaddrinfo() thread failed to start`.
  Approved host execution succeeded on retry. Remote main was fetched as
  `1d1069169e4fd10b5ac887bdcdc827b77b195b92`; no branch was moved.
- `git merge-tree --write-tree HEAD FETCH_HEAD` produced a trial tree, not a
  merge commit, and reported content conflict in `docs/REUSE_PLAN.md` and
  add/add conflicts in `docs/amazon/BUILD_LOG.md` and `docs/amazon/HANDOFF.md`.
  Working tree and index were not merged. The resulting tree differs only in
  documentation; no frozen or core-security changes are proposed.
- Added a resolution plan and owner decision in HANDOFF; actual merge remains
  outside the earlier release-branch-only permission.
- Full regression: `python -X utf8 -m pytest -q -rs --basetemp .test-tmp/conflict-plan`:
  `290 passed, 3 skipped, 1 warning in 31.62s`. Same pass/skip counts as the
  previous local repair run. Node: 3 passed, 0 failed. Diff whitespace check
  passed. No code changed in this task.


## BUILD-CI-REPAIR-001 — 2026-10-13 UTC

- Created an isolated local clone at readme-final `5a0e629` and local branch
  `amazon/ci-repair`; the original checkout was not changed.
- The first clone attempt was sandbox-blocked:
  `fatal error - NtCreateDirectoryObject(\BaseNamedObjects\msys-2.0S5-1888ae32e00d56aa): 0xC0000022`.
  Retrying with approved host execution succeeded.
- An initial sandbox pytest attempt produced setup errors and was interrupted;
  it has no complete test count and is not a valid baseline.
- The host baseline exposed a command-preparation error: the `.test-tmp` parent
  had not been created in the fresh clone. Raw error with the machine-specific
  path replaced: `FileNotFoundError: [WinError 3] The system cannot find the path specified: '<repo>/.test-tmp/ci-baseline-host'`.
  Actual result: `1 failed, 241 passed, 3 skipped, 1 warning, 47 errors in 8.88s`.
  This run is not used as a clean product baseline. The failure also reproduced
  `UnicodeDecodeError: 'utf-8' codec can't decode byte 0x97 in position 38: invalid start byte`.
- Created the temporary parent directory before post-repair verification. The
  new reproduction script also creates it before pytest. No skip or xfail added.
- Checkout encoding tests: `8 passed in 0.97s`.
- Full regression command: `python -X utf8 -m pytest -q -rs --basetemp .test-tmp/ci-fixed`.
  Output: `290 passed, 3 skipped, 1 warning in 34.75s`.
- Cryptography compatibility plus MCP phase1/phase2:
  `13 passed in 14.35s`.
- Node: `tests 3`, `pass 3`, `fail 0` before and after repair.
- Claims: `registered=39 unresolved_or_inconsistent=0`.
- Local Gitleaks 8.30.1 with `--redact=100 --log-opts=--all` and the existing
  exact ignore file: `111 commits scanned`, `no leaks found`, exit 0.
- The Actions scanner failure was an image-launch failure, not a leak finding:
  `docker: unsupported media type application/vnd.in-toto+json`, exit 125.
  The replacement Linux release archive SHA-256 was verified against official
  release metadata; its Linux installation has not yet run in CI.
- Remote main was read-only checked at `1d1069169e4fd10b5ac887bdcdc827b77b195b92`;
  PR #20 is still conflicted. No push, merge, or remote rerun was performed.
- More details and limitations: [CI_REPAIR_REPORT.md](CI_REPAIR_REPORT.md).
- End-to-end `scripts/verify_ci_repair.ps1` execution completed with exit 0:
  `21 passed in 14.14s` focused; `290 passed, 3 skipped, 1 warning in 33.54s`
  full Python; Node 3/3; claims 39/0; Gitleaks 111 commits, no remaining findings.
  Gitleaks printed `Unknown SCM platform` because this clone's origin is local;
  it still completed the history scan. No GitHub scan completion is claimed.


## BUILD-STABILIZE-OWNER-003 — 2026-10-11

- Owner reran the final MCP gate on `amazon/stabilize` commit `2804f8a`.
- Combined phase 1 and phase 2 real-client result: **10 passed in 20.66 seconds**.
- Targeted Bandit result for `scripts/mcp_test_process.py`: **0 high, 0 medium, 2 low**, both high confidence; **0 `nosec`** and 0 skipped files.
- The two low findings are the explicit `subprocess` import and `Popen` invocation used to satisfy the required independent test-server process. The command is an argument list built from the current Python interpreter and test-owned values, with no shell invocation or untrusted command string.

## BUILD-STABILIZE-OWNER-002 — 2026-10-11

- Owner compatibility result: **3 passed in 2.76 seconds** under `cryptography 50.0.0`.
- Full Python: **277 passed, 1 failed, 3 skipped** in 34.62 seconds. The only failure was the documented evaluation-v2 working-tree line-ending mismatch.
- Regression subset excluding that frozen-input check: **275 passed, 3 skipped, 1 deselected** in 31.06 seconds; no previously passing test failed.
- Node: **3 passed, 0 failed, 0 skipped**.
- Phase 1 real-client integration: **3 passed** in 5.37 seconds.
- Phase 2 URL-elicitation integration: **7 passed** in 16.64 seconds.
- Root and MCP pip-audit each reported `No known vulnerabilities found`.
- Bandit scanned 2,879 lines: 0 high, 3 medium, 27 low. Two new medium findings belonged to the test-only MCP health probe (`ssl._create_unverified_context` and generic `urlopen`); they were removed by trusting the generated local certificate and using fixed HTTP/HTTPS connection classes. The pre-existing XML parser medium remains governed by `BANDIT_TRIAGE.md`.

## BUILD-STABILIZE-OWNER-001 — 2026-10-11

- The owner ran `scripts/verify_local.ps1` outside the sandbox on both RC1 and `amazon/stabilize` under `cryptography 50.0.0`; compatibility tests passed **3/3** in 2.76 and 2.72 seconds respectively.
- RC1 full Python: **274 passed, 4 failed, 3 skipped**. Three failures were stale red-team expectations that contradicted the approved Origin, Referrer-Policy, and per-subject rate-limit hardening; the fourth was the known evaluation-v2 working-tree line-ending mismatch.
- RC1 regression subset: **272 passed, 3 failed, 3 skipped, 1 deselected**. The script correctly stopped before Node and dedicated phase tests.
- Stabilize full Python: **275 passed, 3 failed, 3 skipped**. Failures were the evaluation-v2 line-ending mismatch, one stale rate-limit characterization test, and the cross-contact mutation being rejected through MCP SDK `-32000` (`SSE stream ended without a response`) rather than `-32042`.
- Stabilize regression subset: **273 passed, 2 failed, 3 skipped, 1 deselected**. The script again stopped before Node and dedicated phase tests.
- Both former Windows spawned-process baseline failures passed in the owner's environment. No core security or frozen evaluation file was changed in response.

## BUILD-RC1-INTEGRATION-002 — 2026-10-11

- Integrated phase 1, phase 2, dependency upgrade, evaluation, red-team, and UI work into `release/amazon-rc1` in the requested order.
- Phase 1 required reapplying the previously reverted merge because Git correctly considered the original source branch already merged; commit `07a18fe` reverses only that earlier revert.
- Evaluation targeted result: **7 passed in 0.91 seconds**.
- Red-team targeted run completed two tests, then hung twice at `test_approval_page_ignores_query_forgery_and_get_does_not_mutate`; no suite pass is claimed.
- UI targeted run produced no result before the 30-second sandbox limit; no pass is claimed.
- Node result after all merges: **3 passed, 0 failed, 0 skipped** in 59.7216 milliseconds.
- Phase 1 and phase 2 currently fail to start their local MCP test server in this sandbox. The stabilization branch owns that test-harness repair; local verification remains required.
- Dependency pins agree on `cryptography==50.0.0`; the MCP requirements pin `mcp==2.3.0`.

## BUILD-001 — 2026-10-10

- Task: Correct the pre-existing-work cutoff to use Git author dates.
- Command: `py -3.12 -m pytest tests/alexa_mcp/test_tools.py -q --basetemp .test-tmp/tools-author-date`
- Result: pytest stopped during setup with three `FileNotFoundError: [WinError 3]` errors because the parent `.test-tmp` directory did not exist. No test body ran.
- Action: Create the permitted project-local parent directory and retry once.

## BUILD-002 — 2026-10-10

- Task: Run the corrected author-date generator tests.
- Result: 2 passed and 1 failed. The date-only LA Hacks cutoff triggered `zoneinfo._common.ZoneInfoNotFoundError: 'No time zone found with key America/Los_Angeles'` because this Windows Python installation has no IANA `tzdata` package.
- Action: Avoid a new dependency by defining a date-only competition cutoff as `-07:00`; explicit offsets remain unchanged.

## BUILD-003 — 2026-10-10

- Task: Compare the tools branch with the full Python baseline and print skip reasons.
- Result: Collection stopped with `ModuleNotFoundError: No module named 'hypothesis'`; no test total was produced.
- Action: Attempt installation only in an ignored verification environment under the permitted `integrations/alexa_mcp/` path.

## BUILD-004 — 2026-10-10

- Task: Create the isolated verification environment.
- Result: `venv` failed while running `ensurepip --upgrade --default-pip`; the resulting interpreter reported `No module named pip`.
- Action: Stopped dependency setup after the permitted retry path failed. No global package installation was attempted.

## BUILD-005 — 2026-10-10

- Task: Verify the author-date correction and compare it with T0.
- Targeted Python result: **3 passed** in 2.65 seconds.
- Full Python result using the same external verification dependency path as T0: **248 passed, 3 failed, 1 skipped** in 17.64 seconds. The same two Windows spawned-process failures and frozen `evaluation_v2` manifest mismatch remained; no prior pass became a failure.
- Skip: `tests/test_integrations.py::test_pipecat_actual_pipeline_and_transcript_boundary`, because `pipecat` is not installed.
- T5/T6 extra skips identified from their isolated dependency set and test guards: `test_silero_real_model_silence_and_isolation` and `test_sensor_failure_preserves_audio`, both guarded by missing optional `onnxruntime`. The MCP tests themselves were not skipped.
- Node result: **3 passed, 0 failed, 0 skipped**.
# RC1 integration gate — 2026-10-10

- Created `release/amazon-rc1` from `main` at `f18eda5`.
- Merged `amazon/tools` with `--no-ff`; targeted result: `3 passed in 3.58s`.
- The tools full-suite run emitted 18 progress dots and then produced no output for more than 90 seconds; it was interrupted and no total is claimed.
- Merged `amazon/mcp-phase1` with `--no-ff` after one minimal add/add conflict resolution in `FRICTION_LOG.md`.
- Phase-1 targeted run failed twice. The second run reported `RuntimeError: MCP test server did not start` and `1 failed in 12.58s`.
- Because the phase-1 test had passed on its source branch, merge commit `30064b1` was reverted by `47ec401`. Dependent phase-2 and later merges were not attempted.

## BUILD-RC1-RETRY-001 — 2026-10-10

- D1 through D6 were explicitly approved and the phase-1 gate was retried without changing `main`.
- First self-contained attempt failed before tests because Windows `venv` could not complete `ensurepip`; the incomplete environment reported `No module named pip`.
- The retry moved temporary files into the retained worktree. MCP 2.3.0 and its dependencies installed successfully, but the phase-1 requirements file did not include pytest; execution stopped with `No module named pytest`.
- Per the two-failure rule, no third run was made. No phase-1 or full-suite pass is claimed.
- The retained gate worktree is `.rc1-phase1-gate`. The script now installs pinned `pytest==9.1.1` for the owner's next local run.

# Amazon phase-2 build log

## BUILD-UI-HARDENING-001 — 2026-10-10

- D2, D3, and D4 were explicitly approved.
- Added MCP-layer per-subject challenge issuance windows matching the existing five-per-minute and thirty-per-hour demo limits.
- Added browser Origin enforcement while preserving bearer-only handling for clients that send no Origin.
- Added `Referrer-Policy: no-referrer` to UI and approval responses, plus URL/body/log token-redaction assertions.
- First test attempt stopped during collection because the available tool environment could not import `pywintypes`.
- Second attempt repaired that path but stopped because the available MCP package lacked `mcp.server.mcpserver`.
- No passing result is claimed. Run `powershell -ExecutionPolicy Bypass -File scripts/run_ui_hardening_gate.ps1` from the repository root.

## BUILD-PHASE2-001 — 2026-10-10

- Task: Verify runtime cleanup for the generated local HTTPS private key.
- First run: test collection stopped with `ModuleNotFoundError: No module named 'httpx2'` under the global interpreter.
- Second run: the existing MCP virtual environment ran 6 existing tests successfully, but the new cleanup test failed with `PermissionError: [Errno 13] Permission denied` when Windows `TemporaryDirectory` selected the sandbox package temp path.
- Action: Use the already Git-ignored project `.test-tmp/` directory as the default temporary parent and inject a writable test parent.

## BUILD-PHASE2-002 — 2026-10-10

- Targeted cleanup result: **7 passed** in 2.85 seconds.
- Combined Phase 1/2 MCP result: **10 passed** in 13.68 seconds.
- Full Python result: **253 passed, 3 failed, 3 skipped** in 14.19 seconds. The failures and optional-integration skips exactly match the prior Phase 2 run; no previous pass became a failure.
- Node result: **3 passed, 0 failed, 0 skipped**.
- Tracked-key check: no `.pem`, `.key`, `.p12`, or `.pfx` file is tracked on any Amazon work branch.

## BUILD-DEPENDENCY-001 — 2026-10-11

- Task: Generate an Ed25519 compatibility vector with the pre-upgrade dependency.
- First install attempt failed because pip could not write its sandbox temporary directory: `OSError: [Errno 13] Permission denied`.
- Retry with a project-local temporary directory succeeded with `cryptography 46.0.5`; the committed fixture contains only the public key, message, signature, and generating version. No private key was recorded.

## BUILD-DEPENDENCY-002 — 2026-10-11

- Task: Install the selected `cryptography 50.0.0` environment and run compatibility tests.
- Attempt 1 ended without completing the environment; inspection showed `cryptography 50.0.2` still installed and `No module named pytest`.
- Attempt 2 used a project-local target directory but also ended before installing packages; inspection returned `ModuleNotFoundError: No module named 'cryptography'`.
- Per the two-failure rule, sandbox installation and phase/full regression stopped. No compatibility, phase1, phase2, full Python, or Node comparison is claimed yet.

## BUILD-DEPENDENCY-003 — 2026-10-11

- Task: Run post-upgrade pip-audit.
- pip-audit 2.10.1 could not create its temporary virtual environment and raised `PermissionError: [WinError 5] Access is denied` followed by `VirtualEnvError: Couldn't execute in a temporary directory`.
- A project-local `TMP`/`TEMP`/`TMPDIR` retry emitted the `--no-deps` and `pip-compile` warnings but no audit result. No clean audit is claimed.

## BUILD-DEPENDENCY-004 — 2026-10-11

- Task: Re-run static analysis and triage findings.
- Bandit 1.9.4 scanned 2,738 lines: 0 high, 1 medium, 25 low, all 26 high confidence, 0 `nosec`, 0 skipped files.
- The owner-provided 1 medium and 20 low are still present; five additional low findings belong to tooling now present in RC1. All 26 are individually dispositioned in `BANDIT_TRIAGE.md`.

## BUILD-DEPENDENCY-005 — 2026-10-11

- Task: Validate the new test logic independently of the blocked 50.0.0 environment.
- Initial HTTPS test failed with `TypeError: SSLContext.wrap_socket() got an unexpected keyword argument 'certfile'`; the test was corrected to call `load_cert_chain()` before wrapping the socket.
- Retry under the already installed `cryptography 49.0.0`: **2 passed, 1 deselected** in 2.71 seconds. This validates the old Ed25519 vector and HTTPS test mechanics, but it is not the required 50.0.0 acceptance run.
- Full Node result: **3 passed, 0 failed, 0 skipped** in 60.3131 ms, matching the previously recorded Node baseline of 3 passed.

## BUILD-DEPENDENCY-006 — 2026-10-11

- Task: Review the owner's first outside-sandbox run of `scripts/verify_local.ps1`.
- Confirmed `cryptography 50.0.0`; dependency compatibility result: **3 passed** in 2.66 seconds.
- Full Python collection stopped with `ModuleNotFoundError: No module named 'hypothesis'`; the script had omitted the existing `requirements-safety.txt` input.
- Node result: **3 passed, 0 failed, 0 skipped**.
- Phase1 and phase2 were not run because the script looked for worktrees inside the repository instead of beside it.
- Both pip-audit invocations returned `No known vulnerabilities found`.
- Bandit reproduced 0 high, 1 medium, 25 low, all high confidence, 0 `nosec`, and 0 skipped files.

## BUILD-DEPENDENCY-007 — 2026-10-11

- Task: Correct the local verification script and rerun the dependency gate.
- Script corrections: install `requirements-safety.txt`; find the two retained worktrees beside the repository; stop on native-command failures under Windows PowerShell 5.1; accept only the three recorded baseline failures before running the remaining regression subset.
- Dependency compatibility: **3 passed** under `cryptography 50.0.0` in 3.06 seconds.
- Full Python: **249 passed, 3 failed, 3 skipped** in 19.69 seconds. The failures are the same two Windows spawned-process failures and frozen `evaluation_v2` manifest mismatch recorded in the baseline.
- Previously passing regression subset: **249 passed, 3 skipped, 1 deselected** in 15.85 seconds. No previously passing test became a failure.
- Skip reasons: two tests require optional `onnxruntime`; one requires optional `pipecat`. The two `onnxruntime` skips match the previously documented isolated MCP dependency behavior.
- Node: **3 passed, 0 failed, 0 skipped** in 62.1353 ms.
- Phase1 with `cryptography 50.0.0`: **3 passed** in 2.27 seconds.
- Phase2 with `cryptography 50.0.0`: **10 passed** in 4.13 seconds.
- The in-sandbox repeat stalled during pip-audit and was interrupted without a new result; the owner's immediately preceding run already supplied two clean audit results for unchanged manifests.
- High-severity Bandit gate: exit code 0.
 
## EVAL-001 — 2026-10-10

- Task: deterministic checkout sensitivity evaluation.
- Generation: `python -m evaluation_checkout.run` completed and wrote JSON, Markdown, and two SVG figures.
- Targeted result: `7 passed in 0.89s`.
- Claims check: `registered=32 unresolved_or_inconsistent=0`.
- Full Python result: `246 passed, 3 failed, 3 skipped in 9.90s`.
- Existing failures: two Windows spawned-process pipe failures in `tests/test_review_process.py`; frozen `evaluation_v2` manifest mismatch for `blind/scenarios.jsonl`. No frozen evaluation file was changed.
- Skips: missing optional `onnxruntime` (two tests) and `pipecat` (one test); none concerns MCP, HTTPS, or elicitation.
- Node result: `3 passed, 0 failed`.
- Environment correction: the first command used a repository-local virtual-environment path that does not exist on this branch. The existing environment is one directory above the checkout; rerunning there succeeded.
# Red-team build record — 2026-10-10

- First collection failed because `PolicyBlocked` is defined in `server.app` but is not exported by the package. The test import was corrected.
- The next run had one test-authoring error because `anyio.run` does not accept keyword arguments. A local async wrapper corrected it.
- Targeted result: **7 passed in 1.15s**.
- Full Python result: **260 passed, 3 failed, 3 skipped in 14.45s**. The failures are the two known Windows spawned-process pipe failures and the frozen `evaluation_v2` manifest mismatch; no frozen file was changed.
- Skip reasons: missing optional `onnxruntime` (two tests) and `pipecat` (one test); none involves MCP, HTTPS, or elicitation.
- Node result: **3 passed, 0 failed, 0 skipped**.
# UI build record — 2026-10-10

- Added a no-build simulated assistant page, independent contact page, collapsible proof panel, fixed offline fixture/reset behavior, and server-derived transaction fields.
- Targeted UI plus phase-2 result: **10 passed in 12.85s**.
- Full Python result: **256 passed, 3 failed, 3 skipped in 14.42s**. The three failures are the known Windows spawned-process failures and frozen `evaluation_v2` manifest mismatch; no frozen file was changed.
- Skip reasons: missing optional `onnxruntime` (two) and `pipecat` (one); none involves MCP, HTTPS, or elicitation.
- Node result: **3 passed, 0 failed, 0 skipped**.
- Screenshot attempt: the Codex in-app browser could not reach the loopback preview and returned `net::ERR_CONNECTION_TIMED_OUT`. No screenshot was generated or claimed. Session control cleanup was denied by the current permission policy, and Windows CIM process inspection then failed because the CIM resource was unavailable.

## Merchant injection refresh — 2026-10-11

- Existing `amazon/merchant-injection` history was retained and updated by merging RC2; no branch was deleted or rewritten.
- Offline comparison command completed: unguarded `2/2`, CallGate `0/2` simulated unauthorized actions.
- `scripts/check_claims.py`: `registered=33 unresolved_or_inconsistent=0`.
- Two network-free merchant tests passed in 1.35 seconds.
- The complete merchant test file produced no output before the 30-second sandbox command boundary. It is not claimed as passed and remains in the local verification gate.

## ApprovalBench Lite — 2026-10-11

- Generator output: `wrote 3x3 matrix; D5 attack successes=0/300`.
- Focused tests: `3 passed in 0.52s`.
- The benchmark is a fixed-seed author simulation. Latency and legitimate-completion values are explicit simulation parameters, not human observations.

## Final-gate secret scan — 2026-10-11

- Docker was unavailable: `failed to connect to the docker API ... The system cannot find the file specified.`
- Downloaded Gitleaks 8.30.1 from its GitHub release and verified the release archive against the published SHA-256 checksum.
- First full-history redacted scan: 100 commits, 3 owner-classified `generic-api-key` findings in `scambench/local-check.json` at commit `3b4525ff0ce85beab9bd541f377b442f44e7d27c`. No matched values were printed or recorded.
- Added the three exact fingerprints to `.gitleaksignore` with the owner-classification rationale.
- Second full-history redacted scan: 100 commits, 0 remaining findings, exit code 0.

## Final submission checklist — 2026-10-11

- Passed: LICENSE, required README sections, full-history redacted scan, pre-existing-work freshness, no tracked private-key files, no trademark-named graphics, friction raw-error fields, and run instructions.
- Python test check initially failed before execution because the checklist used the global Python, which lacks `httpx2`; the checklist now uses its own interpreter. The exact error was `ModuleNotFoundError: No module named 'httpx2'`.
- Repository path check found pre-existing local paths in `START_HERE.md` and `docs/REUSE_PLAN.md`. They are outside the task's allowed edit paths, so the final gate remains failed pending owner-approved cleanup.
- The full suite under the pinned environment did not finish within the restricted command window; no final-branch all-tests pass is claimed.

## Owner final-gate rerun — 2026-10-11

- `cryptography 50.0.0`; compatibility: 3 passed in 2.73 seconds.
- MCP phase 1: 3 passed in 5.69 seconds; phase 2: 7 passed in 4.58 seconds; combined: 10 passed in 9.76 seconds.
- Stable MCP error mapping: 5 passed in 6.41 seconds.
- Merchant suite reached application behavior and returned `403 BLOCKED: CG_PROOF_REPLAYED`; the sole failure was a stale assertion for the old `already consumed` text. The assertion now targets the stable reason code.
- The standalone merchant gate used the global interpreter and failed collection with `ModuleNotFoundError: No module named 'mcp'`. The script now uses the same pinned environment as `verify_local.ps1`.
- Corrected merchant gate rerun: 3 passed in 0.76 seconds.
- Offline comparison remained unguarded 2/2 and CallGate 0/2; claim registry remained `registered=34 unresolved_or_inconsistent=0`.
- Submission check passed 10 checks and failed 2: full Python tests and local absolute paths. The checker now prints the captured pytest failure and only the relative filenames containing local paths.
- The next owner run showed widespread pytest setup errors because the submission checker omitted the required project-local `--basetemp`. The checker now uses `.test-tmp/submission-check`, matching the established Windows verification rule; these setup errors are not classified as product regressions.
- The owner approved cleanup outside the prior Amazon-only path scope. Machine-specific absolute paths were replaced in `START_HERE.md` and `docs/REUSE_PLAN.md` with repository-relative or generic guidance; no execution logic changed.
- After project-local `--basetemp` was restored, the owner run produced 288 passed, 1 failed, and 3 skipped in 29.78 seconds. The sole failure was the diagnosed current-worktree line-ending conversion for `evaluation_v2/blind/scenarios.jsonl`; all other tests passed. The final checker now requires both the deselected regression suite and direct SHA-256 validation of every committed `evaluation_v2` blob before treating this known checkout artifact as cleared.

## Historical main workstream log (preserved during PR #20 resolution)

Source: `1d1069169e4fd10b5ac887bdcdc827b77b195b92`. The entries below are historical observations,
not current acceptance results. Their original identifiers are preserved and
may overlap identifiers from other branches above. No old failure is being
silently reclassified as a pass.

# Amazon workstream build log

This log contains only commands and results observed during the Amazon workstream. It does not replace the repository's historical root `BUILD_LOG.md`.

## BUILD-001 — T0 baseline — 2026-10-10 (America/Los_Angeles)

- Git base: `f18eda5` on local branch `feat/amazon-alexa-mcp-phase1`; worktree was clean.
- Python: `3.12.6` via `py -3.12`.
- Node.js: `v24.18.0`; npm: `11.16.0`.
- `python.exe` alias check failed before tests:

```text
Program 'python.exe' failed to run: An error occurred trying to start process '<LOCAL_WINDOWS_APPS>/python.exe' ... The file cannot be accessed by the system.
```

- `hypothesis` was initially absent. The first install attempt failed because network access was unavailable:

```text
ERROR: Could not find a version that satisfies the requirement hypothesis (from versions: none)
ERROR: No matching distribution found for hypothesis
```

- After network permission was granted, `hypothesis==6.168.5` and `sortedcontainers==2.4.0` were installed into the project-specific external directory `work/.verification-deps`; global Python was not modified.
- Python command: `py -3.12 -m pytest --basetemp <workspace>/work/.pytest-baseline -q`, with `work/.verification-deps` on `PYTHONPATH`.
- Python result: **245 passed, 3 failed, 1 skipped** in 14.54 seconds.
- Existing failures:
  - `tests/test_review_process.py::test_two_process_approval_then_unavailable_reviewer` — spawned child ended its pipe in the sandbox.
  - `tests/test_review_process.py::test_three_process_routing_switch_and_cross_contact_isolation` — spawned child ended its pipe in the sandbox.
  - `tests/test_v2_inputs.py::test_input_schema_and_manifest` — `ValueError: manifest mismatch: blind/scenarios.jsonl`.
- Node command: `node --test tests/review_ui.test.cjs`.
- Node result: **3 passed, 0 failed, 0 skipped**.

## BUILD-002 — T1 temporary-clone manifest check — 2026-10-10 (America/Los_Angeles)

- Attempted twice with `git clone -c core.autocrlf=false`, once with `--no-local` and once with the normal local-clone path.
- Both attempts failed before a checkout was created, so the manifest verifier was not run and `.gitattributes` was not added.
- Raw error from both attempts:

```text
sh.exe: *** fatal error - NtCreateDirectoryObject(\BaseNamedObjects\msys-2.0S5-1888ae32e00d56aa): 0xC0000022
fatal: Could not read from remote repository.
```

- Per the two-failure rule, T1 stopped. No frozen evaluation file was read or modified by this task.

## BUILD-003 — T2 full-history secret scan — 2026-10-10 (America/Los_Angeles)

- Tool: official `gitleaks 8.30.1` Windows x64 release; the downloaded archive was checked against the release checksum file before execution.
- Scope: Git history reachable through all refs (`gitleaks git`); **43 commits** scanned.
- Result: **3 findings**.
- Redacted finding metadata only:

| Count | Rule | Path | Commit |
|---:|---|---|---|
| 3 | `generic-api-key` | `scambench/local-check.json` | `3b4525ff0ce85beab9bd541f377b442f44e7d27c` |

- No secret value or matching line was printed or copied into repository files.
- Consequence: T3 migration helper was skipped as required.

## BUILD-004 — T4 commitment-v2 proposal — 2026-10-10 (America/Los_Angeles)

- Branch: `proposal/commitment-v2`, based on `main`.
- Proposal commit: `42cda8d8107f84d05817e47f2bf68adcf29916ab`.
- Applying the executable core diff was rejected by the pre-existing approval gate. No core file or test was modified.
- A review-only design diff and risk note were committed under `docs/amazon/`; the patch explicitly identifies itself as not apply-ready and not tested.
- No tests were claimed for this proposal. The working branch was restored after the commit.

## BUILD-005 — T5 phase 1 MCP server — 2026-10-10 (America/Los_Angeles)

- Branch/commit: `amazon/mcp-phase1` at `4b48feb4aa8544844cf13b58cccaa5dd2f7cd4be`.
- First MCP run: 3 failed because SDK 2.3.0 hid ordinary exception text behind `UnexpectedToolError`. The integration switched expected failures to SDK `ToolError` and reran once.
- Targeted result: **3 passed** in 1.75 seconds.
- Full Python result in the isolated MCP environment: **246 passed, 3 failed, 3 skipped**. The three failures exactly match T0; no previously passing test became a failure. Two additional optional integrations skipped because this isolated environment did not include all global optional packages.
- Node result: **3 passed, 0 failed, 0 skipped**.
- The isolated dependency install reported unrelated package-version conflicts involving `pyppeteer`, OpenTelemetry, and `realtime`; no repository dependency file was changed in response.

## BUILD-006 — T6 URL elicitation — 2026-10-10 (America/Los_Angeles)

- Branch/commit: `amazon/mcp-phase2` at `c9dd7c32d782299b596b4e7261463af79efb8036`.
- Initial phase-2 test result: **6 failed**. The client surfaced server `-32042` as generic `MCPError`, and one nested temporary database directory was absent.
- After one correction, phase-2 targeted result: **6 passed** in 2.82 seconds.
- Combined phase-1/phase-2 MCP result: **9 passed** in 3.77 seconds.
- Full Python result: **252 passed, 3 failed, 3 skipped**. The three failures exactly match T0; no previously passing test became a failure.
- Node result: **3 passed, 0 failed, 0 skipped**.

## BUILD-007 — T7 support tools — 2026-10-10 (America/Los_Angeles)

- Branch/commit: `amazon/tools` at `c4d80ca80f70a154834c7bcace80a389692d646a`.
- Targeted tool tests: **2 passed** in 1.55 seconds.
- Full Python result: **247 passed, 3 failed, 1 skipped**. The three failures exactly match T0; no previously passing test became a failure.
- Node result: **3 passed, 0 failed, 0 skipped**.
- Both Git-derived boundary reports were generated: Amazon cutoff `2026-08-31T10:15:00-07:00` and separate LA Hacks cutoff `2026-10-17`.

## BUILD-008 — T8 README draft — 2026-10-10 (America/Los_Angeles)

- Branch/commit: `feat/amazon-alexa-mcp-phase1` at `96376131450f81d1ed6b309d06b383f747f6d001` before the T9 update.
- Static heading check: **7 of 7 required sections present**.
- No executable code changed; no test result was claimed for prose.

## BUILD-009 — T7 author-date correction — 2026-10-10 (America/Los_Angeles)

- Branch/commit: `amazon/tools` at `720681ca776a5933227542045e5882924b5aaee4`.
- The first targeted run stopped because `.test-tmp` did not exist. After creating it, Windows Python lacked IANA `tzdata`, so the date-only LA cutoff was defined explicitly as `-07:00` without adding a dependency.
- A global-Python full run then stopped on missing `hypothesis`; an attempted project venv failed in `ensurepip`. Reusing the same external verification dependency directory as T0 succeeded.
- Targeted result: **3 passed**. Full Python result: **248 passed, 3 failed, 1 skipped**. Node result: **3 passed, 0 failed, 0 skipped**. No prior pass became a failure.
- The one baseline skip is the optional `pipecat` test. The two additional T5/T6 skips are the optional `onnxruntime` tests; no MCP test was skipped.

## BUILD-010 — history rescan and Phase 2 key cleanup — 2026-10-10 (America/Los_Angeles)

- Gitleaks 8.30.1 all-branch scan with 100% redaction: **3 findings**, all `generic-api-key`, path `scambench/local-check.json`, commit `3b4525ff0ce85beab9bd541f377b442f44e7d27c`; no new finding.
- Tracked-file inspection across all five Amazon work branches found no `.pem`, `.key`, `.p12`, or `.pfx` file.
- Phase 2 global-Python collection first stopped on missing `httpx2`; the existing MCP venv then exposed a sandbox `PermissionError` for the OS temp directory. The implementation now uses Git-ignored `.test-tmp/` and removes the generated certificate/key directory on normal exit.
- Branch/commit: `amazon/mcp-phase2` at `bff4e3679026585c93bd306f92f046a7f1aeb7ff`.
- Targeted result: **7 passed**. Combined MCP result: **10 passed**. Full Python result: **253 passed, 3 failed, 3 skipped**. Node result: **3 passed, 0 failed, 0 skipped**. No prior pass became a failure.

## BUILD-011 — English submission package — 2026-10-10 (America/Los_Angeles)

- Added an English Devpost draft, evidence-gated three-minute script, judge Q&A bank, and explicit non-claims list.
- Full Python result: **242 passed, 4 failed, 3 skipped**. The two spawned-process failures and frozen-manifest mismatch match known baseline/environment failures. A rate-limit boundary test initially returned `Retry-After: 61` instead of its asserted maximum `60`; its immediate isolated rerun passed (`1 passed in 0.88s`) without a code change, so it is recorded as timing-sensitive rather than repaired in core code.
- Skip reasons: optional `onnxruntime` (two) and `pipecat` (one); none involves MCP, HTTPS, or elicitation.
- Node result: **3 passed, 0 failed, 0 skipped**.
- Documentation path scan found no local username or absolute home path.

