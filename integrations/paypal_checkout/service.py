"""CallGate Checkout: the payment can only be what both people agreed to in the chat.

Flow (each step is a ledger transition):
  start            chat -> two readers -> terms with quotes         DRAFT
  confirm_terms    a person resolves conflicts and confirms          TERMS_CONFIRMED
  build_order /    CallGate builds the order from the terms, or an
  attach_order     order made elsewhere (e.g. an AI sales agent)     ORDER_ATTACHED
                   is checked against them                           -> READY | MISMATCH
  buyer_confirm    payer confirms the exact order version they saw   BUYER_CONFIRMED
                   (signed approval bound to the order fingerprint)
  capture          re-read order, re-check fingerprint, then capture CAPTURING -> CAPTURED
                   with a PayPal-Request-Id derived from the approval
  reconcile /      resolve timeouts and asynchronous results          CAPTURE_UNKNOWN -> ...
  handle_webhook

Boundary: this governs checkouts created or checked through CallGate.  It does
not and cannot intercept other PayPal payments a person makes.
"""
from __future__ import annotations

import hashlib
import json
import secrets
import time
from decimal import Decimal

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from callgate.receipt import canonical

from . import ledger as L
from .extract import ModelReader, read_terms
from .order_check import blocking, compare, order_fingerprint, order_from_terms
from .paypal_client import PayPalClient, PayPalError, PayPalTimeout, approve_link, capture_of
from . import risk as RK
from . import shipping as SH
from .terms import (AgreedTerms, Evidence, Field, ground_terms, parse_chat, terms_from_dict)

APPROVAL_VERSION = "callgate-checkout-approval-v1"
RECEIPT_VERSION = "callgate-checkout-receipt-v1"


class CheckoutError(Exception):
    def __init__(self, code: str, message: str, http: int = 409, **extra):
        super().__init__(message)
        self.code, self.http, self.extra = code, http, extra


