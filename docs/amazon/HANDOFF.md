# Amazon unattended batch handoff

> 🔴 **禁止公开或迁移历史：T2 在完整 Git 历史中发现 3 个 `generic-api-key` 命中。不要 push、公开或迁移历史，直到人工确认并完成合规处置。**

## Task status

| Task | Status | Result/reason |
|---|---|---|
| T0 | DONE | Baseline recorded: Python 245 passed, 3 failed, 1 skipped; Node 3 passed. |
| T1 | BLOCKED | Required temporary clone failed twice with Git/MSYS `0xC0000022`; no `.gitattributes` change. |
| T2 | DONE | gitleaks 8.30.1 scanned 43 commits and found 3 redacted `generic-api-key` findings in one path/commit. |
| T3 | SKIPPED | Required by T2 findings; no migration helper was created. |
| T4 | PARTIAL | Approval gate prohibited applying core code. Review-only design proposal committed; no core test claim. |
| T5 | DONE | Streamable HTTP MCP server, three simulated tools, permanent canary block, SQLite restart replay test, real client tool-list/denial test. |
| T6 | PARTIAL | Native `-32042`, local HTTPS page, completion notification, exact one-time retry, mutation/expiry/self/contact checks pass. Still uses v1 proof and a simulated local contact credential pending commitment-v2 approval. |
| T7 | DONE | Friction logger, submission checker, and separate boundary reports; follow-up commit now uses Git author date and tests rebase-safe classification. |
| T8 | DONE | English submission README draft with all required sections and explicit limitations. |
| T9 | DONE | This handoff, branch inventory, comparisons, decisions, commands, and risks. |

## Branches and latest commits

| Branch | Latest commit |
|---|---|
| `main` | `f18eda53965a349a46c37cc243a7a86e90151f91` |
| `proposal/commitment-v2` | `1fbb196035f327568902475b3e4c95499d4597d2` |
| `amazon/mcp-phase1` | `4b48feb4aa8544844cf13b58cccaa5dd2f7cd4be` |
| `amazon/mcp-phase2` | `bff4e3679026585c93bd306f92f046a7f1aeb7ff` |
| `amazon/tools` | `720681ca776a5933227542045e5882924b5aaee4` |
| `feat/amazon-alexa-mcp-phase1` | T9 self-reference; resolve with `git rev-parse HEAD` |

No branch was pushed, deleted, rebased, reset, or merged. `main` was not modified.

## Test comparison to T0

| Branch/task | Passed | Failed | Skipped | Comparison |
|---|---:|---:|---:|---|
| T0 baseline Python | 245 | 3 | 1 | Baseline |
| T5 full Python | 246 | 3 | 3 | Same 3 failures; isolated environment had 2 more optional skips; 3 MCP targeted tests passed separately. |
| T6 full Python | 252 | 3 | 3 | Same 3 failures; 9 combined MCP tests passed separately. |
| T7 follow-up full Python | 248 | 3 | 1 | Same 3 failures; 3 author-date/tool tests passed. |
| T6 private-key cleanup full Python | 253 | 3 | 3 | Same failures/skips; 10 combined MCP tests passed. |
| Node at T0/T5/T6/T7 | 3 | 0 | 0 | Unchanged. |

The recurring failures are the two Windows spawned-process pipe failures and
`evaluation_v2` manifest mismatch for `blind/scenarios.jsonl`. No new failure
replaced a baseline pass, so no task commit required a revert.

The baseline skip is `test_pipecat_actual_pipeline_and_transcript_boundary` because
the optional `pipecat` package is absent. T5/T6 used an isolated environment that
also lacked optional `onnxruntime`, so `test_silero_real_model_silence_and_isolation`
and `test_sensor_failure_preserves_audio` were the two additional skips. No MCP test
was skipped.

## Decisions required

1. Inspect and resolve the three T2 findings before any public release or history migration. Finding metadata: rule `generic-api-key`, path `scambench/local-check.json`, commit `3b4525ff0ce85beab9bd541f377b442f44e7d27c`.
2. Re-run T1 outside this sandbox. If the clean `core.autocrlf=false` clone still fails its manifest, inspect the differing paths and `git log -- <path>` before deciding whether frozen data or its manifest is wrong.
3. Review `proposal/commitment-v2` commit `1fbb196`. It now requires signed v2 fields, Unicode/number/duplicate-key normalization tests, and MCP rejection of valid v1 credentials. Explicit approval is still required before an apply-ready core implementation or tests may be created.
4. Decide whether phase 2 may be merged while its stable subject binding remains server-side around a v1 signed proof, or whether merge must wait for commitment v2.
5. Decide the final branch-combination order. No merge was performed automatically.
6. Classify the three historical `generic-api-key` findings as SHA-256 false positives or revoke/rotate them. Until then, the publication gate stays closed.

## Commands to run after return

```powershell
# 1. Reproduce T1 outside the sandbox.
git clone -c core.autocrlf=false <local-repository-path> <temporary-path>
Set-Location <temporary-path>
py -3.12 -m evaluation_v2.verify_inputs

# 2. Re-run a redacted full-history scan before any migration.
gitleaks git --no-banner --redact=100 --report-format json --report-path <outside-repo-report.json>

# 3. Review each isolated branch locally.
git show proposal/commitment-v2
git show amazon/mcp-phase1
git show amazon/mcp-phase2
git show amazon/tools

# 4. Re-run targeted tests on their branches.
git switch amazon/mcp-phase1
py -3.12 -m pytest tests/alexa_mcp/test_phase1.py -q
git switch amazon/mcp-phase2
py -3.12 -m pytest tests/alexa_mcp -q
git switch amazon/tools
py -3.12 -m pytest tests/alexa_mcp/test_tools.py -q
```

Do not run migration or push commands while the red warning at the top remains unresolved.

## Known risks

- Historical possible secrets block public migration.
- A 2026-10-10 redacted all-branch rescan still reports exactly 3 findings at the same rule/path/commit and no new finding.
- The frozen v2 manifest could not be independently validated in the required clean clone.
- Commitment v2 is a design proposal only; its `.patch` intentionally contains marked implementation points and is not apply-ready.
- The MCP adapter must reject v1 to prevent downgrade; Phase 2 must not be described or recorded as cryptographically binding tool name or stable subject until v2 is approved and implemented.
- Phase 2's contact credential, page, certificate, identities, money, and approvals are local simulations, not production identity or payment controls.
- The phase-2 proof is v1; stable `subject` is held in the adapter state rather than signed into the credential.
- The self-signed certificate is suitable only for local development.
- Phase 2 now writes its generated certificate/private key only below Git-ignored `.test-tmp/` and removes the temporary directory on normal exit; no key/certificate extension is tracked on any Amazon work branch.
- The Python SDK client required manual conversion from generic `MCPError` code `-32042` to its specialized URL-elicitation error type.
