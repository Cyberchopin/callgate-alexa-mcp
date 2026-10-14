"""Real-client regression coverage for stable MCP rejection mappings."""

import re

import anyio
import httpx2
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.shared.exceptions import MCPError, UrlElicitationRequiredError

from callgate.verification import issue_for_demo
from integrations.alexa_mcp.server import operation_resource
from scripts.mcp_test_process import running_test_server


def error_text(result):
    assert result.is_error is True
    return " ".join(str(item) for item in result.content)


async def call_phase1(url, arguments):
    async with streamable_http_client(url + "/mcp") as streams:
        async with ClientSession(streams[0], streams[1]) as session:
            await session.initialize()
            return await session.call_tool("send_money", arguments)


async def require_url(session, arguments):
    try:
        await session.call_tool("send_money", arguments)
    except MCPError as error:
        assert error.code == -32042
        return UrlElicitationRequiredError.from_error(error.error).elicitations[0].url
    raise AssertionError("URL elicitation was not required")


def test_expired_proof_has_stable_tool_error(tmp_path):
    key = Ed25519PrivateKey.generate()
    arguments = {"destination": "private-destination", "amount_cents": 987654}
    proof = issue_for_demo(key, issuer="issuer", session_id="session-a",
        resource=operation_resource("send_money", arguments), now=1000)
    public_key = key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex()
    with running_test_server("phase1", tmp_path / "replay.sqlite3",
                             public_key=public_key, clock=1200) as url:
        result = anyio.run(call_phase1, url, {
            **arguments, "session_id": "session-a", "proof": proof.model_dump()})
    text = error_text(result)
    assert "CG_PROOF_EXPIRED_OR_NOT_YET_VALID" in text
    assert "private-destination" not in text and "987654" not in text


def test_replayed_proof_has_stable_tool_error(tmp_path):
    key = Ed25519PrivateKey.generate()
    arguments = {"destination": "private-destination", "amount_cents": 987654}
    proof = issue_for_demo(key, issuer="issuer", session_id="session-a",
        resource=operation_resource("send_money", arguments), now=1000)
    payload = {**arguments, "session_id": "session-a", "proof": proof.model_dump()}
    public_key = key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex()
    database = tmp_path / "replay.sqlite3"
    with running_test_server("phase1", database, public_key=public_key, clock=1001) as url:
        assert anyio.run(call_phase1, url, payload).is_error is False
    with running_test_server("phase1", database, public_key=public_key, clock=1001) as url:
        replay = anyio.run(call_phase1, url, payload)
    assert "CG_PROOF_REPLAYED" in error_text(replay)


async def exercise_phase2(base_url, case):
    original = {"destination": "private-destination", "amount_cents": 987654,
                "session_id": "session-a", "claimed_identity": "saved-family"}
    async with httpx2.AsyncClient(verify=False) as http:
        async with streamable_http_client(base_url + "/mcp", http_client=http) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                if case == "unknown_contact":
                    result = await session.call_tool(
                        "send_money", {**original, "claimed_identity": "unknown-contact"})
                    return error_text(result)
                approval_url = await require_url(session, original)
                if case == "cross_contact":
                    rejected = await http.post(approval_url, json={"approved": True},
                        headers={"X-CallGate-Contact-Token": "wrong-contact"})
                    assert rejected.status_code == 403
                    next_url = await require_url(session, original)
                    assert re.fullmatch(r"https://127\.0\.0\.1:\d+/approval/[a-f0-9]{32}", next_url)
                    return "-32042 CG_APPROVAL_STILL_REQUIRED"
                approved = await http.post(approval_url, json={"approved": True},
                    headers={"X-CallGate-Contact-Token": "family-token"})
                assert approved.status_code == 200
                result = await session.call_tool(
                    "send_money", {**original, "claimed_identity": "unknown-contact"})
                return error_text(result)


def test_unknown_contact_has_stable_tool_error(tmp_path):
    with running_test_server("phase2", tmp_path / "replay.sqlite3",
                             certificate_dir=tmp_path) as url:
        text = anyio.run(exercise_phase2, url, "unknown_contact")
    assert "CG_CONTACT_NOT_REGISTERED" in text
    assert "SSE stream ended without a response" not in text
    assert "private-destination" not in text and "987654" not in text


def test_changed_identity_has_stable_tool_error_without_sse_termination(tmp_path):
    with running_test_server("phase2", tmp_path / "replay.sqlite3",
                             certificate_dir=tmp_path) as url:
        text = anyio.run(exercise_phase2, url, "changed_identity")
    assert "CG_CONTACT_NOT_REGISTERED" in text
    assert "SSE stream ended without a response" not in text


def test_cross_contact_approval_keeps_url_elicitation_required(tmp_path):
    with running_test_server("phase2", tmp_path / "replay.sqlite3",
                             certificate_dir=tmp_path) as url:
        outcome = anyio.run(exercise_phase2, url, "cross_contact")
    assert outcome == "-32042 CG_APPROVAL_STILL_REQUIRED"
