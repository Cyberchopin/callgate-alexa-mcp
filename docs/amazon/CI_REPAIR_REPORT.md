# Local CI repair — 2026-10-13 UTC

Scope: local branch `amazon/ci-repair`, based on `amazon/readme-final`
at `5a0e6296ab0c3f36e1047a2892966b5c830dfabb`, in an isolated local clone.
No push, merge, branch deletion, core-security change, or frozen-data change.

## Diagnosed failures and changes

1. `.github/workflows/test.yml` collected MCP tests without installing their
   requirements. The actual job reported missing `mcp` and `httpx2`, with six
   collection errors. Add the existing pinned MCP requirements to installation.
2. The Ubuntu matrix reported `288 passed, 1 failed, 3 skipped`.
   `test_committed_checkout_results_match_regenerated_report` raised
   `UnicodeDecodeError: 'utf-8' codec can't decode byte 0x97 in position 38: invalid start byte`.
   The report generator and its reader relied on platform-default encodings.
   Set explicit UTF-8 and LF on generated artifacts and explicit UTF-8 in tests.
   Regenerate the non-frozen checkout artifacts: only REPORT.md and
   sensitivity_scan.svg change encoding; results.json and safety_utility.svg
   remain byte-identical. No results, assumptions, or security logic changed.
3. Gitleaks never started in the failed Actions job. Docker reported
   `unsupported media type application/vnd.in-toto+json` (exit 125).
   Replace the unusable image reference with the official Linux x64 release
   archive, version 8.30.1, verified before extraction using SHA-256
   `551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb`.
   This digest was obtained from the official release API during this task:
   <https://api.github.com/repos/gitleaks/gitleaks/releases/tags/v8.30.1>.
   Retain all-history scanning, complete redaction, and the existing exact
   fingerprint ignore file. Do not weaken the scanner or change ignored findings.

Sources: [matrix job](https://github.com/Cyberchopin/callgate-alexa-mcp/actions/runs/38196353326)
and [legacy core job](https://github.com/Cyberchopin/callgate-alexa-mcp/actions/runs/38196353456).
These jobs tested the earlier synthetic PR merge with the old main, not a future
merge against the current main.

## Actual local verification

The existing dependency-upgrade Python environment was reused, not freshly
installed. All commands ran from the isolated clone. Python was invoked with
`-X utf8` to exercise the encoding failure seen on Ubuntu.

| Check | Actual result |
|---|---|
| Checkout evaluation focused tests | 8 passed in 0.97s |
| Cryptography compatibility plus MCP phase1/phase2 | 13 passed in 14.35s |
| Full Python regression | 290 passed, 3 skipped, 1 warning in 34.75s |
| Node tests, before and after | 3 passed, 0 failed |
| Claims checker | registered=39 unresolved_or_inconsistent=0 |
| Local Gitleaks 8.30.1, all reachable refs, existing ignores | 111 commits scanned; no leaks found; exit 0 |
| Diff whitespace check | exit 0 |
| Core security and evaluation_v1/evaluation_v2 diff | empty |

The one-command script was also executed end-to-end with exit 0: 21 focused
tests passed in 14.14s; the full suite repeated with 290 passed, 3 skipped,
1 warning in 33.54s; Node 3/3, claims 39/0, and scan 111 commits/no remaining
findings. The scanner's `Unknown SCM platform` message reflects the local origin
URL and did not prevent scanning.

The previous Linux job had 288 passes and one failure. This local run has one
additional UTF-8 regression test and the formerly failing report test passes.
This is a cross-platform comparison, not a claim that a new Ubuntu CI run passed.
No skips or xfails were added. The three existing skips are
`tests/test_integrations.py` lines 7, 19, and 50, for unavailable `onnxruntime`
and `pipecat`. The warning is the existing AnyIO BlockingPortal deprecation.

The added test `test_checkout_artifact_writer_uses_explicit_utf8_and_lf` checks
all four generated files, asserts explicit encoding/newline arguments, and
compares their contents with the renderer and JSON report.

## Remaining limits

- The Linux archive download/extraction and full workflow have not been executed
  on a Linux runner after these edits. The local scanner was the Windows binary.
- The local clone scan covers its reachable history, not future remote commits.
- GitHub main remains `1d1069169e4fd10b5ac887bdcdc827b77b195b92`;
  PR #20 remains open and conflicted. No conflict resolution was applied.
- The readme-final PR head is unchanged remotely. These local repairs are not
  present on GitHub and no CI rerun was requested.

## Reproduce locally

Use the pinned dependency environment and Gitleaks 8.30.1:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify_ci_repair.ps1 -Python <python-executable> -Gitleaks <gitleaks-executable>
```

The script creates the project-local temporary parent directory before pytest
and fails on any nonzero check. It does not install dependencies or push.
