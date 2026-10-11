# Dependency and static-analysis evidence

Date: 2026-10-11. These are local tool results, not a certification or an external audit.

## Tools

- `pip-audit 2.10.1`
- `bandit 1.9.4` on Python 3.12.6
- Agent Scan: **postponed by owner decision; not run and not claimed as passed**.

## pip-audit after selecting cryptography 50.0.0

### Owner rerun

The owner reran `scripts/verify_local.ps1` outside the sandbox with `cryptography 50.0.0`. Both manifest audits completed with the exact result:

```text
No known vulnerabilities found
No known vulnerabilities found
```

The first line covers `requirements-lock.txt`; the second covers `integrations/alexa_mcp/requirements.txt`. This closes the six dependency findings for these two resolved inputs as of 2026-10-11. It is not an external audit or certification, and Agent Scan remains postponed.

### Earlier sandbox attempts

The sandbox could not complete a post-upgrade requirements audit. The initial resolver attempts ended without a result. The explicit attempts then failed while pip-audit created its temporary virtual environment:

```text
PermissionError: [WinError 5] Access is denied: '<sandbox-temp>/Include'
pip_audit._virtual_env.VirtualEnvError: Couldn't execute in a temporary directory under <sandbox-temp>.
```

A retry with `TMP`, `TEMP`, and `TMPDIR` pointed inside the project emitted only these warnings before ending without a vulnerability result or exit summary:

```text
WARNING:pip_audit._cli:--no-deps is supported, but users are encouraged to fully hash their pinned dependencies
WARNING:pip_audit._cli:Consider using a tool like `pip-compile`: https://pip-tools.readthedocs.io/en/latest/#using-hashes
```

These failures describe the earlier sandbox attempts only; the owner rerun above supplied the missing result.

## Bandit

Command:

```text
bandit -r callgate scripts -f json
```

Actual summary:

```text
Files skipped: 0
Lines of code: 2738
High: 0
Medium: 1
Low: 25
Confidence high: 26
nosec suppressions: 0
```

The medium is B314 at `scripts/check_local.py:38`; it parses a JUnit XML file produced locally by the immediately preceding pytest process. It is outside core security code and was accepted with a bounded rationale rather than suppressed. Every finding is individually recorded in `BANDIT_TRIAGE.md`.

## Previous findings being remediated

The owner-run pre-upgrade audit reported 11 rows representing six unique advisory IDs for `cryptography 46.0.5`. `DEPENDENCY_FINDINGS.md` maps those IDs to their fixed versions and the repository's feature usage. The two clean owner reruns above are the evidence for closing those findings on the selected manifests.
