# Amazon phase-2 build log

## BUILD-SCAN-001 — Security evidence — 2026-10-10

- Agent Scan 0.6.8 failed twice before inspection: `ModuleNotFoundError: No module named 'pywintypes'`. No MCP scan result is claimed.
- pip-audit 2.10.1 first failed with `VirtualEnvError: Couldn't execute in a temporary directory` and `PermissionError: [WinError 5] Access is denied`. After relocating temporary files, two allowed query attempts returned no result before interruption. Dependency vulnerability status is unknown.
- Bandit 1.9.4 completed: 3,005 lines scanned; 20 low, 1 medium, 0 high; 21 findings had high confidence; 0 files skipped.
- No source finding was fixed on the evidence-only branch.

## ApprovalBench build record — 2026-10-10

- First run failed because the Windows sandbox temporary directory could not open or remove the SQLite file (`sqlite3.OperationalError: unable to open database file`; `PermissionError: [WinError 5] Access is denied`).
- The rerun used the repository's ignored `.test-tmp/approvalbench` directory and completed.
- Actual output: fixed seed `20261010`, `50` trials per matrix cell; D5 reported `0/50` attack success for A1 through A6.
- OTP relay scan raw successes: `0/50`, `10/50`, `30/50`, `38/50`, `50/50` at the five requested probabilities.
- Targeted result: `3 passed in 1.43s`.
- Claims result: `registered=32 unresolved_or_inconsistent=0`.
- A full-suite total is not claimed because the branch includes the merchant end-to-end test that had already stalled twice; the two-failure stop rule applies.

## Merchant injection build record — 2026-10-10

- Added an independent simulated merchant MCP server, deterministic vulnerable test double, offline comparison command, and dual-service launcher.
- The targeted command was attempted twice. Both runs stalled on `test_simulated_merchant_search_cart_checkout_approval_and_replay`; the second run collected three tests and produced no result for the first test within 30 seconds.
- No pass count or injection comparison count is claimed. No core security code was changed.

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
