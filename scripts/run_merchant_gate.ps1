$ErrorActionPreference = "Stop"

py -3.12 -m pytest tests/alexa_mcp/test_merchant_injection.py -vv --basetemp=.test-tmp/merchant-gate
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

py -3.12 -m scripts.run_merchant_injection_demo --database .test-tmp/merchant-demo.sqlite3
exit $LASTEXITCODE
