import socket
import threading
import time
from contextlib import contextmanager

import anyio
import pytest
import uvicorn
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client

from callgate.verification import issue_for_demo
from integrations.alexa_mcp.server import CapabilityGateway, create_server, operation_resource


@contextmanager
def running_server(gateway):
    app = create_server(gateway).streamable_http_app(streamable_http_path="/mcp")
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    port = listener.getsockname()[1]
    config = uvicorn.Config(app, log_level="error", lifespan="on")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, kwargs={"sockets": [listener]}, daemon=True)
    thread.start()
    deadline = time.monotonic() + 10
    while not server.started and thread.is_alive() and time.monotonic() < deadline:
        time.sleep(0.01)
    if not server.started:
        raise RuntimeError("MCP test server did not start")
    try:
        yield f"http://127.0.0.1:{port}/mcp"
    finally:
        server.should_exit = True
        thread.join(timeout=10)
        listener.close()


async def mcp_call(url, name=None, arguments=None):
    async with streamable_http_client(url) as streams:
        async with ClientSession(streams[0], streams[1]) as session:
            initialized = await session.initialize()
            tools = await session.list_tools()
            result = None if name is None else await session.call_tool(name, arguments)
            return initialized, tools, result


def test_real_client_connects_lists_tools_and_rejects_missing_proof(tmp_path):
    gateway = CapabilityGateway(tmp_path / "replay.sqlite3")
    with running_server(gateway) as url:
        initialized, tools, result = anyio.run(mcp_call, url, "send_money", {
            "destination": "simulated-wallet", "amount_cents": 5000,
            "session_id": "session-a"})
    assert initialized.protocol_version >= "2025-11-25"
    assert {tool.name for tool in tools.tools} == {
        "send_money", "place_order", "share_verification_code"}
    assert result.is_error is True
    assert "403 POLICY_PROOF_REQUIRED" in str(result.content)


def test_canary_is_blocked_even_with_valid_proof(tmp_path):
    key = Ed25519PrivateKey.generate()
    arguments = {"recipient": "simulated-recipient"}
    proof = issue_for_demo(key, issuer="issuer", session_id="session-a",
        resource=operation_resource("share_verification_code", arguments), now=1000)
    gateway = CapabilityGateway(tmp_path / "replay.sqlite3",
                                {"issuer": key.public_key()}, clock=lambda: 1001)
    with running_server(gateway) as url:
        _, _, result = anyio.run(mcp_call, url, "share_verification_code", {
            **arguments, "session_id": "session-a", "proof": proof.model_dump()})
    assert result.is_error is True
    assert "403 BLOCKED" in str(result.content)


def test_sqlite_replay_rejected_after_server_restart(tmp_path):
    key = Ed25519PrivateKey.generate()
    arguments = {"destination": "simulated-wallet", "amount_cents": 5000}
    proof = issue_for_demo(key, issuer="issuer", session_id="session-a",
        resource=operation_resource("send_money", arguments), now=1000)
    database = tmp_path / "replay.sqlite3"
    payload = {**arguments, "session_id": "session-a", "proof": proof.model_dump()}

    first = CapabilityGateway(database, {"issuer": key.public_key()}, clock=lambda: 1001)
    with running_server(first) as url:
        _, _, accepted = anyio.run(mcp_call, url, "send_money", payload)
    assert accepted.is_error is False

    restarted = CapabilityGateway(database, {"issuer": key.public_key()}, clock=lambda: 1001)
    with running_server(restarted) as url:
        _, _, replay = anyio.run(mcp_call, url, "send_money", payload)
    assert replay.is_error is True
    assert "already consumed" in str(replay.content)
