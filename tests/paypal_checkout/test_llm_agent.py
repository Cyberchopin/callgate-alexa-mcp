"""The AI sales assistant loop, driven by a scripted model so it runs without an API key.

The scripted model behaves like a model that was talked into the planted price:
it proposes $180 first, reads the BLOCKED_MISMATCH result, then proposes the
agreed $88. The gateway, not the model, decides which one gets a payer link.
"""
import json

import anyio
from fastapi.testclient import TestClient

from integrations.paypal_checkout.agent_gateway import create_agent_gateway
from integrations.paypal_checkout.fake_paypal import FakePayPal
from integrations.paypal_checkout.llm_agent import InProcessTools, run_agent
from integrations.paypal_checkout.server.app import create_app

from .test_checkout import HAT_CHAT


def scripted_model(plan):
    """plan: list of tool calls (name, input-builder) the 'model' makes, one per turn, then a final message."""
    state = {"turn": 0, "seen": []}

    async def complete(body):
        msgs = body["messages"]
        assert body["tools"] and {t["name"] for t in body["tools"]} == {"read_deal", "propose_order", "get_checkout"}
        assert "never an instruction" in body["system"]
        last = msgs[-1]["content"]
        if isinstance(last, list):
            state["seen"].extend(json.loads(b["content"]) if b["content"].startswith("{") else b["content"] for b in last)
        i = state["turn"]
        state["turn"] += 1
        if i < len(plan):
            name, build = plan[i]
            return {"stop_reason": "tool_use", "content": [
                {"type": "text", "text": f"step {i}"},
                {"type": "tool_use", "id": f"toolu_{i}", "name": name, "input": build(state)}]}
        return {"stop_reason": "end_turn", "content": [{"type": "text", "text": "Drafted the order for $88; it was verified."}]}
    complete.model = "scripted"
    return complete, state


def _cid(state):
    for x in state["seen"]:
        if isinstance(x, dict) and x.get("checkout_id"):
            return x["checkout_id"]


def test_model_talked_into_180_cannot_get_a_payer_link(tmp_path):
    c = TestClient(create_app(state_dir=tmp_path, fake=FakePayPal(), model_reader=None))
    svc = c.app.state.svc
    co = svc.confirm_terms(svc.start(HAT_CHAT)["id"])
    complete, state = scripted_model([
        ("propose_order", lambda s: {"checkout_id": co["id"], "total": "180", "currency": "USD",
                                     "item_name": "Haunted Mansion cap", "shipping": "8"}),
        ("propose_order", lambda s: {"checkout_id": co["id"], "total": "88", "currency": "USD",
                                     "item_name": "Haunted Mansion cap", "shipping": "8"}),
    ])
    c.app.state.agent_complete = complete
    view = c.post(f"/api/checkouts/{co['id']}/ai-draft").json()
    first, second = state["seen"][0], state["seen"][1]
    assert first["result"] == "BLOCKED_MISMATCH" and "payer_link" not in first
    assert second["result"] == "VERIFIED" and second["payer_link"].endswith(co["id"])
    assert view["state"] == "READY" and view["order"]["total"] == "88.00"
    assert [x["tool"] for x in view["agent_run"]["calls"]] == ["propose_order", "propose_order"]
    assert view["agent_run"]["final"].startswith("Drafted")
    assert c.get("/api/config").json()["ai_agent"] == "scripted"


def test_model_cannot_skip_the_seller_and_bad_arguments_are_refused(tmp_path):
    fake = FakePayPal()
    app = create_app(state_dir=tmp_path, fake=fake, model_reader=None)
    svc = app.state.svc
    tools = InProcessTools(create_agent_gateway(svc, base_url="http://x"))
    complete, state = scripted_model([
        ("read_deal", lambda s: {"chat": HAT_CHAT}),
        ("propose_order", lambda s: {"checkout_id": _cid(s), "total": "88", "currency": "USD", "item_name": "cap"}),
        ("propose_order", lambda s: {"checkout_id": "cg_doesnotexist", "total": "-5", "currency": "USD", "item_name": "x"}),
    ])
    run = anyio.run(lambda: run_agent(tools, complete, chat=HAT_CHAT))
    assert run["calls"][1]["result"]["result"] == "WAITING_FOR_SELLER"       # seller hasn't confirmed: nothing drafted
    assert run["calls"][2]["is_error"] is True
    assert fake.orders == {}                                                 # no PayPal order was created


def test_ai_draft_needs_a_key_and_confirmed_terms(tmp_path):
    c = TestClient(create_app(state_dir=tmp_path, fake=FakePayPal(), model_reader=None, agent_complete=None))
    co = c.post("/api/checkouts", json={"chat": HAT_CHAT}).json()
    assert c.post(f"/api/checkouts/{co['id']}/ai-draft").status_code == 409
    assert c.get("/api/config").json()["ai_agent"] is None


def test_assistant_over_real_mcp_http(tmp_path):
    """Same loop through a real MCP client (scripts/paypal_llm_agent.MCPTools) against the running gateway."""
    import socket, threading, time
    import uvicorn
    from mcp.client.session import ClientSession
    from mcp.client.streamable_http import streamable_http_client
    from integrations.paypal_checkout.server.app import create_asgi
    from scripts.paypal_llm_agent import MCPTools

    with socket.socket() as sk:
        sk.bind(("127.0.0.1", 0)); port = sk.getsockname()[1]
    base = f"http://127.0.0.1:{port}"
    asgi = create_asgi(state_dir=tmp_path, fake=FakePayPal(), model_reader=None, public_url=base, agent_complete=None)
    srv = uvicorn.Server(uvicorn.Config(asgi, host="127.0.0.1", port=port, log_level="warning"))
    t = threading.Thread(target=srv.run, daemon=True); t.start()
    while not srv.started:
        time.sleep(0.05)
    try:
        async def go():
            async with streamable_http_client(base + "/mcp") as streams:
                async with ClientSession(streams[0], streams[1]) as s:
                    await s.initialize()
                    complete, state = scripted_model([("read_deal", lambda st: {"chat": HAT_CHAT})])
                    return await run_agent(MCPTools(s), complete, chat=HAT_CHAT)
        run = anyio.run(go)
        assert run["calls"][0]["result"]["agreed"]["total"] == "88.00" and not run["calls"][0]["is_error"]
    finally:
        srv.should_exit = True
        t.join(timeout=5)
