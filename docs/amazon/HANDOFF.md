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
| T7 | DONE | Friction logger, Git boundary generator, submission checker, two separate generated boundary reports. |
| T8 | DONE | English submission README draft with all required sections and explicit limitations. |
| T9 | DONE | This handoff, branch inventory, comparisons, decisions, commands, and risks. |

## Branches and latest commits

| Branch | Latest commit |
|---|---|
| `main` | `f18eda53965a349a46c37cc243a7a86e90151f91` |
| `proposal/commitment-v2` | `42cda8d8107f84d05817e47f2bf68adcf29916ab` |
| `amazon/mcp-phase1` | `4b48feb4aa8544844cf13b58cccaa5dd2f7cd4be` |
| `amazon/mcp-phase2` | `c9dd7c32d782299b596b4e7261463af79efb8036` |
| `amazon/tools` | `c4d80ca80f70a154834c7bcace80a389692d646a` |
| `feat/amazon-alexa-mcp-phase1` | T9 self-reference; resolve with `git rev-parse HEAD` |

No branch was pushed, deleted, rebased, reset, or merged. `main` was not modified.

## Test comparison to T0

| Branch/task | Passed | Failed | Skipped | Comparison |
|---|---:|---:|---:|---|
| T0 baseline Python | 245 | 3 | 1 | Baseline |
| T5 full Python | 246 | 3 | 3 | Same 3 failures; isolated environment had 2 more optional skips; 3 MCP targeted tests passed separately. |
| T6 full Python | 252 | 3 | 3 | Same 3 failures; 9 combined MCP tests passed separately. |
| T7 full Python | 247 | 3 | 1 | Same 3 failures; 2 new tool tests passed. |
| Node at T0/T5/T6/T7 | 3 | 0 | 0 | Unchanged. |

The recurring failures are the two Windows spawned-process pipe failures and
`evaluation_v2` manifest mismatch for `blind/scenarios.jsonl`. No new failure
replaced a baseline pass, so no task commit required a revert.

## Decisions required

1. Inspect and resolve the three T2 findings before any public release or history migration. Finding metadata: rule `generic-api-key`, path `scambench/local-check.json`, commit `3b4525ff0ce85beab9bd541f377b442f44e7d27c`.
2. Re-run T1 outside this sandbox. If the clean `core.autocrlf=false` clone still fails its manifest, inspect the differing paths and `git log -- <path>` before deciding whether frozen data or its manifest is wrong.
3. Review `proposal/commitment-v2` commit `42cda8d`. Explicit approval is still required before an apply-ready core implementation or tests may be created.
4. Decide whether phase 2 may be merged while its stable subject binding remains server-side around a v1 signed proof, or whether merge must wait for commitment v2.
5. Decide the final branch-combination order. No merge was performed automatically.

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
- The frozen v2 manifest could not be independently validated in the required clean clone.
- Commitment v2 is a design proposal only; its `.patch` intentionally contains marked implementation points and is not apply-ready.
- Phase 2's contact credential, page, certificate, identities, money, and approvals are local simulations, not production identity or payment controls.
- The phase-2 proof is v1; stable `subject` is held in the adapter state rather than signed into the credential.
- The self-signed certificate is suitable only for local development.
- The Python SDK client required manual conversion from generic `MCPError` code `-32042` to its specialized URL-elicitation error type.
