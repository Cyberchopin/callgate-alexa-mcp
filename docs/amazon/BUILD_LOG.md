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

