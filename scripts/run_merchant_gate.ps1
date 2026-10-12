$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$python = Join-Path $root ".venv-dependency-upgrade\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Run scripts/verify_local.ps1 first to create the pinned environment." }
Set-Location $root

& $python -m pytest tests/alexa_mcp/test_merchant_injection.py -vv --basetemp=.test-tmp/merchant-gate
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $python -m scripts.run_merchant_injection_demo `
    --database .test-tmp/merchant-demo.sqlite3 `
    --output docs/amazon/merchant_injection_results.json
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $python scripts/check_claims.py
exit $LASTEXITCODE
