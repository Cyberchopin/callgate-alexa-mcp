param(
    [string]$Phase1Path = ".rc1-phase1-gate",
    [string]$Phase2Path = ".dependency-phase2-gate"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$venv = Join-Path $root ".venv-dependency-upgrade"
$python = Join-Path $venv "Scripts\python.exe"
$temp = Join-Path $root ".test-tmp\dependency-upgrade"
New-Item -ItemType Directory -Force $temp | Out-Null
$env:TMP = $temp
$env:TEMP = $temp
$env:TMPDIR = $temp

if (-not (Test-Path $python)) {
    py -3.12 -m venv $venv
}

& $python -m pip install --disable-pip-version-check -r requirements-lock.txt -r requirements-verification.txt
& $python -m pip install --disable-pip-version-check -r integrations/alexa_mcp/requirements.txt pip-audit==2.10.1 bandit==1.9.4
& $python -c "import cryptography; assert cryptography.__version__ == '50.0.0'; print('cryptography', cryptography.__version__)"

& $python -m pytest tests/test_cryptography_upgrade.py -q --basetemp (Join-Path $temp "compat")
& $python -m pytest -q -rs --basetemp (Join-Path $temp "full")
node --test tests/review_ui.test.cjs

foreach ($gate in @(
    @{ Name = "phase1"; Path = $Phase1Path; Tests = @("tests/alexa_mcp/test_phase1.py") },
    @{ Name = "phase2"; Path = $Phase2Path; Tests = @("tests/alexa_mcp/test_phase1.py", "tests/alexa_mcp/test_phase2.py") }
)) {
    $gatePath = Resolve-Path -LiteralPath $gate.Path -ErrorAction SilentlyContinue
    if (-not $gatePath) {
        Write-Warning "$($gate.Name) worktree not found: $($gate.Path)"
        continue
    }
    Push-Location $gatePath
    try {
        & $python -m pytest @($gate.Tests) -q -rs --basetemp (Join-Path $temp $gate.Name)
    } finally {
        Pop-Location
    }
}

& $python -m pip_audit -r requirements-lock.txt
& $python -m pip_audit -r integrations/alexa_mcp/requirements.txt
& $python -m bandit -r callgate scripts
