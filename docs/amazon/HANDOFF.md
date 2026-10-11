# Merchant injection handoff

## Security scan handoff

- > **RELEASE BLOCKER:** the owner-machine audit reported 11 vulnerability entries for `cryptography==46.0.5` in the MCP requirements. Test an upgrade that covers every reported fixed version, then rerun the audit before submission.
- Status: PARTIAL on `amazon/scan-evidence`.
- Review `docs/amazon/SECURITY_SCAN.md` before publishing any security statement.
- Run `powershell -ExecutionPolicy Bypass -File scripts/run_security_scans.ps1` outside the restricted environment. Add `-AllowRemoteAnalysis` only after accepting that simulated MCP tool names and descriptions may be sent to the scanner's analysis service and after starting both local demo servers.
- Agent Scan remote analysis remains unrun by explicit privacy choice. The dependency audit completed with the MCP finding above; the root lock-file command reported no known vulnerabilities. Bandit found one accepted medium-severity XML-parsing issue and 20 low-severity items.

- Branch: `amazon/merchant-injection`.
- Status: PARTIAL; implementation exists but its first end-to-end test stalled twice in this environment.
- Run `powershell -ExecutionPolicy Bypass -File scripts/run_merchant_gate.ps1` locally.
- Do not use comparison counts in submission materials until that script exits successfully.
- No LLM mode was added; the requested default-off behavior is satisfied by having no LLM dependency.

## ApprovalBench

- Status: DONE on `amazon/approvalbench` for the deterministic author simulation.
- Reproduce with `python -m evaluation_checkout.approvalbench.run`.
- D0 is explicitly documented as the inferred unguarded baseline; D1–D4 are labeled as our reference implementations and invite corrections.
- D5 had no successful attack in this run, so no D5 failure was added to the red-team report.

