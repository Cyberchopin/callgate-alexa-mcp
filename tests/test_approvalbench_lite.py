from evaluation_checkout.approvalbench.run import ATTACKS, DESIGNS, TRIALS, build_results


def test_matrix_has_raw_counts_and_wilson_intervals():
    report = build_results()
    assert set(report["matrix"]) == set(DESIGNS)
    assert all(set(report["matrix"][design]) == set(ATTACKS) for design in DESIGNS)
    assert all(item["trials"] == TRIALS and len(item["wilson95"]) == 2
               for row in report["matrix"].values() for item in row.values())


def test_callgate_reference_has_no_scripted_attack_successes():
    report = build_results()
    assert all(item["successes"] == 0 for item in report["matrix"]["D5_callgate"].values())


def test_otp_relay_sensitivity_endpoints_are_exact():
    sweep = build_results()["d2_relay_sensitivity"]
    assert sweep["0"]["successes"] == 0
    assert sweep["1"]["successes"] == TRIALS
