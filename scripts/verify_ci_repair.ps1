param(
    [string]$Python = '.\.venv-dependency-upgrade\Scripts\python.exe',
    [string]$Gitleaks = 'gitleaks'
)
$ErrorActionPreference = 'Stop'
Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    New-Item -ItemType Directory -Force .test-tmp | Out-Null
    & $Python -X utf8 -m pytest tests/test_checkout_evaluation.py tests/test_cryptography_upgrade.py tests/alexa_mcp/test_phase1.py tests/alexa_mcp/test_phase2.py -q -rs --basetemp .test-tmp/ci-repair-focused
    if ($LASTEXITCODE -ne 0) { throw 'Focused tests failed.' }
    & $Python -X utf8 -m pytest -q -rs --basetemp .test-tmp/ci-repair-full
    if ($LASTEXITCODE -ne 0) { throw 'Full Python suite failed.' }
    & node --test tests/review_ui.test.cjs
    if ($LASTEXITCODE -ne 0) { throw 'Node tests failed.' }
    & $Python -X utf8 scripts/check_claims.py
    if ($LASTEXITCODE -ne 0) { throw 'Claims check failed.' }
    & $Gitleaks version
    if ($LASTEXITCODE -ne 0) { throw 'Gitleaks is unavailable.' }
    & $Gitleaks git --redact=100 --no-banner --log-opts=--all --gitleaks-ignore-path=.gitleaksignore .
    if ($LASTEXITCODE -ne 0) { throw 'History scan failed.' }
} finally {
    Pop-Location
}
