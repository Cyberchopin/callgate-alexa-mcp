param(
    [switch]$AllowRemoteAnalysis
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $root ".scan-venv"
$python = Join-Path $venv "Scripts\python.exe"

if (-not (Test-Path $python)) {
    py -3.12 -m venv $venv
}

& $python -m pip install "snyk-agent-scan==0.6.8" "pip-audit==2.10.1" "bandit==1.9.4"
& $python -m pip_audit -r (Join-Path $root "integrations\alexa_mcp\requirements.txt") --no-deps --disable-pip --timeout 15 --progress-spinner off
& $python -m pip_audit -r (Join-Path $root "requirements-lock.txt") --no-deps --disable-pip --timeout 15 --progress-spinner off
& $python -m bandit -r (Join-Path $root "callgate") (Join-Path $root "integrations\alexa_mcp") (Join-Path $root "scripts") -q

if ($AllowRemoteAnalysis) {
    Write-Host "Remote analysis explicitly enabled; demo servers must already be running."
    & $python -m agent_scan.cli scan --dangerously-run-mcp-servers --no-skills "streamable-http:127.0.0.1:8000/mcp" "streamable-http:127.0.0.1:8010/mcp"
} else {
    Write-Host "Agent Scan remote analysis skipped. Re-run with -AllowRemoteAnalysis after reviewing docs/amazon/SECURITY_SCAN.md."
}

