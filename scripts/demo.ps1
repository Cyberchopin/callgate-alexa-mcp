param([switch]$Offline)

$ErrorActionPreference = "Stop"
$repo = Split-Path -Parent $PSScriptRoot
Push-Location $repo
try {
    if ($Offline) {
        py -3.12 -m scripts.run_merchant_injection_demo `
            --database .test-tmp/merchant-demo.sqlite3 `
            --output docs/amazon/merchant_injection_results.json
    } else {
        py -3.12 -m scripts.run_amazon_services --replay-db .test-tmp/demo-replay.sqlite3
    }
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
