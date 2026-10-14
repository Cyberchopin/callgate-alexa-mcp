$ErrorActionPreference = "Stop"

$gatePath = Join-Path (Split-Path (Get-Location) -Parent) ".rc1-phase1-gate"
if (-not (Test-Path -LiteralPath $gatePath)) {
    git worktree add --detach $gatePath amazon/mcp-phase1
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Push-Location $gatePath
try {
    $temporary = Join-Path $gatePath ".test-tmp\venv"
    New-Item -ItemType Directory -Force $temporary | Out-Null
    $env:TEMP = $temporary
    $env:TMP = $temporary
    $venv = Join-Path $gatePath ".venv-rc1-gate-2"
    $python = Join-Path $venv "Scripts\python.exe"
    py -3.12 -m venv $venv
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $python -m pip install -r integrations/alexa_mcp/requirements.txt
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $python -m pip install pytest==9.1.1
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $python -m pytest tests/alexa_mcp/test_phase1.py -q --basetemp=.test-tmp/phase1
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    & $python -m pytest -q --basetemp=.test-tmp/full -rs
    exit $LASTEXITCODE
} finally {
    Pop-Location
    Write-Host "Gate worktree retained for inspection: $gatePath"
}
