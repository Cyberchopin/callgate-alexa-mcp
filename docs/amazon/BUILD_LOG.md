# Amazon phase-2 build log

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

## BUILD-COMMITMENT-V2-RETRY-001 — 2026-10-10

- Owner decisions D1 through D6 were explicitly approved.
- The approved v2 implementation was reapplied on `amazon/commitment-v2-retry`; it has not been merged into the release candidate.
- First gate attempt stopped before collection: `No module named pytest` in the existing verification environment.
- Second gate attempt stopped during collection: `ModuleNotFoundError: No module named 'mcp'` in the global Python environment.
- Per the two-failure rule, testing stopped. No v2 pass or regression claim is made.
- Run `powershell -ExecutionPolicy Bypass -File scripts/run_v2_retry_gate.ps1` from the repository root to create an isolated fixed-dependency environment and execute the core, MCP, and full gates.


## BUILD-COMMITMENT-V2-001 — 2026-10-10

- Task: First targeted commitment-v2 run.
- Result: collection stopped before tests with `ImportError: cannot import name 'PolicyBlocked' from 'integrations.alexa_mcp.server'`.
- Action: Import the exception from its defining `server.app` module; no production behavior changed for this correction.

## BUILD-COMMITMENT-V2-002 — 2026-10-10

- Task: Targeted v2/core/MCP verification after the import correction.
- Result: **15 passed, 10 failed** in 103.78 seconds. All 10 failures were existing Phase 1/2 tests whose Uvicorn server did not reach `server.started` within 10 seconds (`RuntimeError: MCP test server did not start`).
- Second diagnostic: the isolated `test_real_client_connects_lists_tools_and_rejects_missing_proof` failed with the same startup timeout in 12.21 seconds.
- Action: Stop the v2 task after the same blocking condition repeated. Because a previous MCP pass became a failure, revert this implementation attempt instead of changing unrelated server/test infrastructure.
