# Security scan evidence

Initial run: 2026-10-10. Owner-machine rerun: 2026-10-11. Scope: the simulated CallGate MCP server, simulated merchant MCP server, Python dependency manifests, and Python source under `callgate/`, `integrations/alexa_mcp/`, and `scripts/`.

This is tool output from a local development run, not a certification or independent audit. No secret values, environment files, approval credentials, or real user data were inspected or submitted.

## Tool versions

- `snyk-agent-scan==0.6.8`
- `pip-audit==2.10.1`
- `bandit==1.9.4` on Python 3.12.6

The versions were fixed before execution. The packages were installed into an ignored project-local tool directory.

## Agent Scan privacy decision and result

The current Agent Scan documentation says analysis may send component information needed for analysis, including MCP tool names and descriptions, to Snyk's analysis service. It also says detected config/text secrets are redacted and tool call contents/results are not stored or logged. The scanner can execute configured stdio servers or contact remote servers after consent. There is an inspection mode, but no fully local security-analysis mode was identified.

Only the non-sensitive, simulated server metadata was in scope. No credential, pending approval, contact record, environment file, or real transaction was supplied. Source consulted: [Snyk Agent Scan](https://github.com/snyk/agent-scan).

The initial restricted-environment scan did **not** run. Both attempts stopped before server inspection with the same import error:

```text
ModuleNotFoundError: No module named 'pywintypes'
```

On the 2026-10-11 owner-machine rerun, Agent Scan started, but remote analysis was intentionally skipped because `-AllowRemoteAnalysis` was not supplied. This is the expected privacy-preserving default. No Agent Scan finding or passing result is claimed for either MCP server.

## Dependency audit

Commands attempted:

```text
pip-audit -r integrations/alexa_mcp/requirements.txt --no-deps --disable-pip --timeout 15 --progress-spinner off
pip-audit -r requirements-lock.txt --no-deps --disable-pip --timeout 15 --progress-spinner off
```

The initial restricted-environment run failed while creating a virtual environment:

```text
VirtualEnvError: Couldn't execute in a temporary directory
PermissionError: [WinError 5] Access is denied
```

The 2026-10-11 owner-machine rerun completed both commands:

- `integrations/alexa_mcp/requirements.txt`: **11 vulnerability entries in one package**, `cryptography==46.0.5`. The output contains six unique advisory IDs: `PYSEC-2026-35`, `PYSEC-2026-36`, `PYSEC-2026-3552`, `PYSEC-2026-3553`, `PYSEC-2026-3554`, and `GHSA-537c-gmf6-5ccf`.
- `requirements-lock.txt`: **no known vulnerabilities found** by this command.

The reported fixed versions range from 46.0.6 through 50.0.0; satisfying every listed entry requires evaluating an upgrade to at least 50.0.0. No dependency was changed on this evidence-only branch. The MCP dependency set must not be described as clean until the upgrade is tested and the audit is rerun.

## Static analysis

Command:

```text
bandit -r callgate integrations/alexa_mcp scripts -q
```

Actual summary:

```text
Total lines of code: 3005
Low: 20
Medium: 1
High: 0
Confidence high: 21
Files skipped: 0
```

Findings and disposition:

| Rule | Count | Area | Disposition |
| --- | ---: | --- | --- |
| B314 | 1 | `scripts/check_local.py` parses the JUnit XML produced by the immediately preceding local pytest process. | Accept for this evidence branch because the input is locally generated, not externally supplied. Replace with `defusedxml` before accepting arbitrary XML. |
| B404 | 2 | Maintenance scripts import `subprocess`. | Accept as expected process-launch behavior; each concrete call remains separately reviewed. |
| B405 | 1 | `scripts/check_local.py` imports `xml.etree.ElementTree`. | Same bounded-input rationale as B314. |
| B603 | 5 | Maintenance scripts launch Python or `gh` using argument arrays with `shell=False`. | Accept for now: no shell interpolation is used. The GitHub repository value still needs to remain constrained to the checked manifest. |
| B607 | 3 | `scripts/fork_upstreams.py` resolves `gh` through `PATH`. | Accept for a developer-only helper; operators must use a trusted `PATH`. Pinning an executable path would reduce this local risk. |
| B101 | 9 | Offline/demo scripts use `assert` as self-checks. | Accept only for demos. Running Python with optimization can remove these checks, so they are not authorization controls and should become explicit exceptions if used as release gates. |

No code was changed in response to findings because this branch is evidence-only. The medium finding and accepted local-tool risks remain open for owner review.

