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

