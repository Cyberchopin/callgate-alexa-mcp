import json

from integrations.paypal_checkout.fake_paypal import FakePayPal
from integrations.paypal_checkout.paypal_client import PayPalClient
from scripts import paypal_sandbox_check as check


def test_sandbox_check_script_runs_end_to_end(monkeypatch, tmp_path):
    """Same script you run against the real sandbox, here against the stand-in, so a script bug shows up first."""
    fake = FakePayPal()
    monkeypatch.setenv("PAYPAL_CLIENT_ID", "x")
    monkeypatch.setenv("PAYPAL_CLIENT_SECRET", "y")
    monkeypatch.setattr(PayPalClient, "from_env", classmethod(lambda cls, transport=None: cls("x", "y", transport=fake.transport())))

    def approve_latest(_seconds):          # stands in for the person clicking "Pay" on PayPal
        oid = list(fake.orders)[-1]
        if fake.orders[oid]["status"] != "APPROVED":
            fake.approve(oid)
    monkeypatch.setattr(check.time, "sleep", approve_latest)
    monkeypatch.setattr(check, "OUT", tmp_path / "sandbox-run.json")

    assert check.main() == 0
    run = json.loads((tmp_path / "sandbox-run.json").read_text())
    steps = {s["step"]: s for s in run["steps"]}
    assert "total" in steps["tampered_order"]["blocked"]
    assert steps["capture"]["captures_on_paypal"] == 1 and "no second charge" in steps["capture"]["second_attempt"]
    assert steps["shipped"]["trackers_on_paypal"] and steps["receipt"]["verifies"]
