import copy

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from integrations.paypal_checkout import ledger as L
from integrations.paypal_checkout import provenance as PV
from integrations.paypal_checkout.fake_paypal import FakePayPal
from integrations.paypal_checkout.paypal_client import PayPalClient
from integrations.paypal_checkout.service import CheckoutError, CheckoutService, verify_receipt

from .test_checkout import Clock

RECEIPT_JP = b"\xff\xd8\xff\xe0" + "東京ディズニーランド レシート".encode() + b"\x00" * 16
SERIAL = b"\x89PNG\r\n\x1a\n" + b"serial-tag" + b"\x00" * 16


def seller(tmp_path, name):
    fake = FakePayPal()
    return CheckoutService(L.Ledger(tmp_path / f"{name}.sqlite3"), PayPalClient("i", "s", transport=fake.transport()),
                           Ed25519PrivateKey.generate(), clock=Clock(), photo_dir=tmp_path / name), fake


def test_passport_travels_across_three_sellers_and_survives_verification(tmp_path):
    shop, _ = seller(tmp_path, "proxy")          # e.g. a Japan proxy buyer
    a = shop.start("Buyer: cap for $40?\nSeller: ok")
    shop.add_provenance(a["id"], event="acquired", holder="Tokyo proxy (Buyee order 48812)",
                        where="Tokyo Disneyland, World Bazaar", when="2026-09-14",
                        serials=["JAN 4580542911234"], photos=[("receipt", RECEIPT_JP), ("serial", SERIAL)])
    exported = shop.passport(a["id"])["chain"]

    bro, fake = seller(tmp_path, "brother")      # the reseller in the US
    b = bro.start("Buyer: is the cap $80?\nSeller: yes $80 shipped\nBuyer: deal")
    bro.import_passport(b["id"], exported)
    bro.add_provenance(b["id"], event="inspected", holder="Shiyue's brother", where="Los Angeles",
                       when="2026-10-02", note="Tags attached, no wear on sweatband")
    v = bro.passport(b["id"])["verification"]
    assert v["ok"] and v["holders"] == 2 and [e["event"] for e in v["entries"]] == ["acquired", "inspected"]

    # the payer sees it, pays, and the sale is appended and signed
    co = bro.confirm_terms(b["id"])
    co = bro.build_order(co["id"])
    co = bro.buyer_confirm(co["id"], seen_fingerprint=co["data"]["order_fingerprint"])
    fake.approve(co["data"]["order_id"])
    bro.capture(co["id"], idempotency_key="prov-pay-01")
    final = bro.passport(co["id"])
    assert final["verification"]["ok"] and final["verification"]["entries"][-1]["event"] == "sold"
    assert verify_receipt(bro.receipt(co["id"]))["provenance_head"] == PV.entry_hash(final["chain"][-1])

    # the buyer can later resell with the whole history
    nxt, _ = seller(tmp_path, "next")
    c = nxt.start("Buyer: $70?\nSeller: ok")
    nxt.import_passport(c["id"], final["chain"])
    assert nxt.passport(c["id"])["verification"]["holders"] == 2     # proxy + brother keys
    assert nxt.check_photo(c["id"], RECEIPT_JP)["matches_entries"] == [1]
    assert nxt.check_photo(c["id"], b"\xff\xd8\xff\xe0 a different receipt")["matches_entries"] == []


def chain_of_three(tmp_path):
    svc, _ = seller(tmp_path, "s")
    co = svc.start("Seller: $10\nBuyer: deal")
    for ev, who in [("acquired", "Shop"), ("inspected", "Reseller"), ("listed", "Reseller")]:
        svc.add_provenance(co["id"], event=ev, holder=who, when="2026-10-01")
    return svc.passport(co["id"])["chain"]


def test_editing_any_entry_breaks_its_signature(tmp_path):
    chain = chain_of_three(tmp_path)
    bad = copy.deepcopy(chain)
    bad[0]["entry"]["where"] = "Official store (forged)"
    v = PV.verify_chain(bad)
    assert not v["ok"] and v["entries"][0]["status"] == "bad signature"


def test_removing_or_reordering_entries_breaks_the_links(tmp_path):
    chain = chain_of_three(tmp_path)
    assert not PV.verify_chain([chain[0], chain[2]])["ok"]
    assert not PV.verify_chain([chain[1], chain[0], chain[2]])["ok"]
    assert PV.verify_chain(chain)["ok"]


def test_resigned_forgery_still_breaks_the_next_link(tmp_path):
    chain = chain_of_three(tmp_path)
    forger = Ed25519PrivateKey.generate()
    forged = PV.make_entry([], forger, event="acquired", holder="Official store", recorded_at=1)
    forged["entry"]["item_id"] = chain[0]["entry"]["item_id"]
    forged["signature"] = forger.sign(PV.canonical(forged["entry"])).hex()
    v = PV.verify_chain([forged] + chain[1:])
    assert not v["ok"] and any("does not link" in p for p in v["problems"])


def test_import_refuses_an_altered_passport(tmp_path):
    chain = chain_of_three(tmp_path)
    chain[1]["entry"]["note"] = "never opened"
    svc, _ = seller(tmp_path, "other")
    co = svc.start("Seller: $10\nBuyer: deal")
    with pytest.raises(CheckoutError) as e:
        svc.import_passport(co["id"], chain)
    assert e.value.code == "PASSPORT_BROKEN"


def test_bad_inputs_are_refused(tmp_path):
    svc, _ = seller(tmp_path, "x")
    co = svc.start("Seller: $10\nBuyer: deal")
    for kwargs in [dict(event="teleported", holder="me"), dict(event="acquired", holder=" "),
                   dict(event="acquired", holder="me", when="14/09/2026")]:
        with pytest.raises(CheckoutError):
            svc.add_provenance(co["id"], **kwargs)
    with pytest.raises(CheckoutError):
        svc.add_provenance(co["id"], event="acquired", holder="me", photos=[("receipt", b"not an image")])
