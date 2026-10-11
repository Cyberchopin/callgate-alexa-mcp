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

