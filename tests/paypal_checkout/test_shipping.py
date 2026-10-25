import threading

import pytest
from fastapi.testclient import TestClient

from integrations.paypal_checkout import ledger as L
from integrations.paypal_checkout.fake_paypal import FakePayPal
from integrations.paypal_checkout.server.app import create_app
from integrations.paypal_checkout.service import CheckoutError, verify_receipt

from .test_checkout import confirmed_and_approved, env  # noqa: F401  (fixture)

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPG = b"\xff\xd8\xff\xe0" + b"\x01" * 64


def paid(svc, fake):
    co = confirmed_and_approved(svc, fake)
    svc.capture(co["id"], idempotency_key="ship-pay-01")
    return svc.ledger.get(co["id"])


def test_checklist_comes_from_the_chat_promises(env):  # noqa: F811
    svc, fake, _ = env
    co = paid(svc, fake)
    labels = [x["label"] for x in co["data"]["checklist"]]
    assert labels[0].startswith("The item")
    assert "Included: comes with the original box" in labels and "Included: new with tags" in labels
    assert labels[-1] == "Everything in the box, before sealing"
    box = next(x for x in co["data"]["checklist"] if "original box" in x["label"])
    assert box["quote"] == "comes with the original box"


def test_cannot_ship_until_every_line_is_photographed_or_explained(env):  # noqa: F811
    svc, fake, _ = env
    co = paid(svc, fake)
    with pytest.raises(CheckoutError) as e:
        svc.ship(co["id"], carrier="USPS", tracking_number="9400111899223")
    assert e.value.code == "CHECKLIST_INCOMPLETE"
    with pytest.raises(CheckoutError) as e:
        svc.add_photo(co["id"], "item", b"not an image at all")
    assert e.value.code == "BAD_PHOTO"
    lines = [x["id"] for x in co["data"]["checklist"]]
    for i, line in enumerate(lines[:-1]):
        svc.add_photo(co["id"], line, PNG + bytes([i]))
    svc.skip_line(co["id"], lines[-1], "taped the box before I remembered")
    co = svc.ship(co["id"], carrier="usps", tracking_number="9400111899223")
    assert co["state"] == L.SHIPPED
    tracker = fake.trackers[co["data"]["order_id"]][0]
    assert tracker["capture_id"] == co["data"]["capture_id"] and tracker["carrier"] == "USPS"
    assert tracker["notify_payer"] is True
    again = svc.ship(co["id"], carrier="USPS", tracking_number="9400111899223")
    assert again["state"] == L.SHIPPED and len(fake.trackers[co["data"]["order_id"]]) == 1
    receipt = verify_receipt(svc.receipt(co["id"]))
    assert len(receipt["packing_photos"]) == len(lines) - 1
    assert receipt["not_photographed"] == {lines[-1]: "taped the box before I remembered"}
    assert receipt["shipment"]["tracking_number"] == "9400111899223"


def test_unknown_carrier_goes_through_as_other(env):  # noqa: F811
    svc, fake, _ = env
    co = paid(svc, fake)
    for line in [x["id"] for x in co["data"]["checklist"]]:
        svc.add_photo(co["id"], line, JPG + line.encode())
    co = svc.ship(co["id"], carrier="yunexpress", tracking_number="YT2512345678901")
    t = fake.trackers[co["data"]["order_id"]][0]
    assert (t["carrier"], t["carrier_name_other"]) == ("OTHER", "Yunexpress")


def test_concurrent_photo_uploads_are_all_kept(env):  # noqa: F811
    svc, fake, _ = env
    co = paid(svc, fake)
    lines = [x["id"] for x in co["data"]["checklist"]]
    threads = [threading.Thread(target=svc.add_photo, args=(co["id"], line, PNG + line.encode())) for line in lines]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert set(svc.ledger.get(co["id"])["data"]["photos"]) == set(lines)


def test_evidence_pack_and_submission(env):  # noqa: F811
    svc, fake, _ = env
    co = paid(svc, fake)
    for line in [x["id"] for x in co["data"]["checklist"]]:
        svc.add_photo(co["id"], line, PNG + line.encode())
    svc.ship(co["id"], carrier="UPS", tracking_number="1Z999AA10123456784")
    pack = svc.evidence_pack(co["id"])
    ev = pack["input"]["evidences"][0]
    assert ev["evidence_type"] == "PROOF_OF_FULFILLMENT"
    assert ev["evidence_info"]["tracking_info"][0]["tracking_number"] == "1Z999AA10123456784"
    assert "can you do $80?" in ev["notes"] and "80 is ok" in ev["notes"]
    co = svc.submit_evidence(co["id"], "PP-D-27803")
    assert co["data"]["evidence_submitted"]["files"] == 1 + len(co["data"]["checklist"])
    assert fake.evidence["PP-D-27803"][0]["parts"] == 2 + len(co["data"]["checklist"])


def test_photos_are_only_served_for_their_own_checkout(tmp_path):
    fake = FakePayPal()
    c = TestClient(create_app(state_dir=tmp_path, fake=fake, model_reader=None))
    svc = c.app.state.svc
    a = paid(svc, fake)
    b = svc.confirm_terms(svc.start("Seller: $10 for the pin\nBuyer: deal")["id"])
    r = c.post(f"/api/checkouts/{a['id']}/photos", data={"line": "item"},
               files={"photo": ("p.png", PNG, "image/png")})
    sha = r.json()["photos"]["item"]["sha256"]
    assert c.get(f"/api/checkouts/{a['id']}/photos/{sha}").content == PNG
    assert c.get(f"/api/checkouts/{b['id']}/photos/{sha}").status_code == 404
    assert c.get(f"/api/checkouts/{a['id']}/photos/{'0' * 64}").status_code == 404
