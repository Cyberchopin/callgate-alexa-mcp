"""HTTP surface for CallGate Checkout: seller page, payer page, JSON API, PayPal webhook.

Modes
  sandbox  PAYPAL_CLIENT_ID / PAYPAL_CLIENT_SECRET set -> real PayPal sandbox
  fake     otherwise -> in-process FakePayPal; demo controls are enabled

Run:  python -m integrations.paypal_checkout.server  (http://localhost:8787)
"""
from __future__ import annotations

import os
import secrets
from decimal import Decimal
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from fastapi import FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse

from .. import ledger as L
from ..extract import default_model_reader
from ..fake_paypal import FakePayPal
from ..paypal_client import PayPalClient, PayPalError, PayPalTimeout
from ..service import CheckoutError, CheckoutService

UI = Path(__file__).with_name("ui.html")


def _load_key(path: Path) -> Ed25519PrivateKey:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return Ed25519PrivateKey.from_private_bytes(bytes.fromhex(path.read_text().strip()))
    key = Ed25519PrivateKey.generate()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(key.private_bytes_raw().hex())
    return key


def create_app(*, state_dir: str | Path | None = None, fake: FakePayPal | None = None,
               model_reader="default", public_url: str | None = None) -> FastAPI:
    state = Path(state_dir or os.environ.get("CALLGATE_CHECKOUT_STATE", ".callgate-checkout"))
    state.mkdir(parents=True, exist_ok=True)
    public_url = (public_url or os.environ.get("CALLGATE_PUBLIC_URL") or os.environ.get("RENDER_EXTERNAL_URL")
                  or "http://localhost:8787").rstrip("/")
    if fake is None and os.environ.get("PAYPAL_CLIENT_ID"):
        mode, client = "sandbox", PayPalClient.from_env()
        webhook_id = os.environ.get("PAYPAL_WEBHOOK_ID")
    else:
        fake = fake or FakePayPal()
        mode, client, webhook_id = "fake", PayPalClient("fake", "fake", transport=fake.transport()), fake.webhook_id
    reader = default_model_reader() if model_reader == "default" else model_reader
    svc = CheckoutService(L.Ledger(state / "ledger.sqlite3"), client, _load_key(state / "signing.key"),
                          model_reader=reader, return_url=f"{public_url}/return", webhook_id=webhook_id)

    app = FastAPI(title="CallGate Checkout", docs_url=None, redoc_url=None)
    app.state.svc, app.state.fake, app.state.mode = svc, fake, mode
    app.state.public_url = public_url
    demo_on = mode == "fake" or os.environ.get("CALLGATE_DEMO") == "1"

    @app.middleware("http")
    async def demo_gate(request: Request, call_next):
        # Demo controls change orders on purpose; never expose them on a sandbox deploy by accident.
        if request.url.path.startswith("/demo/") and not demo_on:
            return JSONResponse({"error": "DEMO_DISABLED", "message": "set CALLGATE_DEMO=1 to enable"}, status_code=404)
        return await call_next(request)

    @app.exception_handler(CheckoutError)
    async def checkout_error(_, e: CheckoutError):
        body = {"error": e.code, "message": str(e)}
        for k, v in e.extra.items():
            body[k] = _view(svc, v) if k == "checkout" else v
        return JSONResponse(body, status_code=e.http)

    @app.exception_handler(L.Conflict)
    async def conflict(_, e):
        return JSONResponse({"error": "CONFLICT", "message": str(e)}, status_code=409)

    @app.exception_handler(L.InProgress)
    async def in_progress(_, e):
        return JSONResponse({"error": "IN_PROGRESS", "message": "This request is still being processed"},
                            status_code=409, headers={"Retry-After": "1"})

    @app.exception_handler(PayPalError)
    async def paypal_error(_, e: PayPalError):
        return JSONResponse({"error": "PAYPAL", "message": str(e), "debug_id": e.debug_id}, status_code=502)

    @app.exception_handler(PayPalTimeout)
    async def paypal_timeout(_, e):
        return JSONResponse({"error": "PAYPAL_TIMEOUT", "message": "PayPal did not answer; nothing was changed here"},
                            status_code=504)

    # ---------------------------------------------------------------- pages
    @app.get("/", response_class=HTMLResponse)
    def seller_page():
        return UI.read_text(encoding="utf-8")

    @app.get("/pay/{checkout_id}", response_class=HTMLResponse)
    def payer_page(checkout_id: str):
        _get(svc, checkout_id)
        return UI.read_text(encoding="utf-8")

    @app.get("/return")
    def paypal_return(checkout: str, cancel: int = 0):
        return RedirectResponse(f"/pay/{checkout}?back={'cancel' if cancel else 'approved'}", status_code=303)

    # ------------------------------------------------------------------ api
    @app.get("/api/config")
    def config():
        return {"mode": mode, "demo": demo_on, "model": reader.label if reader else None,
                "public_key": svc.public_key.public_bytes_raw().hex()}

    @app.post("/api/checkouts")
    async def start(req: Request):
        body = await req.json()
        chat = body.get("chat")
        if not isinstance(chat, (str, list)) or not chat:
            raise HTTPException(400, "chat is required")
        if isinstance(chat, str) and len(chat) > 20000:
            raise HTTPException(413, "chat too long")
        cur = str(body.get("currency") or "USD").upper()[:3]
        return _view(svc, svc.start(chat, default_currency=cur, title=body.get("title")))

    @app.get("/api/checkouts/{checkout_id}")
    def get(checkout_id: str):
        return _view(svc, _get(svc, checkout_id))

    @app.post("/api/checkouts/{checkout_id}/confirm")
    async def confirm(checkout_id: str, req: Request):
        body = await req.json() if (await req.body()) else {}
        return _view(svc, svc.confirm_terms(checkout_id, resolutions=body.get("resolutions")))

    @app.post("/api/checkouts/{checkout_id}/build-order")
    def build(checkout_id: str):
        return _view(svc, svc.build_order(checkout_id))

    @app.post("/api/checkouts/{checkout_id}/attach")
    async def attach(checkout_id: str, req: Request):
        body = await req.json()
        return _view(svc, svc.attach_order(checkout_id, str(body["order_id"]), source=str(body.get("source", "external"))[:40]))

    @app.post("/api/checkouts/{checkout_id}/buyer-confirm")
    async def buyer_confirm(checkout_id: str, req: Request):
        body = await req.json()
        return _view(svc, svc.buyer_confirm(checkout_id, seen_fingerprint=str(body.get("seen_fingerprint", ""))))

    @app.post("/api/checkouts/{checkout_id}/capture")
    def capture(checkout_id: str, idempotency_key: str = Header(..., alias="Idempotency-Key")):
        result = svc.capture(checkout_id, idempotency_key=idempotency_key)
        if "error" in result:
            return JSONResponse(result, status_code=int(result.get("http", 409)))
        return {**result, "checkout": _view(svc, _get(svc, checkout_id))}

    @app.post("/api/checkouts/{checkout_id}/reconcile")
    def reconcile(checkout_id: str):
        return _view(svc, svc.reconcile(checkout_id))

    @app.get("/api/checkouts/{checkout_id}/receipt")
    def receipt(checkout_id: str):
        _get(svc, checkout_id)
        return svc.receipt(checkout_id)

    @app.post("/api/checkouts/{checkout_id}/photos")
    async def add_photo(checkout_id: str, line: str = Form(...), photo: UploadFile = File(...)):
        data = await photo.read(8 * 1024 * 1024 + 1)
        return _view(svc, svc.add_photo(checkout_id, line, data))

    @app.post("/api/checkouts/{checkout_id}/skip")
    async def skip(checkout_id: str, req: Request):
        body = await req.json()
        return _view(svc, svc.skip_line(checkout_id, str(body.get("line", "")), str(body.get("reason", ""))))

    @app.get("/api/checkouts/{checkout_id}/photos/{sha256}")
    def get_photo(checkout_id: str, sha256: str):
        path = svc.photo_path(checkout_id, sha256)
        co = svc.ledger.get(checkout_id)
        mime = next(p["content_type"] for p in co["data"]["photos"].values() if p["sha256"] == sha256)
        return FileResponse(path, media_type=mime, headers={"Cache-Control": "private, max-age=3600",
                                                            "X-Content-Type-Options": "nosniff"})

    @app.post("/api/checkouts/{checkout_id}/ship")
    async def ship(checkout_id: str, req: Request):
        body = await req.json()
        return _view(svc, svc.ship(checkout_id, carrier=str(body.get("carrier", "")),
                                   tracking_number=str(body.get("tracking_number", ""))))

    @app.get("/api/checkouts/{checkout_id}/evidence")
    def evidence(checkout_id: str):
        _get(svc, checkout_id)
        return svc.evidence_pack(checkout_id)

    @app.post("/api/checkouts/{checkout_id}/disputes/{dispute_id}/evidence")
    def submit_evidence(checkout_id: str, dispute_id: str):
        try:
            return _view(svc, svc.submit_evidence(checkout_id, dispute_id))
        except ValueError as e:
            raise HTTPException(400, str(e)) from None

    @app.post("/webhooks/paypal")
    async def webhook(req: Request):
        return svc.handle_webhook(dict(req.headers), await req.body())

    # ------------------------------------------------------- demo controls
    @app.post("/demo/agent-draft")
    async def agent_draft(req: Request):
        """An AI sales agent drafts the PayPal order itself — sometimes at the wrong price."""
        body = await req.json()
        co = _get(svc, body["checkout_id"])
        cur = (co["data"]["terms"].get("currency") or {}).get("value") or "USD"
        value = format(Decimal(str(body.get("value", "180"))).quantize(Decimal("0.01")), "f")
        order = svc.paypal.create_order({"intent": "CAPTURE", "purchase_units": [{
            "reference_id": "default", "description": "Drafted by sales agent",
            "amount": {"currency_code": cur, "value": value}}]},
            request_id="agent-" + secrets.token_hex(8))
        return _view(svc, svc.attach_order(co["id"], order["id"], source="ai-sales-agent"))

    @app.post("/demo/edit-order")
    async def edit_order(req: Request):
        """Change the order amount on PayPal's side after the payer looked at it."""
        body = await req.json()
        co = _get(svc, body["checkout_id"])
        oid = co["data"]["order_id"]
        order = svc.paypal.get_order(oid)
        amount = order["purchase_units"][0]["amount"]
        new = Decimal(str(body.get("value", "180"))).quantize(Decimal("0.01"))
        delta = new - Decimal(amount["value"])
        amount["value"] = format(new, "f")
        if "breakdown" in amount and "item_total" in amount["breakdown"]:
            it = amount["breakdown"]["item_total"]
            it["value"] = format(Decimal(it["value"]) + delta, "f")
        ops = [{"op": "replace", "path": "/purchase_units/@reference_id=='default'/amount", "value": amount}]
        items = order["purchase_units"][0].get("items")
        if items and "breakdown" in amount:
            q = int(items[0]["quantity"])
            items[0]["unit_amount"]["value"] = format(Decimal(amount["breakdown"]["item_total"]["value"]) / q, "f")
            ops.append({"op": "replace", "path": "/purchase_units/@reference_id=='default'/items", "value": items})
        svc.paypal.patch_order(oid, ops)
        return {"order_id": oid, "new_total": amount["value"]}

    def need_fake():
        if fake is None:
            raise HTTPException(404, "only available in the offline demo")
        return fake

    @app.post("/demo/approve")
    async def demo_approve(req: Request):
        body = await req.json()
        co = _get(svc, body["checkout_id"])
        need_fake().approve(co["data"]["order_id"])
        return {"approved": co["data"]["order_id"]}

    @app.post("/demo/inject")
    async def demo_inject(req: Request):
        mode_ = (await req.json()).get("mode")
        if mode_ not in ("timeout_after_commit", "timeout_before", "decline", "pending", None):
            raise HTTPException(400, "unknown failure mode")
        need_fake().fail_next_capture = mode_
        return {"next_capture": mode_}

    @app.post("/demo/webhook")
    async def demo_webhook(req: Request):
        body = await req.json()
        co = _get(svc, body["checkout_id"])
        headers, event = need_fake().webhook(body.get("type", "PAYMENT.CAPTURE.COMPLETED"), co["data"]["order_id"])
        import json as _json
        raw = _json.dumps(event).encode()
        first = svc.handle_webhook(headers, raw)
        again = svc.handle_webhook(headers, raw) if body.get("redeliver") else None
        return {"first": first, "redelivered": again}

    @app.get("/demo/paypal-count/{checkout_id}")
    def capture_count(checkout_id: str):
        co = _get(svc, checkout_id)
        return {"captures_at_paypal": need_fake().capture_count.get(co["data"].get("order_id"), 0)}

    return app


