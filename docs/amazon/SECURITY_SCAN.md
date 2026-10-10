# Security scan evidence

Date: 2026-10-10. Scope: the simulated CallGate MCP server, simulated merchant MCP server, Python dependency manifests, and Python source under `callgate/`, `integrations/alexa_mcp/`, and `scripts/`.

This is tool output from a local development run, not a certification or independent audit. No secret values, environment files, approval credentials, or real user data were inspected or submitted.

## Tool versions

- `snyk-agent-scan==0.6.8`
- `pip-audit==2.10.1`
- `bandit==1.9.4` on Python 3.12.6

The versions were fixed before execution. The packages were installed into an ignored project-local tool directory.

## Agent Scan privacy decision and result

The current Agent Scan documentation says analysis may send component information needed for analysis, including MCP tool names and descriptions, to Snyk's analysis service. It also says detected config/text secrets are redacted and tool call contents/results are not stored or logged. The scanner can execute configured stdio servers or contact remote servers after consent. There is an inspection mode, but no fully local security-analysis mode was identified.

Only the non-sensitive, simulated server metadata was in scope. No credential, pending approval, contact record, environment file, or real transaction was supplied. Source consulted: [Snyk Agent Scan](https://github.com/snyk/agent-scan).

The scan did **not** run. Both attempts stopped before server inspection with the same import error:

```text
ModuleNotFoundError: No module named 'pywintypes'
```

This is an environment/tool-startup failure, not a security result. No claim is made about either MCP server. `scripts/run_security_scans.ps1` reproduces the fixed-version setup outside this environment; its remote-analysis step requires an explicit switch and assumes the two local demo servers are already running.

## Dependency audit

Commands attempted:

```text
pip-audit -r integrations/alexa_mcp/requirements.txt --no-deps --disable-pip --timeout 15 --progress-spinner off
pip-audit -r requirements-lock.txt --no-deps --disable-pip --timeout 15 --progress-spinner off
```

The first form initially failed while creating a virtual environment:

```text
VirtualEnvError: Couldn't execute in a temporary directory
PermissionError: [WinError 5] Access is denied
```

After moving temporary files into the ignored project directory and disabling dependency resolution, two runs produced no vulnerability response and were interrupted after the allowed retry. Therefore the number of dependency vulnerabilities is **unknown**. This is not a clean audit result. The local reproduction script retains the exact fixed versions and manifest scope.

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

