# Bandit triage

Bandit version: `1.9.4`. Command: `bandit -r callgate scripts -f json`.

The owner-provided run contained 1 medium and 20 low findings. The current RC1 tree also contains five low findings in the subsequently merged tooling scripts, so this review records all **26** current findings: 1 medium and 25 low. No `nosec` suppression was added and no core security code was changed.

| # | Finding | Location | Decision | Reason |
|---:|---|---|---|---|
| 1 | B404 low | `scripts/check_local.py:8` | Accept | Local verification script imports `subprocess`; it invokes fixed argument lists with `shell=False`. |
| 2 | B405 low | `scripts/check_local.py:10` | Accept | The only XML input is a JUnit file generated immediately beforehand by the local pytest process in a fresh temporary directory. |
| 3 | B603 low | `scripts/check_local.py:33` | Accept | Runs the current Python interpreter with fixed pytest arguments and `shell=False`; no command text is interpreted by a shell. |
| 4 | B314 medium | `scripts/check_local.py:38` | Accept | The parser reads only the locally generated JUnit file described above. This is not core security code and no externally supplied XML is accepted. If the script ever accepts an external report, replace this parser with a hardened XML parser. |
| 5 | B603 low | `scripts/check_local.py:43` | Accept | Runs a fixed local module through the current Python interpreter with `shell=False`. |
| 6 | B404 low | `scripts/fork_upstreams.py:6` | Accept | The user-invoked repository helper needs subprocess execution; all calls use argument arrays and `shell=False`. |
| 7 | B607 low | `scripts/fork_upstreams.py:13` | Accept | The helper intentionally resolves the locally authenticated `gh` CLI from the trusted developer `PATH`. |
| 8 | B603 low | `scripts/fork_upstreams.py:13` | Accept | Fixed `gh api user` argument array; no shell interpolation. |
| 9 | B607 low | `scripts/fork_upstreams.py:19` | Accept | Same trusted local `gh` executable boundary; the repository value remains a separate argument. |
| 10 | B603 low | `scripts/fork_upstreams.py:19` | Accept | Uses an argument array with `shell=False`; a manifest value cannot inject shell syntax. |
| 11 | B607 low | `scripts/fork_upstreams.py:20` | Accept | Same trusted local `gh` executable boundary. |
| 12 | B603 low | `scripts/fork_upstreams.py:20` | Accept | Uses an argument array with `shell=False`; destination is passed as one API-path argument. |
| 13 | B101 low | `scripts/offline_demo.py:22` | Accept | Demo-only invariant, not an authorization boundary. The documented demo is not run with Python optimization. |
| 14 | B101 low | `scripts/offline_demo.py:49` | Accept | Demo-only replay assertion; production replay enforcement remains in `SQLiteReplayStore`. |
| 15 | B101 low | `scripts/proof_demo.py:38` | Accept | Scripted demonstration assertion, not policy enforcement. |
| 16 | B101 low | `scripts/proof_demo.py:39` | Accept | Scripted demonstration assertion, not the HTTP authorization check itself. |
| 17 | B101 low | `scripts/proof_demo.py:40` | Accept | Scripted demonstration assertion, not workflow state storage. |
| 18 | B101 low | `scripts/proof_demo.py:51` | Accept | Demo output check; the protected operation remains simulated. |
| 19 | B101 low | `scripts/proof_demo.py:52` | Accept | Demo output check that confirms no real action; the repository does not provide a real payment path. |
| 20 | B101 low | `scripts/workflow_demo.py:23` | Accept | Demo-only state assertion, not policy enforcement. |
| 21 | B101 low | `scripts/workflow_demo.py:24` | Accept | Demo-only result assertion; the operation is simulated. |
| 22 | B404 low | `scripts/gen_preexisting.py:5` | Accept | Read-only Git-history generator; subprocess is required and invoked without a shell. |
| 23 | B607 low | `scripts/gen_preexisting.py:14` | Accept | The developer's trusted local `git` executable is intentionally resolved from `PATH`. |
| 24 | B603 low | `scripts/gen_preexisting.py:14` | Accept | Git arguments are passed as an array with `shell=False`; user cutoff values are not executed. |
| 25 | B404 low | `scripts/submission_check.py:6` | Accept | Local submission checker imports `subprocess` to run fixed verification commands. |
| 26 | B603 low | `scripts/submission_check.py:14` | Accept | Commands are argument arrays selected by repository code and use `shell=False`. |

## Residual risk

The medium XML finding is acceptable only while the JUnit input is generated locally in the same run. The B607 findings assume the owner's local `PATH` is trusted. The B101 demo checks disappear under `python -O`; they are not security controls, but optimized mode should not be used when recording the demonstrations.
