# Merchant injection handoff

- Branch: `amazon/merchant-injection`.
- Status: PARTIAL; implementation exists but its first end-to-end test stalled twice in this environment.
- Run `powershell -ExecutionPolicy Bypass -File scripts/run_merchant_gate.ps1` locally.
- Do not use comparison counts in submission materials until that script exits successfully.
- No LLM mode was added; the requested default-off behavior is satisfied by having no LLM dependency.

