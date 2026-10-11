# Amazon build log

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

