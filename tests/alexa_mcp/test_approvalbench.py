import json
from pathlib import Path

from evaluation_checkout.approvalbench.run import render_relay_svg, render_report, render_svg, run


def test_approvalbench_is_reproducible_and_d5_has_no_hidden_success():
    first = run()
    second = run()
    assert first == second
    assert all(item["numerator"] == 0 for item in first["matrix"]["D5"].values())
    assert all(first["d5_actual_gateway_checks"].values())


def test_approvalbench_reports_raw_counts_intervals_and_utility():
    result = run()
    assert set(result["matrix"]) == {"D0", "D1", "D2", "D3", "D4", "D5"}
    assert set(result["matrix"]["D0"]) == {"A1", "A2", "A3", "A4", "A5", "A6"}
    assert all("wilson95" in cell for row in result["matrix"].values() for cell in row.values())
    assert all("completion" in item and "verification_ms_p95" in item
               for item in result["legitimate_utility"].values())
    assert len(result["otp_relay_scan"]) == 5


def test_committed_approvalbench_artifacts_are_generated():
    result = run()
    root = Path("evaluation_checkout/approvalbench")
    if (root / "results.json").exists():
        assert json.loads((root / "results.json").read_text(encoding="utf-8")) == result
        assert (root / "REPORT.md").read_text(encoding="utf-8") == render_report(result)
        assert (root / "matrix.svg").read_text(encoding="utf-8") == render_svg(result)
        assert (root / "relay_sensitivity.svg").read_text(encoding="utf-8") == render_relay_svg(result)
