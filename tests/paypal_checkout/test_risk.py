import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from integrations.paypal_checkout import ledger as L
from integrations.paypal_checkout import risk as RK
from integrations.paypal_checkout.fake_paypal import FakePayPal
from integrations.paypal_checkout.paypal_client import PayPalClient
from integrations.paypal_checkout.service import CheckoutError, CheckoutService, verify_receipt
from integrations.paypal_checkout.terms import parse_chat

from .test_checkout import Clock

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
US_SALE = """Buyer: is the cap available? I'm in Toronto
Seller: yes, $80 plus $8 shipping within the US
Buyer: ok deal"""


@pytest.fixture
def mk(tmp_path):
    def make(seller_country="US"):
        fake = FakePayPal()
        svc = CheckoutService(L.Ledger(tmp_path / f"l-{seller_country}.sqlite3"),
                              PayPalClient("i", "s", transport=fake.transport()), Ed25519PrivateKey.generate(),
                              clock=Clock(), seller_country=seller_country, photo_dir=tmp_path / "p")
        return svc, fake
    return make


def to_payer_approved(svc, fake, chat, ship_to=None):
    co = svc.confirm_terms(svc.start(chat)["id"])
    co = svc.build_order(co["id"])
    co = svc.buyer_confirm(co["id"], seen_fingerprint=co["data"]["order_fingerprint"])
    fake.approve(co["data"]["order_id"], ship_to=ship_to)
    return co


@pytest.mark.parametrize("line,code", [
    ("Buyer: can you ship it to my friend in Texas? it's a gift", "REDIRECT_REQUEST"),
    ("Buyer: please send to a different address than PayPal", "REDIRECT_REQUEST"),
    ("买家: 能不能寄到我朋友那里，地址改一下", "REDIRECT_REQUEST"),
    ("Buyer: I'll send you a label, use my UPS account", "BUYER_SHIPPER"),
    ("买家: 我叫快递来取", "BUYER_SHIPPER"),
    ("Buyer: can I pay friends and family to save the fee?", "OFF_PLATFORM_PAYMENT"),
    ("Buyer: I can zelle you", "OFF_PLATFORM_PAYMENT"),
    ("买家: 微信转账可以吗", "OFF_PLATFORM_PAYMENT"),
    ("Buyer: oops I overpaid, can you send back the difference", "OVERPAYMENT"),
])
def test_known_scam_lines_are_flagged_with_their_quote(line, code):
    flags = RK.chat_flags(parse_chat(line))
    hit = next(f for f in flags if f.code == code)
    assert hit.quote in line and hit.source


@pytest.mark.parametrize("line", [
    "Buyer: can you send us more pics?", "Seller: I'll ship it to you tomorrow", "Buyer: shipping to me is fine",
    "Seller: wireless earbuds included", "Buyer: what's the offer?"])
def test_ordinary_lines_are_not_flagged(line):
    assert RK.chat_flags(parse_chat(line)) == []


def test_us_pronoun_is_not_a_country():
    found, _ = RK.agreed_destinations(parse_chat("Buyer: can you ship and send us the tracking?"), "US")
    assert found == set()


def test_destination_outside_agreement_holds_the_payment(mk):
    svc, fake = mk()
    co = to_payer_approved(svc, fake, US_SALE, ship_to={"country_code": "CA", "postal_code": "M5V 2T6",
                                                       "admin_area_2": "Toronto", "admin_area_1": "ON"})
    with pytest.raises(CheckoutError) as e:
        svc.capture(co["id"], idempotency_key="hold-0001")
    assert e.value.code == "ADDRESS_HOLD"
    co = svc.ledger.get(co["id"])
    assert co["state"] == L.ADDRESS_HOLD and fake.capture_count.get(co["data"]["order_id"], 0) == 0
    flag = next(f for f in co["data"]["payment_flags"] if f["code"] == "DESTINATION_MISMATCH")
    assert "within the US" in flag["quote"]
    assert any(f["code"] == "DUTIES_NOT_DISCUSSED" for f in co["data"]["payment_flags"])
    with pytest.raises(CheckoutError):
        svc.accept_destination(co["id"], reason="")
    svc.accept_destination(co["id"], reason="Buyer agreed to pay the $14 difference separately in chat")
    assert svc.capture(co["id"], idempotency_key="hold-0002")["state"] == L.CAPTURED
    r = verify_receipt(svc.receipt(co["id"]))
    assert r["destination_override"]["country_code"] == "CA" and r["ship_to"]["country_code"] == "CA"
    assert "DESTINATION_MISMATCH" in r["flags"]


