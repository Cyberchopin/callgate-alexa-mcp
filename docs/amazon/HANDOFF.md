# Amazon UI handoff

## Approved hardening gate

- D2/D3/D4 changes are present but not yet regression-cleared in this environment.
- Run `powershell -ExecutionPolicy Bypass -File scripts/run_ui_hardening_gate.ps1` from the repository root.
- Do not merge this branch into `release/amazon-rc1` until both targeted and full commands pass without turning a previous pass into a failure.

- Branch: `amazon/ui`.
- Status: PARTIAL because implementation/tests passed but screenshots could not be captured.
- Open `/demo` on the local phase-2 server for the fixed offline simulated voice-assistant fixture.
- Use `python -m scripts.run_ui_preview` only for local screenshots; it clearly serves HTTP and is not security evidence. The protected approval demonstration must use the HTTPS phase-2 command.
- Owner action: capture the three screenshots listed in `UI_ACCESSIBILITY.md` outside this environment and visually verify contrast with an accessibility tool.
- No bilingual toggle was added; it was optional and did not displace security or accessibility work.

