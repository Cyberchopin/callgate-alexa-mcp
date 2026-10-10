$ErrorActionPreference = "Stop"

$gatePath = Join-Path (Split-Path (Get-Location) -Parent) ".rc1-phase1-gate"
if (Test-Path -LiteralPath $gatePath) {
    throw "Gate worktree already exists: $gatePath"
}

git worktree add --detach $gatePath amazon/mcp-phase1
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Push-Location $gatePath
try {
    py -3.12 -m pytest tests/alexa_mcp/test_phase1.py -q --basetemp=.test-tmp/phase1
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    py -3.12 -m pytest -q --basetemp=.test-tmp/full -rs
    exit $LASTEXITCODE
} finally {
    Pop-Location
    Write-Host "Gate worktree retained for inspection: $gatePath"
}