def test_order_asks_paypal_for_a_ship_to_and_missing_one_holds_the_payment(mk):
    """Found on the real sandbox: an order that didn't ask for shipping came back approved with no address."""
    svc, fake = mk()
    co = svc.build_order(svc.confirm_terms(svc.start(US_SALE)["id"])["id"])
    body = fake.create_bodies[co["data"]["order_id"]]
    assert body["purchase_units"][0]["items"][0]["category"] == "PHYSICAL_GOODS"
    assert body["payment_source"]["paypal"]["experience_context"]["shipping_preference"] == "GET_FROM_FILE"
    co = svc.buyer_confirm(co["id"], seen_fingerprint=co["data"]["order_fingerprint"])
    fake.approve(co["data"]["order_id"], no_address=True)
    with pytest.raises(CheckoutError) as e:
        svc.capture(co["id"], idempotency_key="noaddr-0001")
    assert e.value.code == "ADDRESS_HOLD" and fake.capture_count.get(co["data"]["order_id"], 0) == 0
    assert [f["code"] for f in svc.ledger.get(co["id"])["data"]["payment_flags"]] == ["NO_SHIP_TO"]
    svc.accept_destination(co["id"], reason="Local pickup, agreed in chat")
    assert svc.capture(co["id"], idempotency_key="noaddr-0002")["state"] == L.CAPTURED


def test_cross_border_into_us_mentions_de_minimis(mk):
    svc, fake = mk(seller_country="JP")
    co = to_payer_approved(svc, fake, "Buyer: how much shipped to the USA?\nSeller: $50 shipped to the USA\nBuyer: deal")
    svc.capture(co["id"], idempotency_key="dm-000001")
    flags = svc.ledger.get(co["id"])["data"]["payment_flags"]
    duty = next(f for f in flags if f["code"] == "DUTIES_NOT_DISCUSSED")
    assert "August 29, 2025" in duty["why"] and "JP → US" in duty["title"]


def test_duties_discussed_is_recorded_not_warned(mk):
    svc, fake = mk(seller_country="JP")
    co = to_payer_approved(svc, fake, "Seller: $50 shipped to the USA, buyer pays customs duties\nBuyer: deal")
    svc.capture(co["id"], idempotency_key="dm-000002")
    codes = {f["code"] for f in svc.ledger.get(co["id"])["data"]["payment_flags"]}
    assert "DUTIES_DISCUSSED" in codes and "DUTIES_NOT_DISCUSSED" not in codes


def paid_and_photographed(svc, fake, chat):
    co = to_payer_approved(svc, fake, chat)
    svc.capture(co["id"], idempotency_key="pay-" + co["id"][-8:])
    for line in [x["id"] for x in svc.ledger.get(co["id"])["data"]["checklist"]]:
        svc.add_photo(co["id"], line, PNG + line.encode())
    return svc.ledger.get(co["id"])


def test_label_must_go_to_paypal_address(mk):
    svc, fake = mk()
    co = paid_and_photographed(svc, fake, "Seller: $80 shipped\nBuyer: deal")
    with pytest.raises(CheckoutError) as e:
        svc.ship(co["id"], carrier="USPS", tracking_number="9400111899223", label_country="US",
                 label_postal="10001", weight="1", weight_unit="lb")
    assert e.value.code == "LABEL_BLOCKED" and e.value.extra["flags"][0]["code"] == "LABEL_ADDRESS_MISMATCH"
    assert not fake.trackers
    co = svc.ship(co["id"], carrier="USPS", tracking_number="9400111899223", label_country="us",
                  label_postal="92617-4410", weight="1", weight_unit="lb")
    assert co["state"] == L.SHIPPED


def test_weight_is_required_and_sane(mk):
    svc, fake = mk()
    co = paid_and_photographed(svc, fake, "Seller: $80 shipped\nBuyer: deal")
    for w, u in [("", "lb"), ("0", "lb"), ("2", "stone"), ("500", "lb")]:
        with pytest.raises(CheckoutError) as e:
            svc.ship(co["id"], carrier="USPS", tracking_number="9400111899223", label_country="US",
                     label_postal="92617", weight=w, weight_unit=u)
        assert e.value.code == "BAD_SHIPMENT"


def test_valuable_item_over_ups_default_liability_needs_acknowledgment(mk):
    svc, fake = mk()
    co = paid_and_photographed(svc, fake, "Seller: $350 shipped for the camera\nBuyer: deal")
    args = dict(carrier="UPS", tracking_number="1Z999AA10123456784", label_country="US", label_postal="92617",
                weight="3", weight_unit="lb")
    with pytest.raises(CheckoutError) as e:
        svc.ship(co["id"], **args)
    assert e.value.code == "SHIP_WARNINGS" and e.value.extra["flags"][0]["code"] == "OVER_CARRIER_LIABILITY"
    svc.ship(co["id"], **args, declared_value="350")      # declaring the value clears the warning
    assert svc.ledger.get(co["id"])["state"] == L.SHIPPED


def test_payer_acknowledgment_goes_into_receipt_and_evidence(mk):
    svc, fake = mk()
    co = paid_and_photographed(svc, fake, "Seller: $80 shipped\nBuyer: deal")
    svc.ship(co["id"], carrier="USPS", tracking_number="9400111899223", label_country="US", label_postal="92617",
             weight="22", weight_unit="oz")
    with pytest.raises(CheckoutError):
        svc.acknowledge(co["id"], as_described=False, note="")
    svc.acknowledge(co["id"], as_described=True)
    r = verify_receipt(svc.receipt(co["id"]))
    assert r["buyer_acknowledgment"]["as_described"] is True
    notes = svc.evidence_pack(co["id"])["input"]["evidences"][0]["notes"]
    assert "22 oz" in notes and "matches the PayPal ship-to" in notes and "arrived as described" in notes
