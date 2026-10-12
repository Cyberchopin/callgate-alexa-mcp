import anyio
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client

from callgate.verification import issue_for_demo
from integrations.alexa_mcp.server import operation_resource
from scripts.mcp_test_process import running_test_server


async def mcp_call(url, name=None, arguments=None):
    async with streamable_http_client(url) as streams:
        async with ClientSession(streams[0], streams[1]) as session:
            initialized = await session.initialize()
            tools = await session.list_tools()
            result = None if name is None else await session.call_tool(name, arguments)
            return initialized, tools, result


def test_real_client_connects_lists_tools_and_rejects_missing_proof(tmp_path):
    with running_test_server("phase1", tmp_path / "replay.sqlite3") as base_url:
        initialized, tools, result = anyio.run(mcp_call, base_url + "/mcp", "send_money", {
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
    public_key = key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex()
    with running_test_server("phase1", tmp_path / "replay.sqlite3",
                             public_key=public_key, clock=1001) as base_url:
        _, _, result = anyio.run(mcp_call, base_url + "/mcp", "share_verification_code", {
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

    public_key = key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex()
    with running_test_server("phase1", database, public_key=public_key, clock=1001) as base_url:
        _, _, accepted = anyio.run(mcp_call, base_url + "/mcp", "send_money", payload)
    assert accepted.is_error is False

    with running_test_server("phase1", database, public_key=public_key, clock=1001) as base_url:
        _, _, replay = anyio.run(mcp_call, base_url + "/mcp", "send_money", payload)
    assert replay.is_error is True
    assert "already consumed" in str(replay.content)
