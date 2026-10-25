from fastapi.testclient import TestClient

from integrations.paypal_checkout.fake_paypal import FakePayPal
from integrations.paypal_checkout.server.app import create_app
from integrations.paypal_checkout.service import verify_receipt

from .test_checkout import HAT_CHAT


def make(tmp_path):
    fake = FakePayPal()
    return TestClient(create_app(state_dir=tmp_path, fake=fake, model_reader=None)), fake


def test_demo_story_end_to_end(tmp_path):
    c, fake = make(tmp_path)
    assert c.get("/").status_code == 200 and c.get("/api/config").json()["mode"] == "fake"
    co = c.post("/api/checkouts", json={"chat": HAT_CHAT}).json()
    assert co["terms"]["total"]["value"] == "88.00"
    co = c.post(f"/api/checkouts/{co['id']}/confirm").json()
    assert co["state"] == "TERMS_CONFIRMED"

    # 1. the AI sales agent drafts the wrong order
    co = c.post("/demo/agent-draft", json={"checkout_id": co["id"], "value": "180"}).json()
    assert co["state"] == "MISMATCH" and co["order_source"] == "ai-sales-agent"

    # 2. rebuild from the agreed terms, payer confirms the exact version
    co = c.post(f"/api/checkouts/{co['id']}/build-order").json()
    assert co["state"] == "READY" and c.get(f"/pay/{co['id']}").status_code == 200
    co = c.post(f"/api/checkouts/{co['id']}/buyer-confirm", json={"seen_fingerprint": co["order_fingerprint"]}).json()
    assert co["state"] == "BUYER_CONFIRMED"

    # 3. someone edits the order to $180 after confirmation: refused, nothing charged
    c.post("/demo/approve", json={"checkout_id": co["id"]})
    c.post("/demo/edit-order", json={"checkout_id": co["id"], "value": "180"})
    r = c.post(f"/api/checkouts/{co['id']}/capture", headers={"Idempotency-Key": "k-edited-01"})
    assert r.status_code == 409 and r.json()["error"] == "ORDER_CHANGED_AFTER_APPROVAL"
    assert c.get(f"/demo/paypal-count/{co['id']}").json()["captures_at_paypal"] == 0

    # 4. rebuild, confirm, then two simultaneous payment requests with one key
    co = c.post(f"/api/checkouts/{co['id']}/build-order").json()
    co = c.post(f"/api/checkouts/{co['id']}/buyer-confirm", json={"seen_fingerprint": co["order_fingerprint"]}).json()
    c.post("/demo/approve", json={"checkout_id": co["id"]})
    a = c.post(f"/api/checkouts/{co['id']}/capture", headers={"Idempotency-Key": "k-pay-0001"}).json()
    b = c.post(f"/api/checkouts/{co['id']}/capture", headers={"Idempotency-Key": "k-pay-0001"}).json()
    assert a["state"] == "CAPTURED" and b["replayed"] is True
    assert c.get(f"/demo/paypal-count/{co['id']}").json()["captures_at_paypal"] == 1

    # 5. webhook delivered twice is applied once; receipt verifies
    w = c.post("/demo/webhook", json={"checkout_id": co["id"], "redeliver": True}).json()
    assert w["redelivered"]["status"] == "duplicate"
    rec = c.get(f"/api/checkouts/{co['id']}/receipt").json()
    assert verify_receipt(rec)["agreed"]["total"] == "88.00"


def test_manual_resolution_needs_real_quote(tmp_path):
    c, _ = make(tmp_path)
    co = c.post("/api/checkouts", json={"chat": "Buyer: 80 for the cap?\nSeller: fine"}).json()
    assert co["terms"]["total"] is None
    bad = c.post(f"/api/checkouts/{co['id']}/confirm", json={"resolutions": {
        "total": {"value": "80", "message_index": 0, "quote": "$80 total"},
        "currency": {"value": "USD", "message_index": 0, "quote": "$80 total"},
        "acceptance": {"value": "Seller", "message_index": 1, "quote": "fine"}}})
    assert bad.status_code == 400 and bad.json()["error"] == "UNGROUNDED"
    good = c.post(f"/api/checkouts/{co['id']}/confirm", json={"resolutions": {
        "total": {"value": "80", "message_index": 0, "quote": "80 for the cap"},
        "currency": {"value": "USD", "message_index": 0, "quote": "80 for the cap"},
        "acceptance": {"value": "Seller", "message_index": 1, "quote": "fine"}}})
    assert good.status_code == 200 and good.json()["state"] == "TERMS_CONFIRMED"


def test_webhook_endpoint_rejects_unsigned(tmp_path):
    c, _ = make(tmp_path)
    r = c.post("/webhooks/paypal", content=b'{"id":"WH-1","event_type":"PAYMENT.CAPTURE.COMPLETED","resource":{}}')
    assert r.status_code == 401


def test_capture_requires_idempotency_key(tmp_path):
    c, _ = make(tmp_path)
    co = c.post("/api/checkouts", json={"chat": HAT_CHAT}).json()
    assert c.post(f"/api/checkouts/{co['id']}/capture").status_code == 422


def test_demo_controls_are_off_in_sandbox_mode(tmp_path, monkeypatch):
    from integrations.paypal_checkout.paypal_client import PayPalClient
    fake = FakePayPal()
    monkeypatch.setenv("PAYPAL_CLIENT_ID", "x")
    monkeypatch.setenv("PAYPAL_CLIENT_SECRET", "y")
    monkeypatch.delenv("CALLGATE_DEMO", raising=False)
    real_from_env = PayPalClient.from_env
    monkeypatch.setattr(PayPalClient, "from_env", classmethod(lambda cls, transport=None: real_from_env.__func__(cls, fake.transport())))
    c = TestClient(create_app(state_dir=tmp_path, model_reader=None))
    assert c.get("/api/config").json() == {**c.get("/api/config").json(), "mode": "sandbox", "demo": False}
    assert c.post("/demo/edit-order", json={"checkout_id": "x"}).status_code == 404
