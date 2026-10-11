# Commitment v2 retry handoff

> **NOT READY TO MERGE:** the approved implementation is present, but this environment could not start its test gate because two Python environments were missing required packages.

- Branch: `amazon/commitment-v2-retry`.
- Approval: D6 YES; proposal `1fbb196` remains the design basis.
- Run `powershell -ExecutionPolicy Bypass -File scripts/run_v2_retry_gate.ps1` from the repository root.
- Do not merge into `release/amazon-rc1` unless all three commands in that script complete and previously passing tests remain passing.
