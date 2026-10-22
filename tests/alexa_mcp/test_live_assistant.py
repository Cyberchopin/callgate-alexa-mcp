"""The live simulated-assistant page drives the real merchant and gateway MCP servers."""
import subprocess
import sys
import time
from contextlib import contextmanager

import httpx
import pytest

from tests.alexa_mcp.test_live_demo import _free_port, _wait_for_https

TOKEN = "assistant-test-token"


@contextmanager
def running_services(tmp_path):
    ports = [_free_port() for _ in range(3)]
    # A file, not an undrained pipe: a full pipe blocks every thread that logs.
    log = (tmp_path / "launcher.log").open("w", encoding="utf-8")
    server = subprocess.Popen([sys.executable, "-m", "scripts.run_amazon_services",
        "--replay-db", str(tmp_path / "replay.sqlite3"), "--merchant-port", str(ports[0]),
        "--gateway-port", str(ports[1]), "--assistant-port", str(ports[2]),
        "--contact-token", TOKEN], stdout=log, stderr=subprocess.STDOUT)
    try:
        _wait_for_https(ports[1])
        base = f"http://127.0.0.1:{ports[2]}"
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            try:
                httpx.get(base + "/", timeout=1)
                break
            except httpx.HTTPError:
                time.sleep(0.2)
        yield base
    finally:
        server.terminate()
        server.wait(timeout=10)
        log.close()


def wait_for(base, run_id, predicate, timeout=60):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        state = httpx.get(f"{base}/api/runs/{run_id}").json()
        if predicate(state):
            return state
        time.sleep(0.2)
    raise AssertionError(f"timed out; last state: {state}")


def kinds(state):
    return [event["kind"] for event in state["events"]]


def start(base, scenario):
    response = httpx.post(f"{base}/api/run", json={"scenario": scenario},
                          headers={"Origin": base})
    assert response.status_code == 202, response.text
    return response.json()["run_id"]


def decide(review_url, approved):
    response = httpx.post(review_url, json={"approved": approved}, verify=False,
                          headers={"X-CallGate-Contact-Token": TOKEN})
    assert response.status_code == 200


def pause_event(state):
    return next(event for event in state["events"] if event["kind"] == "pause")


def test_transfer_pauses_completes_once_then_needs_new_review(tmp_path):
    with running_services(tmp_path) as base:
        page = httpx.get(base + "/")
        assert "SIMULATED VOICE ASSISTANT" in page.text
        assert "default-src 'self'" in page.headers["Content-Security-Policy"]

        run_id = start(base, "transfer")
        busy = httpx.post(f"{base}/api/run", json={"scenario": "shopping"},
                          headers={"Origin": base})
        assert busy.status_code == 409
        state = wait_for(base, run_id, lambda s: "pause" in kinds(s))
        connection = next(event for event in state["events"] if event["kind"] == "system")
        assert "2025-11-25" in connection["text"] and "send_money" in connection["text"]
        pause = pause_event(state)
        assert (pause["amount_cents"], pause["destination"]) == (5000, "simulated-wallet")
        assert "5000" not in pause["review_url"]
        assert "done" not in kinds(state)

        decide(pause["review_url"], True)
        state = wait_for(base, run_id, lambda s: s["finished"])
        assert kinds(state).count("done") == 1
        assert "consumed" in kinds(state)
        done = next(event for event in state["events"] if event["kind"] == "done")
        assert done["real_action_executed"] is False


def test_injected_shopping_request_is_denied_and_canary_blocked(tmp_path):
    with running_services(tmp_path) as base:
        run_id = start(base, "shopping")
        state = wait_for(base, run_id, lambda s: "pause" in kinds(s))
        products = next(event for event in state["events"] if event["kind"] == "products")
        assert {item["id"] for item in products["items"]} == {"lamp-safe", "lamp-injected"}
        assert any("search_products" in event["text"] for event in state["events"]
                   if event["kind"] == "system")
        assert "untrusted" in kinds(state)
        pause = pause_event(state)
        assert (pause["amount_cents"], pause["destination"]) == (500000, "injected-wallet")

        decide(pause["review_url"], False)
        state = wait_for(base, run_id, lambda s: s["finished"])
        assert "denied" in kinds(state) and "blocked" in kinds(state)
        assert "done" not in kinds(state) and "error" not in kinds(state)
    launcher_log = (tmp_path / "launcher.log").read_text(encoding="utf-8", errors="replace")
    assert "HTTP Request" not in launcher_log


@pytest.mark.parametrize("body,headers,status", [
    ({"scenario": "unknown"}, {}, 400),
    ({"scenario": "transfer"}, {"Origin": "https://attacker.example"}, 403),
])
def test_run_endpoint_rejects_bad_requests(tmp_path, body, headers, status):
    import anyio
    from integrations.alexa_mcp.assistant import create_assistant_app

    app = create_assistant_app("http://127.0.0.1:9/mcp", "https://127.0.0.1:9/mcp")

    async def call():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                     base_url="http://127.0.0.1:8002") as client:
            return await client.post("/api/run", json=body, headers=headers)

    assert anyio.run(call).status_code == status
