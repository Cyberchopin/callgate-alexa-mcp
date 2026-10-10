# Amazon workstream build log

This log contains only commands and results observed during the Amazon workstream. It does not replace the repository's historical root `BUILD_LOG.md`.

## BUILD-001 — T0 baseline — 2026-10-10 (America/Los_Angeles)

- Git base: `f18eda5` on local branch `feat/amazon-alexa-mcp-phase1`; worktree was clean.
- Python: `3.12.6` via `py -3.12`.
- Node.js: `v24.18.0`; npm: `11.16.0`.
- `python.exe` alias check failed before tests:

```text
Program 'python.exe' failed to run: An error occurred trying to start process 'C:\Users\wangs\AppData\Local\Microsoft\WindowsApps\python.exe' ... The file cannot be accessed by the system.
```

- `hypothesis` was initially absent. The first install attempt failed because network access was unavailable:

```text
ERROR: Could not find a version that satisfies the requirement hypothesis (from versions: none)
ERROR: No matching distribution found for hypothesis
```

- After network permission was granted, `hypothesis==6.168.5` and `sortedcontainers==2.4.0` were installed into the project-specific external directory `work/.verification-deps`; global Python was not modified.
- Python command: `py -3.12 -m pytest --basetemp <workspace>/work/.pytest-baseline -q`, with `work/.verification-deps` on `PYTHONPATH`.
- Python result: **245 passed, 3 failed, 1 skipped** in 14.54 seconds.
- Existing failures:
  - `tests/test_review_process.py::test_two_process_approval_then_unavailable_reviewer` — spawned child ended its pipe in the sandbox.
  - `tests/test_review_process.py::test_three_process_routing_switch_and_cross_contact_isolation` — spawned child ended its pipe in the sandbox.
  - `tests/test_v2_inputs.py::test_input_schema_and_manifest` — `ValueError: manifest mismatch: blind/scenarios.jsonl`.
- Node command: `node --test tests/review_ui.test.cjs`.
- Node result: **3 passed, 0 failed, 0 skipped**.

## BUILD-002 — T1 temporary-clone manifest check — 2026-10-10 (America/Los_Angeles)

- Attempted twice with `git clone -c core.autocrlf=false`, once with `--no-local` and once with the normal local-clone path.
- Both attempts failed before a checkout was created, so the manifest verifier was not run and `.gitattributes` was not added.
- Raw error from both attempts:

```text
sh.exe: *** fatal error - NtCreateDirectoryObject(\BaseNamedObjects\msys-2.0S5-1888ae32e00d56aa): 0xC0000022
fatal: Could not read from remote repository.
```

- Per the two-failure rule, T1 stopped. No frozen evaluation file was read or modified by this task.

## BUILD-003 — T2 full-history secret scan — 2026-10-10 (America/Los_Angeles)

- Tool: official `gitleaks 8.30.1` Windows x64 release; the downloaded archive was checked against the release checksum file before execution.
- Scope: Git history reachable through all refs (`gitleaks git`); **43 commits** scanned.
- Result: **3 findings**.
- Redacted finding metadata only:

| Count | Rule | Path | Commit |
|---:|---|---|---|
| 3 | `generic-api-key` | `scambench/local-check.json` | `3b4525ff0ce85beab9bd541f377b442f44e7d27c` |

- No secret value or matching line was printed or copied into repository files.
- Consequence: T3 migration helper was skipped as required.

## BUILD-004 — T4 commitment-v2 proposal — 2026-10-10 (America/Los_Angeles)

- Branch: `proposal/commitment-v2`, based on `main`.
- Proposal commit: `42cda8d8107f84d05817e47f2bf68adcf29916ab`.
- Applying the executable core diff was rejected by the pre-existing approval gate. No core file or test was modified.
- A review-only design diff and risk note were committed under `docs/amazon/`; the patch explicitly identifies itself as not apply-ready and not tested.
- No tests were claimed for this proposal. The working branch was restored after the commit.

## BUILD-005 — T5 phase 1 MCP server — 2026-10-10 (America/Los_Angeles)

- Branch/commit: `amazon/mcp-phase1` at `4b48feb4aa8544844cf13b58cccaa5dd2f7cd4be`.
- First MCP run: 3 failed because SDK 2.3.0 hid ordinary exception text behind `UnexpectedToolError`. The integration switched expected failures to SDK `ToolError` and reran once.
- Targeted result: **3 passed** in 1.75 seconds.
- Full Python result in the isolated MCP environment: **246 passed, 3 failed, 3 skipped**. The three failures exactly match T0; no previously passing test became a failure. Two additional optional integrations skipped because this isolated environment did not include all global optional packages.
- Node result: **3 passed, 0 failed, 0 skipped**.
- The isolated dependency install reported unrelated package-version conflicts involving `pyppeteer`, OpenTelemetry, and `realtime`; no repository dependency file was changed in response.

## BUILD-006 — T6 URL elicitation — 2026-10-10 (America/Los_Angeles)

- Branch/commit: `amazon/mcp-phase2` at `c9dd7c32d782299b596b4e7261463af79efb8036`.
- Initial phase-2 test result: **6 failed**. The client surfaced server `-32042` as generic `MCPError`, and one nested temporary database directory was absent.
- After one correction, phase-2 targeted result: **6 passed** in 2.82 seconds.
- Combined phase-1/phase-2 MCP result: **9 passed** in 3.77 seconds.
- Full Python result: **252 passed, 3 failed, 3 skipped**. The three failures exactly match T0; no previously passing test became a failure.
- Node result: **3 passed, 0 failed, 0 skipped**.

## BUILD-007 — T7 support tools — 2026-10-10 (America/Los_Angeles)

- Branch/commit: `amazon/tools` at `c4d80ca80f70a154834c7bcace80a389692d646a`.
- Targeted tool tests: **2 passed** in 1.55 seconds.
- Full Python result: **247 passed, 3 failed, 1 skipped**. The three failures exactly match T0; no previously passing test became a failure.
- Node result: **3 passed, 0 failed, 0 skipped**.
- Both Git-derived boundary reports were generated: Amazon cutoff `2026-08-31T10:15:00-07:00` and separate LA Hacks cutoff `2026-10-17`.

## BUILD-008 — T8 README draft — 2026-10-10 (America/Los_Angeles)

- Branch/commit: `feat/amazon-alexa-mcp-phase1` at `96376131450f81d1ed6b309d06b383f747f6d001` before the T9 update.
- Static heading check: **7 of 7 required sections present**.
- No executable code changed; no test result was claimed for prose.