class CheckoutService:
    def __init__(self, ledger: L.Ledger, paypal: PayPalClient, signing_key: Ed25519PrivateKey, *,
                 model_reader: ModelReader | None = None, clock=time.time, approval_ttl: int = 900,
                 return_url: str = "http://localhost:8787/return", webhook_id: str | None = None,
                 photo_dir=None, seller_country: str = "US"):
        from pathlib import Path
        self.ledger, self.paypal, self.key = ledger, paypal, signing_key
        self.photo_dir = Path(photo_dir) if photo_dir else Path(ledger.path).parent / "photos"
        self.seller_country = seller_country.upper()
        self.model_reader, self.clock, self.ttl = model_reader, clock, approval_ttl
        self.return_url, self.webhook_id = return_url, webhook_id

    @property
    def public_key(self) -> Ed25519PublicKey:
        return self.key.public_key()

    # ------------------------------------------------------------ 1. read
    def start(self, chat, *, default_currency: str = "USD", title: str | None = None) -> dict:
        messages = parse_chat(chat)
        if not messages:
            raise CheckoutError("EMPTY_CHAT", "Paste the part of the chat where the deal was made", 400)
        terms = read_terms(messages, self.model_reader, default_currency)
        checkout_id = "cg_" + secrets.token_hex(10)
        chat_rows = [{"index": m.index, "sender": m.sender, "text": m.text} for m in messages]
        return self.ledger.create(checkout_id, {
            "messages": chat_rows, "chat_sha256": hashlib.sha256(canonical(chat_rows)).hexdigest(),
            "title": (title or "")[:127] or None,
            "readers": ["rules-checkout-v1"] + ([self.model_reader.label] if self.model_reader else []),
            "terms": terms.to_dict(), "ready": terms.ready(),
            "chat_flags": [f.to_dict() for f in RK.chat_flags(messages)]})

    # --------------------------------------------------------- 2. confirm
    def confirm_terms(self, checkout_id: str, *, resolutions: dict | None = None) -> dict:
        """A person confirms the terms.  A resolution must point at a quote in the chat:
        {"total": {"value": "80", "message_index": 5, "quote": "80 is ok"}, ...}"""
        co = self.ledger.get(checkout_id)
        terms = terms_from_dict(co["data"]["terms"])
        for name, r in (resolutions or {}).items():
            if name not in ("currency", "total", "shipping", "acceptance"):
                raise CheckoutError("BAD_RESOLUTION", f"cannot resolve {name}", 400)
            f = Field(str(r["value"]).strip().upper() if name == "currency" else str(r["value"]).strip(),
                      [Evidence(int(r["message_index"]), str(r["quote"]))], "human")
            setattr(terms, name, f)
            terms.unresolved = [u for u in terms.unresolved if not u.startswith(f"CONFLICT {name}")]
        messages = _messages(co)
        problems = ground_terms(terms, messages)
        if problems:
            raise CheckoutError("UNGROUNDED", "Every confirmed term must quote the chat", 400, problems=problems)
        conflicts = [u for u in terms.unresolved if u.startswith("CONFLICT")]
        if conflicts or not terms.ready():
            raise CheckoutError("TERMS_INCOMPLETE", "Resolve the price, currency and the other person's 'yes' first",
                                400, unresolved=conflicts or terms.unresolved)
        return self.ledger.transition(checkout_id, {L.DRAFT, L.TERMS_CONFIRMED}, L.TERMS_CONFIRMED,
                                      update={"terms": terms.to_dict(), "terms_commitment": terms.commitment(),
                                              "ready": True},
                                      detail={"note": "terms confirmed", "resolved": sorted(resolutions or {})})

    # ------------------------------------------------------ 3. the order
    def build_order(self, checkout_id: str) -> dict:
        co = self.ledger.get(checkout_id)
        if co["state"] not in (L.TERMS_CONFIRMED, L.MISMATCH, L.ORDER_CHANGED):
            raise CheckoutError("WRONG_STATE", f"cannot build an order while {co['state']}")
        terms = terms_from_dict(co["data"]["terms"])
        body = order_from_terms(terms, checkout_id=checkout_id, title=co["data"].get("title"))
        body["payment_source"] = {"paypal": {"experience_context": {
            "user_action": "PAY_NOW", "return_url": f"{self.return_url}?checkout={checkout_id}",
            "cancel_url": f"{self.return_url}?checkout={checkout_id}&cancel=1"}}}
        # A retry of the same build reuses the request id, so PayPal returns the same order.
        # A deliberate rebuild (after a mismatch or an edit) gets a new id and a fresh order.
        n = int(co["data"].get("builds", 0))
        rid = f"cg-create-{checkout_id}-{co['data']['terms_commitment'][:12]}-{n}"
        order = self.paypal.create_order(body, request_id=rid)
        return self._check_order(checkout_id, order["id"], source="callgate", extra={"builds": n + 1})

    def attach_order(self, checkout_id: str, order_id: str, *, source: str = "external") -> dict:
        """Check an order someone else created (a seller by hand, or an AI sales agent)."""
        return self._check_order(checkout_id, order_id, source=source)

    def _check_order(self, checkout_id, order_id, *, source, extra=None):
        co = self.ledger.get(checkout_id)
        allowed = {L.TERMS_CONFIRMED, L.MISMATCH, L.READY, L.ORDER_CHANGED, L.BUYER_CONFIRMED}
        if co["state"] not in allowed:
            raise CheckoutError("WRONG_STATE", f"cannot check an order while {co['state']}")
        order = self.paypal.get_order(order_id)
        other = self.ledger.find_by_order(order_id)
        if other and other["id"] != checkout_id:
            raise CheckoutError("ORDER_IN_USE", "That PayPal order belongs to another checkout")
        self.ledger.transition(checkout_id, co["state"], L.ORDER_ATTACHED,
                               update={"order_id": order_id, "order_source": source, "approval": None, **(extra or {})},
                               detail={"order_id": order_id, "source": source})
        return self._evaluate(checkout_id, order)

    def _evaluate(self, checkout_id, order):
        co = self.ledger.get(checkout_id)
        diffs = compare(terms_from_dict(co["data"]["terms"]), order)
        blocks = blocking(diffs)
        fp = order_fingerprint(order)
        update = {"order_fingerprint": fp, "differences": [d.to_dict() for d in diffs],
                  "order_summary": _summary(order), "approve_url": approve_link(order)}
        to = L.MISMATCH if blocks else L.READY
        return self.ledger.transition(checkout_id, L.ORDER_ATTACHED, to, update=update,
                                      detail={"blocking": [d.field for d in blocks], "fingerprint": fp[:16]})

    # ------------------------------------------------- 4. payer confirms
    def buyer_confirm(self, checkout_id: str, *, seen_fingerprint: str) -> dict:
        co = self.ledger.get(checkout_id)
        if co["state"] != L.READY:
            raise CheckoutError("WRONG_STATE", f"nothing to confirm while {co['state']}")
        order = self.paypal.get_order(co["data"]["order_id"])
        fp = order_fingerprint(order)
        if seen_fingerprint != co["data"]["order_fingerprint"] or fp != co["data"]["order_fingerprint"]:
            # The page the payer looked at is not the order PayPal holds now: show it again.
            self.ledger.transition(checkout_id, L.READY, L.ORDER_ATTACHED, detail={"note": "order changed before confirmation"})
            co = self._evaluate(checkout_id, order)
            raise CheckoutError("ORDER_CHANGED", "The order changed while you were looking; please review it again",
                                checkout=co)
        now = int(self.clock())
        approval = {"version": APPROVAL_VERSION, "checkout_id": checkout_id,
                    "terms_commitment": co["data"]["terms_commitment"], "chat_sha256": co["data"]["chat_sha256"],
                    "order_id": co["data"]["order_id"], "order_fingerprint": fp,
                    "nonce": secrets.token_hex(16), "issued_at": now, "expires_at": now + self.ttl}
        signed = {"payload": approval, "signature": self.key.sign(canonical(approval)).hex()}
        return self.ledger.transition(checkout_id, L.READY, L.BUYER_CONFIRMED, update={"approval": signed},
                                      detail={"note": "payer confirmed this order version", "fingerprint": fp[:16]})

    def _verified_approval(self, co) -> dict:
        signed = co["data"].get("approval") or {}
        payload = signed.get("payload")
        try:
            self.public_key.verify(bytes.fromhex(signed.get("signature", "")), canonical(payload))
        except (InvalidSignature, ValueError, TypeError):
            raise CheckoutError("APPROVAL_INVALID", "Approval signature does not verify", 403) from None
        if payload["checkout_id"] != co["id"] or payload["terms_commitment"] != co["data"]["terms_commitment"] \
                or payload["order_id"] != co["data"]["order_id"]:
            raise CheckoutError("APPROVAL_MISMATCH", "Approval does not belong to this checkout", 403)
        return payload

    # ------------------------------------------------------- 5. capture
    def capture(self, checkout_id: str, *, idempotency_key: str) -> dict:
        stored = self.ledger.begin(idempotency_key, "capture", {"checkout_id": checkout_id})
        if stored is not None:
            return stored
        try:
            result = self._capture(checkout_id)
        except CheckoutError as e:
            if e.code in ("PAYER_NOT_APPROVED", "IN_FLIGHT"):
                self.ledger.release(idempotency_key)     # nothing irreversible happened; allow a retry
                raise
            self.ledger.finish(idempotency_key, {"error": e.code, "message": str(e), "http": e.http})
            raise
        except Exception:
            self.ledger.release(idempotency_key)
            raise
        return self.ledger.finish(idempotency_key, result)

    def _capture(self, checkout_id):
        co = self.ledger.get(checkout_id)
        if co["state"] in (L.CAPTURED, L.CAPTURE_PENDING, L.SHIPPED, L.REFUNDED):
            return self._result(co, note="already captured; no second charge")
        if co["state"] == L.CAPTURING:
            raise CheckoutError("IN_FLIGHT", "A capture for this checkout is already in progress")
        if co["state"] == L.CAPTURE_UNKNOWN:
            co = self.reconcile(checkout_id)
            if co["state"] != L.BUYER_CONFIRMED:
                return self._result(co, note="reconciled an earlier attempt")
        if co["state"] != L.BUYER_CONFIRMED:
            raise CheckoutError("WRONG_STATE", f"cannot capture while {co['state']}")
        approval = self._verified_approval(co)
        if int(self.clock()) >= approval["expires_at"]:
            self.ledger.transition(checkout_id, L.BUYER_CONFIRMED, L.ORDER_ATTACHED, detail={"note": "approval expired"})
            co = self._evaluate(checkout_id, self.paypal.get_order(co["data"]["order_id"]))
            raise CheckoutError("APPROVAL_EXPIRED", "Confirmation expired; review and confirm again", checkout=co)

        order = self.paypal.get_order(approval["order_id"])
        fp = order_fingerprint(order)
        diffs = blocking(compare(terms_from_dict(co["data"]["terms"]), order))
        if fp != approval["order_fingerprint"] or diffs:
            co = self.ledger.transition(checkout_id, L.BUYER_CONFIRMED, L.ORDER_CHANGED,
                                        update={"changed_order_summary": _summary(order),
                                                "differences": [d.to_dict() for d in compare(
                                                    terms_from_dict(co["data"]["terms"]), order)]},
                                        detail={"note": "order changed after confirmation; capture refused",
                                                "approved": approval["order_fingerprint"][:16], "now": fp[:16]})
            raise CheckoutError("ORDER_CHANGED_AFTER_APPROVAL",
                                "The order was modified after the payer confirmed it. Nothing was charged.",
                                checkout=co)
        if order.get("status") != "APPROVED":
            raise CheckoutError("PAYER_NOT_APPROVED", "The payer has not approved this order on PayPal yet",
                                approve_url=approve_link(order))

        # The ship-to address exists only now, after the payer approved on PayPal.
        dest = RK.ship_to(order)
        flags = RK.payment_flags(_messages(co), order, seller_country=self.seller_country)
        override = co["data"].get("destination_override") or {}
        holds = [f for f in RK.blocking(flags)
                 if not (f.code == "DESTINATION_MISMATCH" and dest and override.get("country_code") == dest["country_code"])]
        self.ledger.transition(checkout_id, L.BUYER_CONFIRMED, L.BUYER_CONFIRMED,
                               update={"ship_to": dest, "payment_flags": [f.to_dict() for f in flags]},
                               detail={"note": "checked PayPal ship-to", "country": (dest or {}).get("country_code")})
        if holds:
            co = self.ledger.transition(checkout_id, L.BUYER_CONFIRMED, L.ADDRESS_HOLD,
                                        detail={"note": "payment held: " + holds[0].title})
            raise CheckoutError("ADDRESS_HOLD", holds[0].title + ". Nothing was charged.", checkout=co)

        rid = f"cg-cap-{approval['nonce']}"
        self.ledger.transition(checkout_id, L.BUYER_CONFIRMED, L.CAPTURING,
                               update={"capture_request_id": rid}, detail={"request_id": rid})
        try:
            resp = self.paypal.capture(approval["order_id"], request_id=rid)
        except PayPalTimeout as exc:
            co = self.ledger.transition(checkout_id, L.CAPTURING, L.CAPTURE_UNKNOWN,
                                        detail={"note": "timeout; will reconcile, not retry blindly", "error": str(exc)})
            return self._result(co, note="PayPal did not answer in time; checking the order before doing anything else")
        except PayPalError as exc:
            if exc.name == "ORDER_ALREADY_CAPTURED":
                return self._result(self.reconcile(checkout_id), note="PayPal reports this order already captured")
            if exc.status >= 500:
                # A server error does not tell us whether the capture happened.
                co = self.ledger.transition(checkout_id, L.CAPTURING, L.CAPTURE_UNKNOWN,
                                            detail={"note": "PayPal server error; will reconcile", "error": exc.name})
                return self._result(co, note="PayPal had an error; checking the order before doing anything else")
            co = self.ledger.transition(checkout_id, L.CAPTURING, L.CAPTURE_FAILED,
                                        update={"last_error": exc.name}, detail={"error": exc.name})
            raise CheckoutError("CAPTURE_FAILED", f"PayPal refused the capture: {exc.name}", 402, checkout=co) from None
        return self._result(self._apply_capture(checkout_id, {L.CAPTURING}, resp))

    def _apply_capture(self, checkout_id, expect, order_or_capture, *, via="capture"):
        cap = capture_of(order_or_capture) or (order_or_capture if order_or_capture.get("status") else None)
        status = (cap or {}).get("status")
        to = {"COMPLETED": L.CAPTURED, "PENDING": L.CAPTURE_PENDING}.get(status, L.CAPTURE_FAILED)
        co = self.ledger.get(checkout_id)
        return self.ledger.transition(checkout_id, expect, to,
                                      update={"capture_id": (cap or {}).get("id"), "capture_status": status,
                                              "captured_amount": (cap or {}).get("amount"),
                                              "checklist": SH.checklist(co["data"]["terms"], co["data"].get("title"))},
                                      detail={"via": via, "capture_status": status})

    # ---------------------------------------------------- 6. reconcile
    def reconcile(self, checkout_id: str) -> dict:
        co = self.ledger.get(checkout_id)
        if co["state"] not in (L.CAPTURE_UNKNOWN, L.CAPTURING, L.CAPTURE_PENDING):
            return co
        order = self.paypal.get_order(co["data"]["order_id"])
        if capture_of(order):
            return self._apply_capture(checkout_id, co["state"], order, via="reconcile")
        if co["state"] == L.CAPTURE_PENDING:
            return co
        if order.get("status") == "APPROVED" and co["state"] == L.CAPTURE_UNKNOWN:
            # Never reached PayPal: safe to try again, with the same request id.
            return self.ledger.transition(checkout_id, L.CAPTURE_UNKNOWN, L.BUYER_CONFIRMED,
                                          detail={"note": "reconcile: no capture exists; retry is safe"})
        return co

    # ------------------------------------------------------ 7. webhooks
    def handle_webhook(self, headers: dict, body: bytes) -> dict:
        try:
            event = json.loads(body)
            event_id, etype = event["id"], event["event_type"]
        except (ValueError, KeyError, TypeError):
            raise CheckoutError("BAD_WEBHOOK", "unreadable webhook", 400) from None
        if not self.webhook_id or not self.paypal.verify_webhook(headers, event, self.webhook_id):
            raise CheckoutError("WEBHOOK_UNVERIFIED", "webhook signature did not verify", 401)
        resource = event.get("resource") or {}
        order_id = ((resource.get("supplementary_data") or {}).get("related_ids") or {}).get("order_id")
        co = self.ledger.find_by_order(order_id) if order_id else None
        if not self.ledger.record_webhook(event_id, co and co["id"], etype, body):
            return {"status": "duplicate", "event_id": event_id}
        if co is None:
            self.ledger.webhook_outcome(event_id, "no matching checkout")
            return {"status": "ignored", "reason": "no matching checkout"}
        mapping = {"PAYMENT.CAPTURE.COMPLETED": L.CAPTURED, "PAYMENT.CAPTURE.PENDING": L.CAPTURE_PENDING,
                   "PAYMENT.CAPTURE.DENIED": L.CAPTURE_FAILED, "PAYMENT.CAPTURE.DECLINED": L.CAPTURE_FAILED,
                   "PAYMENT.CAPTURE.REFUNDED": L.REFUNDED}
        to = mapping.get(etype)
        if to is None or to == co["state"] or to not in L.TRANSITIONS[co["state"]]:
            outcome = f"no change ({co['state']})"
        else:
            self.ledger.transition(co["id"], co["state"], to,
                                   update={"capture_id": resource.get("id") or co["data"].get("capture_id"),
                                           "capture_status": resource.get("status"),
                                           "checklist": co["data"].get("checklist") or SH.checklist(co["data"]["terms"], co["data"].get("title"))},
                                   detail={"via": "webhook", "event": etype, "event_id": event_id})
            outcome = f"{co['state']} -> {to}"
        self.ledger.webhook_outcome(event_id, outcome)
        return {"status": "processed", "outcome": outcome}

    def accept_destination(self, checkout_id: str, *, reason: str) -> dict:
        """Seller agrees to ship to PayPal's address for the agreed price; recorded with their reason."""
        co = self.ledger.get(checkout_id)
        reason = (reason or "").strip()[:300]
        if co["state"] != L.ADDRESS_HOLD or not reason:
            raise CheckoutError("BAD_OVERRIDE", "Only a held payment can be released, and it needs a reason", 400)
        dest = co["data"].get("ship_to") or {}
        return self.ledger.transition(checkout_id, L.ADDRESS_HOLD, L.BUYER_CONFIRMED,
                                      update={"destination_override": {"country_code": dest.get("country_code"),
                                                                       "reason": reason, "at": int(self.clock())}},
                                      detail={"note": f"seller accepted shipping to {dest.get('country_code')}: {reason}"})

    # ------------------------------------------------------ 8. shipping
    def add_photo(self, checkout_id: str, line_id: str, data: bytes) -> dict:
        co = self.ledger.get(checkout_id)
        if co["state"] != L.CAPTURED:
            raise CheckoutError("WRONG_STATE", "Packing photos are added after payment and before shipping")
        if line_id not in {x["id"] for x in co["data"].get("checklist", [])}:
            raise CheckoutError("UNKNOWN_LINE", "That is not on this order's packing checklist", 400)
        try:
            photo = SH.store_photo(self.photo_dir, data)
        except ValueError as e:
            raise CheckoutError("BAD_PHOTO", str(e), 400) from None
        photo["taken_at"] = int(self.clock())

        def put(data):
            data.setdefault("photos", {})[line_id] = photo
            (data.get("skipped") or {}).pop(line_id, None)
        return self.ledger.transition(checkout_id, L.CAPTURED, L.CAPTURED, mutate=put,
                                      detail={"note": f"photo for {line_id}", "sha256": photo["sha256"][:16]})

    def skip_line(self, checkout_id: str, line_id: str, reason: str) -> dict:
        co = self.ledger.get(checkout_id)
        reason = (reason or "").strip()[:200]
        if co["state"] != L.CAPTURED or not reason:
            raise CheckoutError("BAD_SKIP", "Say why this one can't be photographed", 400)
        if line_id not in {x["id"] for x in co["data"].get("checklist", [])}:
            raise CheckoutError("UNKNOWN_LINE", "That is not on this order's packing checklist", 400)
        return self.ledger.transition(checkout_id, L.CAPTURED, L.CAPTURED,
                                      mutate=lambda data: data.setdefault("skipped", {}).__setitem__(line_id, reason),
                                      detail={"note": f"skipped {line_id}: {reason}"})

    def ship(self, checkout_id: str, *, carrier: str, tracking_number: str, label_country: str = "",
             label_postal: str = "", weight: str = "", weight_unit: str = "lb",
             declared_value: str | None = None, acknowledge_warnings: bool = False) -> dict:
        co = self.ledger.get(checkout_id)
        if co["state"] == L.SHIPPED:
            return co
        if co["state"] != L.CAPTURED:
            raise CheckoutError("WRONG_STATE", f"cannot ship while {co['state']}")
        d = co["data"]
        missing = [x["label"] for x in d.get("checklist", [])
                   if x["id"] not in (d.get("photos") or {}) and x["id"] not in (d.get("skipped") or {})]
        if missing:
            raise CheckoutError("CHECKLIST_INCOMPLETE", "Photograph or skip (with a reason) every line first", 400,
                                missing=missing)
        item = d["order_summary"]["items"][0]["name"] if (d.get("order_summary") or {}).get("items") else None
        try:
            body = SH.tracking_body(d["capture_id"], tracking_number, carrier, item)
            packed = SH.parse_weight(weight, weight_unit)
            declared = SH.parse_money(declared_value) if declared_value not in (None, "") else None
        except ValueError as e:
            raise CheckoutError("BAD_SHIPMENT", str(e), 400) from None
        summary = d.get("order_summary") or {}
        item_value = Decimal(summary.get("total") or "0") - Decimal(summary.get("shipping") or "0")
        flags = RK.ship_flags(ship_to_addr=d.get("ship_to"), label_country=label_country, label_postal=label_postal,
                              carrier=body.get("carrier_name_other") or body["carrier"], item_value=item_value,
                              declared_value=declared)
        blocks = RK.blocking(flags)
        if blocks:
            raise CheckoutError("LABEL_BLOCKED", blocks[0].title, 409, flags=[f.to_dict() for f in flags])
        warns = [f for f in flags if f.severity == RK.WARN]
        if warns and not acknowledge_warnings:
            raise CheckoutError("SHIP_WARNINGS", "Read these before shipping", 409, flags=[f.to_dict() for f in flags])
        rid = "cg-track-" + hashlib.sha256(f"{checkout_id}|{body['tracking_number']}".encode()).hexdigest()[:24]
        self.paypal.add_tracking(d["order_id"], body, request_id=rid)
        shipment = {k: body[k] for k in ("tracking_number", "carrier") if k in body}
        if "carrier_name_other" in body:
            shipment["carrier_name_other"] = body["carrier_name_other"]
        shipment.update({"shipped_at": int(self.clock()), "packed_weight": packed,
                         "label_destination": {"country_code": label_country.strip().upper(),
                                               "postal_code": RK.normalize_postal(label_postal, label_country or "US")},
                         "declared_value": None if declared is None else str(declared),
                         "flags": [f.to_dict() for f in flags]})
        return self.ledger.transition(checkout_id, L.CAPTURED, L.SHIPPED, update={"shipment": shipment},
                                      detail={"note": "tracking sent to PayPal", "tracking": body["tracking_number"]})

    def acknowledge(self, checkout_id: str, *, as_described: bool, note: str = "") -> dict:
        """The payer says it arrived as described — or what was wrong — in their own words."""
        co = self.ledger.get(checkout_id)
        if co["state"] != L.SHIPPED:
            raise CheckoutError("WRONG_STATE", "You can confirm delivery once the order has shipped")
        if co["data"].get("buyer_ack"):
            return co
        note = (note or "").strip()[:500]
        if not as_described and not note:
            raise CheckoutError("NOTE_REQUIRED", "Say what was different, so the seller can fix it", 400)
        ack = {"as_described": bool(as_described), "note": note, "at": int(self.clock())}
        return self.ledger.transition(checkout_id, L.SHIPPED, L.SHIPPED, update={"buyer_ack": ack},
                                      detail={"note": "payer: received as described" if as_described
                                              else f"payer reported a problem: {note}"})

    def photo_path(self, checkout_id: str, sha256: str):
        co = self.ledger.get(checkout_id)
        if sha256 not in {p["sha256"] for p in (co["data"].get("photos") or {}).values()}:
            raise CheckoutError("NOT_FOUND", "no such photo on this checkout", 404)
        return self.photo_dir / sha256

    # ---------------------------------------------------- 9. disputes
    def evidence_pack(self, checkout_id: str) -> dict:
        co = self.ledger.get(checkout_id)
        if co["state"] not in (L.CAPTURED, L.SHIPPED, L.REFUNDED):
            raise CheckoutError("WRONG_STATE", "Evidence exists only for paid checkouts")
        receipt = self.receipt(checkout_id)
        photos = co["data"].get("photos") or {}
        return {"input": SH.evidence_input(co, receipt), "receipt": receipt,
                "documents": [{"line": k, "sha256": v["sha256"], "content_type": v["content_type"]}
                              for k, v in photos.items()]}

    def submit_evidence(self, checkout_id: str, dispute_id: str) -> dict:
        pack = self.evidence_pack(checkout_id)
        files = [("callgate-receipt.json", json.dumps(pack["receipt"], indent=2).encode(), "application/json")]
        ext = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "image/heic": "heic"}
        for doc in pack["documents"][:9]:
            files.append((f"{doc['line']}.{ext.get(doc['content_type'], 'bin')}",
                          (self.photo_dir / doc["sha256"]).read_bytes(), doc["content_type"]))
        self.paypal.provide_evidence(dispute_id, pack["input"], files)
        co = self.ledger.get(checkout_id)
        return self.ledger.transition(checkout_id, co["state"], co["state"],
                                      update={"evidence_submitted": {"dispute_id": dispute_id, "files": len(files),
                                                                     "at": int(self.clock())}},
                                      detail={"note": f"evidence sent to PayPal dispute {dispute_id}", "files": len(files)})

    # -------------------------------------------------------- receipts
    def receipt(self, checkout_id: str) -> dict:
        co = self.ledger.get(checkout_id)
        d = co["data"]
        terms = d["terms"]
        payload = {"version": RECEIPT_VERSION, "checkout_id": checkout_id, "state": co["state"],
                   "issued_at": int(self.clock()), "chat_sha256": d["chat_sha256"],
                   "terms_commitment": d.get("terms_commitment"),
                   "agreed": {"currency": (terms.get("currency") or {}).get("value"),
                              "total": (terms.get("total") or {}).get("value"),
                              "shipping": (terms.get("shipping") or {}).get("value"),
                              "includes": [i["value"] for i in terms.get("inclusions", [])]},
                   "order_id": d.get("order_id"), "order_fingerprint": d.get("order_fingerprint"),
                   "approval_nonce": ((d.get("approval") or {}).get("payload") or {}).get("nonce"),
                   "capture_id": d.get("capture_id"), "capture_status": d.get("capture_status"),
                   "shipment": d.get("shipment"),
                   "packing_photos": {k: v["sha256"] for k, v in (d.get("photos") or {}).items()},
                   "not_photographed": d.get("skipped") or {},
                   "ship_to": {k: (d.get("ship_to") or {}).get(k) for k in ("country_code", "postal_code")} if d.get("ship_to") else None,
                   "destination_override": d.get("destination_override"),
                   "flags": sorted({f["code"] for f in (d.get("chat_flags") or []) + (d.get("payment_flags") or [])
                                    + ((d.get("shipment") or {}).get("flags") or [])}),
                   "buyer_acknowledgment": d.get("buyer_ack"),
                   "note": "Records what was agreed, confirmed, charged and photographed before shipping. "
                           "It does not prove what is in the photos or the item's condition."}
        return {"payload": payload, "signature": self.key.sign(canonical(payload)).hex(),
                "public_key": self.public_key.public_bytes_raw().hex()}

    def _result(self, co, note: str | None = None) -> dict:
        out = {"checkout_id": co["id"], "state": co["state"], "capture_id": co["data"].get("capture_id"),
               "capture_status": co["data"].get("capture_status")}
        if note:
            out["note"] = note
        return out


def verify_receipt(receipt: dict, public_key_hex: str | None = None) -> dict:
    key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key_hex or receipt["public_key"]))
    key.verify(bytes.fromhex(receipt["signature"]), canonical(receipt["payload"]))
    return receipt["payload"]


def _messages(co):
    from .terms import Message
    return [Message(m["index"], m["sender"], m["text"]) for m in co["data"]["messages"]]


def _summary(order: dict) -> dict:
    pu = (order.get("purchase_units") or [{}])[0]
    amount = pu.get("amount") or {}
    bd = amount.get("breakdown") or {}
    return {"id": order.get("id"), "status": order.get("status"), "currency": amount.get("currency_code"),
            "total": amount.get("value"), "shipping": (bd.get("shipping") or {}).get("value"),
            "items": [{"name": i.get("name"), "quantity": i.get("quantity"),
                       "unit": (i.get("unit_amount") or {}).get("value")} for i in pu.get("items", [])],
            "description": pu.get("description")}
