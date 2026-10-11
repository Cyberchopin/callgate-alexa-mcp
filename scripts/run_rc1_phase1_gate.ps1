$ErrorActionPreference = "Stop"

$gatePath = Join-Path (Split-Path (Get-Location) -Parent) ".rc1-phase1-gate"
if (Test-Path -LiteralPath $gatePath) {
    throw "Gate worktree already exists: $gatePath"
}

git worktree add --detach $gatePath amazon/mcp-phase1
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Push-Location $gatePath
try {
    $venv = Join-Path $gatePath ".venv-rc1-gate"
    $python = Join-Path $venv "Scripts\python.exe"
    py -3.12 -m venv $venv
    & $python -m pip install -r integrations/alexa_mcp/requirements.txt
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $python -m pytest tests/alexa_mcp/test_phase1.py -q --basetemp=.test-tmp/phase1
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $python -m pytest -q --basetemp=.test-tmp/full -rs
    exit $LASTEXITCODE
} finally {
    Pop-Location
    Write-Host "Gate worktree retained for inspection: $gatePath"
}