def _get(svc, checkout_id):
    try:
        return svc.ledger.get(checkout_id)
    except KeyError:
        raise HTTPException(404, "no such checkout") from None


def _view(svc, co):
    d = co["data"]
    approval = (d.get("approval") or {}).get("payload")
    return {"id": co["id"], "state": co["state"], "messages": d["messages"], "terms": d["terms"],
            "readers": d.get("readers"), "terms_commitment": d.get("terms_commitment"),
            "order_id": d.get("order_id"), "order_source": d.get("order_source"),
            "order": d.get("order_summary"), "changed_order": d.get("changed_order_summary"),
            "order_fingerprint": d.get("order_fingerprint"), "differences": d.get("differences", []),
            "approve_url": d.get("approve_url"),
            "approval": None if not approval else {k: approval[k] for k in ("order_fingerprint", "expires_at", "nonce")},
            "capture_id": d.get("capture_id"), "capture_status": d.get("capture_status"),
            "checklist": d.get("checklist", []), "photos": d.get("photos", {}), "skipped": d.get("skipped", {}),
            "shipment": d.get("shipment"), "evidence_submitted": d.get("evidence_submitted"),
            "events": svc.ledger.events(co["id"])}


class _AgentAuth:
    """Bearer-token check in front of /mcp when CALLGATE_AGENT_TOKEN is set."""

    def __init__(self, app, token: str | None):
        self.app, self.token = app, token

    async def __call__(self, scope, receive, send):
        if self.token and scope["type"] == "http" and scope["path"].startswith("/mcp"):
            import hmac
            got = dict(scope.get("headers") or []).get(b"authorization", b"").decode()
            if not hmac.compare_digest(got, f"Bearer {self.token}"):
                from starlette.responses import JSONResponse as _J
                await _J({"error": "AGENT_UNAUTHORIZED"}, status_code=401)(scope, receive, send)
                return
        await self.app(scope, receive, send)


def create_asgi(**kwargs):
    """Checkout pages + API at /, agent gateway (MCP streamable HTTP) at /mcp, one process."""
    from urllib.parse import urlparse

    from mcp.server.transport_security import TransportSecuritySettings
    from starlette.routing import Mount

    from ..agent_gateway import create_agent_gateway

    api = create_app(**kwargs)
    url = urlparse(api.state.public_url)
    hosts = {"127.0.0.1:*", "localhost:*", url.netloc, url.hostname or ""}
    security = TransportSecuritySettings(enable_dns_rebinding_protection=True,
                                         allowed_hosts=sorted(h for h in hosts if h),
                                         allowed_origins=[api.state.public_url, "http://localhost:*", "http://127.0.0.1:*"])
    gateway = create_agent_gateway(api.state.svc, base_url=api.state.public_url)
    root = gateway.streamable_http_app(streamable_http_path="/mcp", transport_security=security)
    root.routes.append(Mount("/", app=api))
    root.state.api = api
    return _AgentAuth(root, os.environ.get("CALLGATE_AGENT_TOKEN"))
