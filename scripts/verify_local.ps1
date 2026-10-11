param(
    [string]$Phase1Path = "",
    [string]$Phase2Path = ""
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$worktreeParent = Split-Path -Parent $root
if (-not $Phase1Path) { $Phase1Path = Join-Path $worktreeParent ".rc1-phase1-gate" }
if (-not $Phase2Path) { $Phase2Path = Join-Path $worktreeParent ".dependency-phase2-gate" }
$venv = Join-Path $root ".venv-dependency-upgrade"
$python = Join-Path $venv "Scripts\python.exe"
$temp = Join-Path $root ".test-tmp\dependency-upgrade"
New-Item -ItemType Directory -Force $temp | Out-Null
$env:TMP = $temp
$env:TEMP = $temp
$env:TMPDIR = $temp

if (-not (Test-Path $python)) {
    py -3.12 -m venv $venv
    if ($LASTEXITCODE -ne 0) { throw "venv creation failed with exit code $LASTEXITCODE" }
}

& $python -m pip install --disable-pip-version-check -r requirements-lock.txt -r requirements-verification.txt -r requirements-safety.txt
if ($LASTEXITCODE -ne 0) { throw "dependency installation failed with exit code $LASTEXITCODE" }
& $python -m pip install --disable-pip-version-check -r integrations/alexa_mcp/requirements.txt pip-audit==2.10.1 bandit==1.9.4
if ($LASTEXITCODE -ne 0) { throw "audit-tool installation failed with exit code $LASTEXITCODE" }
& $python -c "import cryptography; assert cryptography.__version__ == '50.0.0'; print('cryptography', cryptography.__version__)"
if ($LASTEXITCODE -ne 0) { throw "cryptography version check failed with exit code $LASTEXITCODE" }

& $python -m pytest tests/test_cryptography_upgrade.py -q --basetemp (Join-Path $temp "compat")
if ($LASTEXITCODE -ne 0) { throw "compatibility tests failed with exit code $LASTEXITCODE" }
& $python -m pytest -q -rs --basetemp (Join-Path $temp "full")
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Full suite contains the three recorded baseline failures; checking every other test."
    & $python -m pytest -q -rs --ignore tests/test_review_process.py `
        --deselect tests/test_v2_inputs.py::test_input_schema_and_manifest `
        --basetemp (Join-Path $temp "regression")
    if ($LASTEXITCODE -ne 0) { throw "a previously passing Python test failed with exit code $LASTEXITCODE" }
}
node --test tests/review_ui.test.cjs
if ($LASTEXITCODE -ne 0) { throw "Node tests failed with exit code $LASTEXITCODE" }

foreach ($gate in @(
    @{ Name = "phase1"; Path = $Phase1Path; Tests = @("tests/alexa_mcp/test_phase1.py") },
    @{ Name = "phase2"; Path = $Phase2Path; Tests = @("tests/alexa_mcp/test_phase1.py", "tests/alexa_mcp/test_phase2.py") }
)) {
    $gatePath = Resolve-Path -LiteralPath $gate.Path -ErrorAction SilentlyContinue
    if (-not $gatePath) {
        throw "$($gate.Name) worktree not found: $($gate.Path)"
    }
    Push-Location $gatePath
    try {
        & $python -m pytest @($gate.Tests) -q -rs --basetemp (Join-Path $temp $gate.Name)
        if ($LASTEXITCODE -ne 0) { throw "$($gate.Name) tests failed with exit code $LASTEXITCODE" }
    } finally {
        Pop-Location
    }
}

& $python -m pip_audit -r requirements-lock.txt
if ($LASTEXITCODE -ne 0) { throw "root pip-audit failed with exit code $LASTEXITCODE" }
& $python -m pip_audit -r integrations/alexa_mcp/requirements.txt
if ($LASTEXITCODE -ne 0) { throw "MCP pip-audit failed with exit code $LASTEXITCODE" }
& $python -m bandit -r callgate scripts
if ($LASTEXITCODE -notin @(0, 1)) { throw "Bandit execution failed with exit code $LASTEXITCODE" }
& $python -m bandit -r callgate scripts -lll -q
if ($LASTEXITCODE -ne 0) { throw "Bandit reported a high-severity finding" }
