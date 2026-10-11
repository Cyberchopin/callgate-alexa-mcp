$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $root ".venv-v2-retry"
$python = Join-Path $venv "Scripts\python.exe"

if (-not (Test-Path $python)) {
    py -3.12 -m venv $venv
}

& $python -m pip install -r (Join-Path $root "integrations\alexa_mcp\requirements.txt")
& $python -m pytest -q -p no:cacheprovider --basetemp (Join-Path $root ".test-tmp\v2-retry-core") (Join-Path $root "tests\alexa_mcp\test_commitment_v2.py")
& $python -m pytest -q -p no:cacheprovider --basetemp (Join-Path $root ".test-tmp\v2-retry-mcp") (Join-Path $root "tests\alexa_mcp\test_phase1.py") (Join-Path $root "tests\alexa_mcp\test_phase2.py")
& $python -m pytest -q -p no:cacheprovider --basetemp (Join-Path $root ".test-tmp\v2-retry-full")

