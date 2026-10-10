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
# UI build record — 2026-10-10

- Added a no-build simulated assistant page, independent contact page, collapsible proof panel, fixed offline fixture/reset behavior, and server-derived transaction fields.
- Targeted UI plus phase-2 result: **10 passed in 12.85s**.
- Full Python result: **256 passed, 3 failed, 3 skipped in 14.42s**. The three failures are the known Windows spawned-process failures and frozen `evaluation_v2` manifest mismatch; no frozen file was changed.
- Skip reasons: missing optional `onnxruntime` (two) and `pipecat` (one); none involves MCP, HTTPS, or elicitation.
- Node result: **3 passed, 0 failed, 0 skipped**.
- Screenshot attempt: the Codex in-app browser could not reach the loopback preview and returned `net::ERR_CONNECTION_TIMED_OUT`. No screenshot was generated or claimed. Session control cleanup was denied by the current permission policy, and Windows CIM process inspection then failed because the CIM resource was unavailable.

