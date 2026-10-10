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

## BUILD-COMMITMENT-V2-001 — 2026-10-10

- Approved proposal: `1fbb196035f327568902475b3e4c95499d4597d2`.
- Attempt commit: `afc5e02`; targeted result was **15 passed, 10 failed**. Every failure was an existing MCP test timing out at `RuntimeError: MCP test server did not start`.
- Isolated second diagnostic: `test_real_client_connects_lists_tools_and_rejects_missing_proof` failed with the same startup timeout.
- Required response: commit `a05f675` reverted the implementation attempt because previously passing MCP tests failed.
- Post-revert targeted result on the original Phase 2 code: **1 passed, 9 failed**, again solely MCP/Uvicorn startup timeouts. This shows the current environment is also blocking the pre-v2 server tests; it does not establish that the v2 code caused the timeout.
- Status: BLOCKED. No v2 implementation remains applied at branch HEAD and no v2 success claim is made.
