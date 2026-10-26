import socket
import threading
import time

import anyio
import httpx
import pytest
import uvicorn

from integrations.paypal_checkout.fake_paypal import FakePayPal
from integrations.paypal_checkout.server.app import create_asgi
from scripts.paypal_agent_demo import run


def _port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def server(tmp_path, monkeypatch):
    def start(token=None):
        if token:
            monkeypatch.setenv("CALLGATE_AGENT_TOKEN", token)
        port = _port()
        base = f"http://127.0.0.1:{port}"
        app = create_asgi(state_dir=tmp_path, fake=FakePayPal(), model_reader=None, public_url=base)
        srv = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
        t = threading.Thread(target=srv.run, daemon=True)
        t.start()
        for _ in range(100):
            if srv.started:
                break
            time.sleep(0.05)
        started.append((srv, t))
        return base
    started = []
    yield start
    for srv, t in started:
        srv.should_exit = True
        t.join(timeout=5)


def test_agent_can_draft_but_never_get_paid_for_a_wrong_order(server):
    base = server()
    r = anyio.run(run, base, None, True, lambda *_: None)
    assert r["tools"] == ["get_checkout", "propose_order", "read_deal"]       # no capture, no confirm
    assert r["early"]["result"] == "WAITING_FOR_SELLER"
    assert any("price changed after agreement" in u for u in r["early"]["unresolved"])  # planted $180 reopened it
    assert r["bad"]["result"] == "BLOCKED_MISMATCH" and "payer_link" not in r["bad"]
    assert {d["field"] for d in r["bad"]["blocking_differences"]} == {"total"}
    assert r["good"]["result"] == "VERIFIED" and r["good"]["payer_link"].endswith(r["checkout_id"])


def test_agent_gateway_requires_token_when_configured(server):
    base = server(token="agent-secret-123")
    assert httpx.post(base + "/mcp", json={}).status_code == 401
    r = anyio.run(run, base, "agent-secret-123", True, lambda *_: None)
    assert r["good"]["result"] == "VERIFIED"
    assert httpx.get(base + "/api/config").status_code == 200       # pages stay public
