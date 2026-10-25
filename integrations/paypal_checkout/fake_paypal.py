"""In-process stand-in for the PayPal sandbox, used by tests and the offline demo.

It is NOT PayPal.  It implements the handful of documented behaviours this
project depends on, so the real PayPalClient code path is exercised:
  * PayPal-Request-Id: same id -> same response, no second side effect
  * capture requires an APPROVED order and happens at most once
  * PATCH can change the amount before capture
  * webhook verification via /v1/notifications/verify-webhook-signature
Failure injection lets tests reproduce the hard cases: a timeout *after* the
capture committed, a decline, and a pending capture.
"""
from __future__ import annotations

import copy
import hashlib
import hmac
import itertools
import json
import secrets
import time
from decimal import Decimal

import httpx


class FakePayPal:
    def __init__(self, base_url: str = "https://api-m.sandbox.paypal.com", webhook_id: str = "WH-FAKE"):
        self.base_url = base_url
        self.webhook_id = webhook_id
        self.orders: dict[str, dict] = {}
        self.request_ids: dict[tuple[str, str], tuple[int, dict]] = {}
        self.capture_count: dict[str, int] = {}
        self.trackers: dict[str, list[dict]] = {}
        self.evidence: dict[str, list[dict]] = {}
        self.fail_next_capture: str | None = None    # "timeout_after_commit" | "decline" | "pending" | "timeout_before" | "server_error_after_commit"
        self._secret = secrets.token_bytes(32)
        self._ids = itertools.count(1)

    # --------------------------------------------------------- test helpers
    def transport(self) -> httpx.MockTransport:
        return httpx.MockTransport(self._handle)

    def approve(self, order_id: str, payer_email: str = "buyer@example.com") -> None:
        o = self.orders[order_id]
        if o["status"] not in ("CREATED", "PAYER_ACTION_REQUIRED"):
            raise ValueError(f"cannot approve order in {o['status']}")
        o["status"] = "APPROVED"
        o["payer"] = {"email_address": payer_email, "payer_id": "FAKEPAYER1"}

    def set_amount(self, order_id: str, value: str) -> None:
        """Simulate a merchant-side edit (typo, compromised agent) after the buyer looked."""
        pu = self.orders[order_id]["purchase_units"][0]
        cur = pu["amount"]["currency_code"]
        old = Decimal(pu["amount"]["value"])
        pu["amount"]["value"] = value
        bd = pu["amount"].get("breakdown")
        if bd and "item_total" in bd:
            bd["item_total"]["value"] = str(Decimal(bd["item_total"]["value"]) + Decimal(value) - old)
            if pu.get("items"):
                q = int(pu["items"][0]["quantity"])
                pu["items"][0]["unit_amount"] = {"currency_code": cur,
                                                 "value": str(Decimal(bd["item_total"]["value"]) / q)}

    def webhook(self, event_type: str, order_id: str) -> tuple[dict, dict]:
        """Build (headers, event) as PayPal would deliver them for this order's capture."""
        o = self.orders[order_id]
        cap = (o["purchase_units"][0].get("payments") or {}).get("captures", [{}])[0]
        event = {"id": f"WH-EVT-{secrets.token_hex(6).upper()}", "event_type": event_type,
                 "resource_type": "capture",
                 "resource": {"id": cap.get("id", "UNKNOWN"),
                              "status": {"PAYMENT.CAPTURE.COMPLETED": "COMPLETED",
                                         "PAYMENT.CAPTURE.DENIED": "DECLINED",
                                         "PAYMENT.CAPTURE.PENDING": "PENDING",
                                         "PAYMENT.CAPTURE.REFUNDED": "REFUNDED"}.get(event_type, "UNKNOWN"),
                              "amount": o["purchase_units"][0]["amount"],
                              "supplementary_data": {"related_ids": {"order_id": order_id}}},
                 "create_time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        tid = secrets.token_hex(8)
        sig = hmac.new(self._secret, tid.encode() + json.dumps(event, sort_keys=True).encode(),
                       hashlib.sha256).hexdigest()
        headers = {"PAYPAL-AUTH-ALGO": "FAKE-HMAC-SHA256", "PAYPAL-CERT-URL": "https://fake.invalid/cert",
                   "PAYPAL-TRANSMISSION-ID": tid, "PAYPAL-TRANSMISSION-SIG": sig,
                   "PAYPAL-TRANSMISSION-TIME": event["create_time"]}
        return headers, event

    # -------------------------------------------------------------- server
    def _handle(self, request: httpx.Request) -> httpx.Response:
        path, method = request.url.path, request.method
        if path == "/v1/oauth2/token":
            return httpx.Response(200, json={"access_token": "FAKE-TOKEN", "expires_in": 32400})
        if request.headers.get("Authorization") != "Bearer FAKE-TOKEN":
            return _err(401, "AUTHENTICATION_FAILURE")
        rid = request.headers.get("PayPal-Request-Id")
        if rid and (path, rid) in self.request_ids:
            status, body = self.request_ids[(path, rid)]
            return httpx.Response(status, json=copy.deepcopy(body))
        if path.startswith("/v1/customer/disputes/") and path.endswith("/provide-evidence"):
            ctype = request.headers.get("content-type", "")
            if not ctype.startswith("multipart/form-data"):
                return _err(415, "UNSUPPORTED_MEDIA_TYPE")
            raw = request.content
            dispute = path.split("/")[4]
            self.evidence.setdefault(dispute, []).append({"bytes": len(raw), "parts": raw.count(b"Content-Disposition")})
            return httpx.Response(200, json={"links": [{"rel": "self", "href": f"{self.base_url}/v1/customer/disputes/{dispute}"}]})
        body = json.loads(request.content or b"null")

        if path == "/v2/checkout/orders" and method == "POST":
            status, out = self._create(body)
        elif path == "/v1/notifications/verify-webhook-signature":
            status, out = self._verify(body)
        elif path.startswith("/v2/checkout/orders/"):
            parts = path.split("/")
            oid = parts[4]
            if oid not in self.orders:
                return _err(404, "RESOURCE_NOT_FOUND")
            if len(parts) == 5 and method == "GET":
                status, out = 200, copy.deepcopy(self.orders[oid])
            elif len(parts) == 5 and method == "PATCH":
                status, out = self._patch(oid, body)
            elif len(parts) == 6 and parts[5] == "track" and method == "POST":
                status, out = self._track(oid, body)
            elif len(parts) == 6 and parts[5] == "capture" and method == "POST":
                if self.fail_next_capture == "timeout_before":
                    self.fail_next_capture = None
                    raise httpx.ReadTimeout("injected timeout before reaching PayPal", request=request)
                status, out = self._capture(oid)
                if self.fail_next_capture == "server_error_after_commit" and status == 201:
                    self.fail_next_capture = None
                    return _err(500, "INTERNAL_SERVER_ERROR")
                if self.fail_next_capture == "timeout_after_commit" and status == 201:
                    self.fail_next_capture = None
                    if rid:
                        self.request_ids[(path, rid)] = (status, copy.deepcopy(out))
                    raise httpx.ReadTimeout("injected timeout after capture committed", request=request)
            else:
                return _err(404, "NOT_FOUND")
        else:
            return _err(404, "NOT_FOUND")
        if rid and status < 500:
            self.request_ids[(path, rid)] = (status, copy.deepcopy(out))
        return httpx.Response(status, json=out)

    def _create(self, body):
        try:
            pu = body["purchase_units"][0]
            Decimal(pu["amount"]["value"])
        except (KeyError, IndexError, TypeError, ArithmeticError):
            return 422, {"name": "UNPROCESSABLE_ENTITY", "details": [{"issue": "INVALID_PARAMETER_VALUE"}]}
        oid = f"FAKE{next(self._ids):012d}"
        order = {"id": oid, "intent": body.get("intent", "CAPTURE"), "status": "PAYER_ACTION_REQUIRED",
                 "purchase_units": copy.deepcopy(body["purchase_units"]),
                 "links": [{"rel": "self", "href": f"{self.base_url}/v2/checkout/orders/{oid}", "method": "GET"},
                           {"rel": "payer-action", "href": f"https://www.sandbox.paypal.com/checkoutnow?token={oid}",
                            "method": "GET"}]}
        for pu in order["purchase_units"]:
            pu.setdefault("reference_id", "default")
            pu.setdefault("payee", {"merchant_id": "FAKEMERCHANT"})
        self.orders[oid] = order
        return 200, copy.deepcopy(order)

    def _patch(self, oid, ops):
        o = self.orders[oid]
        if o["status"] not in ("CREATED", "PAYER_ACTION_REQUIRED", "APPROVED"):
            return 422, {"name": "UNPROCESSABLE_ENTITY", "details": [{"issue": "ORDER_ALREADY_COMPLETED"}]}
        for op in ops or []:
            if op.get("op") == "replace" and op.get("path", "").endswith("/amount"):
                o["purchase_units"][0]["amount"] = copy.deepcopy(op["value"])
            elif op.get("op") == "replace" and op.get("path", "").endswith("/items"):
                o["purchase_units"][0]["items"] = copy.deepcopy(op["value"])
            else:
                return 422, {"name": "UNPROCESSABLE_ENTITY", "details": [{"issue": "PATCH_PATH_NOT_SUPPORTED"}]}
        return 204, {}

    def _capture(self, oid):
        o = self.orders[oid]
        if o["status"] == "COMPLETED":
            return 422, {"name": "UNPROCESSABLE_ENTITY", "details": [{"issue": "ORDER_ALREADY_CAPTURED"}]}
        if o["status"] != "APPROVED":
            return 422, {"name": "UNPROCESSABLE_ENTITY", "details": [{"issue": "ORDER_NOT_APPROVED"}]}
        mode, self.fail_next_capture = self.fail_next_capture, (
            self.fail_next_capture if self.fail_next_capture in ("timeout_after_commit", "server_error_after_commit") else None)
        if mode == "decline":
            return 422, {"name": "UNPROCESSABLE_ENTITY", "details": [{"issue": "INSTRUMENT_DECLINED"}]}
        self.capture_count[oid] = self.capture_count.get(oid, 0) + 1
        cap_status = "PENDING" if mode == "pending" else "COMPLETED"
        cap = {"id": f"CAP{secrets.token_hex(6).upper()}", "status": cap_status,
               "amount": copy.deepcopy(o["purchase_units"][0]["amount"])}
        cap["amount"].pop("breakdown", None)
        o["purchase_units"][0]["payments"] = {"captures": [cap]}
        o["status"] = "COMPLETED"
        return 201, copy.deepcopy(o)

    def _track(self, oid, body):
        o = self.orders[oid]
        cap = ((o["purchase_units"][0].get("payments") or {}).get("captures") or [{}])[0]
        if o["status"] != "COMPLETED" or body.get("capture_id") != cap.get("id"):
            return 422, {"name": "UNPROCESSABLE_ENTITY", "details": [{"issue": "CAPTURE_ID_NOT_FOUND"}]}
        if not body.get("tracking_number") or not body.get("carrier"):
            return 400, {"name": "INVALID_REQUEST", "details": [{"issue": "MISSING_REQUIRED_PARAMETER"}]}
        tracker = {"id": f"{cap['id']}-{body['tracking_number']}", "status": "SHIPPED", **body}
        self.trackers.setdefault(oid, []).append(tracker)
        o["purchase_units"][0].setdefault("shipping", {})["trackers"] = self.trackers[oid]
        return 201, copy.deepcopy(o)

    def _verify(self, body):
        try:
            tid, sig, event = body["transmission_id"], body["transmission_sig"], body["webhook_event"]
        except (KeyError, TypeError):
            return 400, {"name": "VALIDATION_ERROR"}
        expect = hmac.new(self._secret, tid.encode() + json.dumps(event, sort_keys=True).encode(),
                          hashlib.sha256).hexdigest()
        ok = hmac.compare_digest(expect, sig) and body.get("webhook_id") == self.webhook_id
        return 200, {"verification_status": "SUCCESS" if ok else "FAILURE"}


def _err(status, name):
    return httpx.Response(status, json={"name": name, "message": name})
