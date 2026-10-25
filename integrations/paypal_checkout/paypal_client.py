"""Small PayPal REST client for the Orders v2 checkout flow and webhook verification.

Only the calls this checkout needs.  Every mutating call carries a
PayPal-Request-Id so PayPal itself de-duplicates retries; the ledger decides
which id to send.  The transport is injectable so tests run the same code
against fake_paypal.py.

Endpoints (sandbox host https://api-m.sandbox.paypal.com):
  POST  /v1/oauth2/token
  POST  /v2/checkout/orders
  GET   /v2/checkout/orders/{id}
  PATCH /v2/checkout/orders/{id}
  POST  /v2/checkout/orders/{id}/capture
  POST  /v1/notifications/verify-webhook-signature
"""
from __future__ import annotations

import json
import os
import re
import threading
import time

import httpx

SANDBOX = "https://api-m.sandbox.paypal.com"
LIVE = "https://api-m.paypal.com"


class PayPalError(Exception):
    def __init__(self, status: int, name: str, message: str = "", debug_id: str | None = None):
        super().__init__(f"{status} {name}: {message}".strip())
        self.status, self.name, self.debug_id = status, name, debug_id


class PayPalTimeout(Exception):
    """The request may or may not have reached PayPal.  Never treat as failure."""


class PayPalClient:
    def __init__(self, client_id: str, secret: str, *, base_url: str = SANDBOX,
                 transport: httpx.BaseTransport | None = None, timeout: float = 20.0):
        if base_url == LIVE and os.environ.get("CALLGATE_ALLOW_LIVE") != "1":
            raise ValueError("live PayPal is disabled; this project runs against the sandbox")
        self._auth = (client_id, secret)
        self.base_url = base_url.rstrip("/")
        self._http = httpx.Client(base_url=self.base_url, transport=transport, timeout=timeout)
        self._token: tuple[str, float] | None = None
        self._lock = threading.Lock()

    @classmethod
    def from_env(cls, transport=None):
        return cls(os.environ["PAYPAL_CLIENT_ID"], os.environ["PAYPAL_CLIENT_SECRET"],
                   base_url=os.environ.get("PAYPAL_BASE_URL", SANDBOX), transport=transport)

    def _bearer(self) -> str:
        with self._lock:
            if self._token and self._token[1] > time.time() + 60:
                return self._token[0]
            r = self._http.post("/v1/oauth2/token", auth=self._auth,
                                data={"grant_type": "client_credentials"})
            body = self._check(r)
            self._token = (body["access_token"], time.time() + int(body.get("expires_in", 300)))
            return self._token[0]

    def _send(self, method: str, path: str, *, json=None, request_id: str | None = None) -> dict:
        headers = {"Authorization": f"Bearer {self._bearer()}", "Content-Type": "application/json",
                   "Prefer": "return=representation"}
        if request_id:
            headers["PayPal-Request-Id"] = request_id
        try:
            r = self._http.request(method, path, json=json, headers=headers)
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            raise PayPalTimeout(f"{method} {path}: {type(exc).__name__}") from exc
        return self._check(r)

    @staticmethod
    def _check(r: httpx.Response) -> dict:
        if r.status_code >= 400:
            try:
                body = r.json()
            except ValueError:
                body = {}
            name = body.get("name") or body.get("error") or "HTTP_ERROR"
            details = body.get("details") or []
            issue = details[0].get("issue") if details and isinstance(details[0], dict) else None
            raise PayPalError(r.status_code, issue or name, body.get("message", "") or body.get("error_description", ""),
                              body.get("debug_id"))
        return r.json() if r.content else {}

    # ------------------------------------------------------------ orders
    def create_order(self, body: dict, *, request_id: str) -> dict:
        return self._send("POST", "/v2/checkout/orders", json=body, request_id=request_id)

    def get_order(self, order_id: str) -> dict:
        _check_id(order_id)
        return self._send("GET", f"/v2/checkout/orders/{order_id}")

    def patch_order(self, order_id: str, ops: list[dict]) -> None:
        _check_id(order_id)
        self._send("PATCH", f"/v2/checkout/orders/{order_id}", json=ops)

    def capture(self, order_id: str, *, request_id: str) -> dict:
        _check_id(order_id)
        return self._send("POST", f"/v2/checkout/orders/{order_id}/capture", json={}, request_id=request_id)

    def add_tracking(self, order_id: str, body: dict, *, request_id: str) -> dict:
        _check_id(order_id)
        return self._send("POST", f"/v2/checkout/orders/{order_id}/track", json=body, request_id=request_id)

    def provide_evidence(self, dispute_id: str, input_json: dict, files: list[tuple[str, bytes, str]]) -> dict:
        """multipart/form-data: JSON in the `input` part, each document as its own file part."""
        if not re.fullmatch(r"PP-[A-Z]-[A-Z0-9-]{1,40}|PP-[0-9A-Z-]{1,40}", dispute_id):
            raise ValueError("invalid PayPal dispute id")
        parts = [("input", ("input.json", json.dumps(input_json).encode(), "application/json"))]
        parts += [(f"file{i + 1}", (name, data, mime)) for i, (name, data, mime) in enumerate(files)]
        try:
            r = self._http.post(f"/v1/customer/disputes/{dispute_id}/provide-evidence",
                                headers={"Authorization": f"Bearer {self._bearer()}"}, files=parts)
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            raise PayPalTimeout(f"provide-evidence: {type(exc).__name__}") from exc
        return self._check(r)

    # ---------------------------------------------------------- webhooks
    def verify_webhook(self, headers: dict, event: dict, webhook_id: str) -> bool:
        h = {k.lower(): v for k, v in headers.items()}
        body = {"auth_algo": h.get("paypal-auth-algo"), "cert_url": h.get("paypal-cert-url"),
                "transmission_id": h.get("paypal-transmission-id"),
                "transmission_sig": h.get("paypal-transmission-sig"),
                "transmission_time": h.get("paypal-transmission-time"),
                "webhook_id": webhook_id, "webhook_event": event}
        if not all(body.values()):
            return False
        return self._send("POST", "/v1/notifications/verify-webhook-signature", json=body) \
            .get("verification_status") == "SUCCESS"


def _check_id(order_id: str) -> None:
    if not (1 <= len(order_id) <= 36 and order_id.isalnum() and order_id.upper() == order_id):
        raise ValueError("invalid PayPal order id")


def approve_link(order: dict) -> str | None:
    for link in order.get("links", []):
        if link.get("rel") in ("payer-action", "approve"):
            return link.get("href")
    return None


def capture_of(order_or_capture: dict) -> dict | None:
    """First capture object inside an order / capture response, if any."""
    for pu in order_or_capture.get("purchase_units", []):
        caps = (pu.get("payments") or {}).get("captures") or []
        if caps:
            return caps[0]
    return None
