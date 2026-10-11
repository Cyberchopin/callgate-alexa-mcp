$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$venv = Join-Path $root ".venv-ui-hardening"
$python = Join-Path $venv "Scripts\python.exe"

if (-not (Test-Path $python)) {
    py -3.12 -m venv $venv
}

& $python -m pip install -r (Join-Path $root "integrations\alexa_mcp\requirements.txt")
& $python -m pytest -q -p no:cacheprovider --basetemp (Join-Path $root ".test-tmp\ui-hardening") (Join-Path $root "tests\alexa_mcp\test_ui.py")
& $python -m pytest -q -p no:cacheprovider --basetemp (Join-Path $root ".test-tmp\ui-hardening-full")

