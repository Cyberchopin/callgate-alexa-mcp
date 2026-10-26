"""End-to-end check against the real PayPal sandbox, using the same service code the app uses.

    export PAYPAL_CLIENT_ID=... PAYPAL_CLIENT_SECRET=...
    python -m scripts.paypal_sandbox_check

It reads the hat-sale chat, confirms the terms, creates a real sandbox order,
prints the PayPal approval link, and waits while you approve it with a sandbox
*personal* account. Then it re-checks the order, captures it (twice, to show
the second attempt doesn't charge again), adds tracking, and writes every
PayPal id to docs/paypal/sandbox-run.json so the write-up can quote real ids.

It also proves the tamper check on the real API: before you approve, it
creates a second order for $180 and shows that it is blocked.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from integrations.paypal_checkout import ledger as L
from integrations.paypal_checkout.paypal_client import SANDBOX, PayPalClient, capture_of
from integrations.paypal_checkout.risk import ship_to
from integrations.paypal_checkout.service import CheckoutError, CheckoutService, verify_receipt

CHAT = """Buyer: hi is the Haunted Mansion cap still available?
Seller: yes! new with tags, comes with the original box
Buyer: how much?
Seller: $95 plus $8 shipping
Buyer: can you do $80?
Seller: 80 is ok, shipping is $8
Buyer: deal
Seller: sending the paypal link now"""
PNG = b"\x89PNG\r\n\x1a\n" + b"sandbox-check" + b"\x00" * 16
OUT = Path("docs/paypal/sandbox-run.json")


def step(msg):
    print(f"\n== {msg}", flush=True)


def main() -> int:
    if not (os.environ.get("PAYPAL_CLIENT_ID") and os.environ.get("PAYPAL_CLIENT_SECRET")):
        print("Set PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET from a developer.paypal.com sandbox app.")
        return 2
    if os.environ.get("PAYPAL_BASE_URL", SANDBOX) != SANDBOX:
        print("This check only runs against the sandbox.")
        return 2
    paypal = PayPalClient.from_env()
    state = Path(tempfile.mkdtemp(prefix="callgate-sandbox-"))
    svc = CheckoutService(L.Ledger(state / "ledger.sqlite3"), paypal, Ed25519PrivateKey.generate(),
                          return_url="https://example.com/return", seller_country=os.environ.get("SELLER_COUNTRY", "US"))
    run = {"ran_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "base_url": paypal.base_url, "steps": []}

    def record(name, **data):
        run["steps"].append({"step": name, **data})
        print("   ", json.dumps(data, ensure_ascii=False))

    step("Read the chat and confirm the terms")
    co = svc.start(CHAT, title="Haunted Mansion cap")
    co = svc.confirm_terms(co["id"])
    t = co["data"]["terms"]
    record("terms", total=t["total"]["value"], currency=t["currency"]["value"], shipping=t["shipping"]["value"],
           quotes=[e["quote"] for e in t["total"]["evidence"]])

    step("A $180 order made outside CallGate is checked against the chat")
    bad = paypal.create_order({"intent": "CAPTURE", "purchase_units": [{
        "reference_id": "default", "amount": {"currency_code": "USD", "value": "180.00"}}]},
        request_id=f"cg-sandbox-bad-{co['id']}")
    co = svc.attach_order(co["id"], bad["id"], source="sandbox-check")
    blocked = [d["field"] for d in co["data"]["differences"] if d["severity"] == "block"]
    record("tampered_order", order_id=bad["id"], state=co["state"], blocked=blocked)
    if co["state"] != L.MISMATCH:
        print("!! expected the $180 order to be blocked")
        return 1

    step("Build the order from the confirmed terms")
    co = svc.build_order(co["id"])
    record("order", order_id=co["data"]["order_id"], state=co["state"], fingerprint=co["data"]["order_fingerprint"][:16],
           approve_url=co["data"]["approve_url"])
    if co["state"] != L.READY:
        print("!! order did not match the terms:", co["data"]["differences"])
        return 1
    co = svc.buyer_confirm(co["id"], seen_fingerprint=co["data"]["order_fingerprint"])

    step("Approve in the PayPal sandbox")
    print(f"   Open this link and log in with a sandbox PERSONAL account:\n   {co['data']['approve_url']}")
    print("   (You'll land on example.com afterwards; that's expected. Come back here.)", flush=True)
    deadline = time.time() + 15 * 60
    while time.time() < deadline:
        order = paypal.get_order(co["data"]["order_id"])
        if order.get("status") == "APPROVED":
            break
        time.sleep(5)
    else:
        print("!! not approved within 15 minutes")
        return 1
    # Saved file is public: keep only the country, never the test buyer's city or ZIP.
    record("approved", status=order["status"], ship_to_country=(ship_to(order) or {}).get("country_code"))

    step("Capture — twice, to show the second attempt doesn't charge again")
    try:
        first = svc.capture(co["id"], idempotency_key=f"sandbox-{co['id']}-1")
    except CheckoutError as e:
        if e.code == "ADDRESS_HOLD":
            print("   Held: the sandbox buyer's address is outside the agreed destination. Releasing for the check.")
            svc.accept_destination(co["id"], reason="sandbox check: test buyer address")
            first = svc.capture(co["id"], idempotency_key=f"sandbox-{co['id']}-1b")
        else:
            raise
    second = svc.capture(co["id"], idempotency_key=f"sandbox-{co['id']}-2")
    order = paypal.get_order(co["data"]["order_id"])
    captures = [c for pu in order.get("purchase_units", []) for c in (pu.get("payments") or {}).get("captures", [])]
    record("capture", state=first["state"], capture_id=first["capture_id"], second_attempt=second.get("note"),
           captures_on_paypal=len(captures), payment_flags=[f["code"] for f in svc.ledger.get(co["id"])["data"].get("payment_flags", [])])
    if len(captures) != 1:
        print("!! expected exactly one capture")
        return 1

    step("Pack, check the label against PayPal's address, add tracking")
    co = svc.ledger.get(co["id"])
    for line in [x["id"] for x in co["data"]["checklist"]]:
        svc.add_photo(co["id"], line, PNG + line.encode())
    dest = co["data"].get("ship_to") or {}
    co = svc.ship(co["id"], carrier="USPS", tracking_number="9400111899223817", label_country=dest.get("country_code", "US"),
                  label_postal=dest.get("postal_code", ""), weight="1.2", weight_unit="lb", acknowledge_warnings=True)
    order = paypal.get_order(co["data"]["order_id"])
    trackers = ((order["purchase_units"][0].get("shipping") or {}).get("trackers") or [])
    record("shipped", state=co["state"], tracking=co["data"]["shipment"]["tracking_number"],
           trackers_on_paypal=[{"id": x.get("id"), "status": x.get("status")} for x in trackers])

    step("Signed receipt")
    receipt = svc.receipt(co["id"])
    payload = verify_receipt(receipt)
    record("receipt", verifies=True, capture_id=payload["capture_id"], agreed_total=payload["agreed"]["total"],
           packing_photos=len(payload["packing_photos"]))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(run, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nAll steps passed against {paypal.base_url}. Saved {OUT}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
