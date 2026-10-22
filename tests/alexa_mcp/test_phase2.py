from pathlib import Path

import anyio
import httpx2
import pytest
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.shared.exceptions import MCPError, UrlElicitationRequiredError
from mcp.types import ElicitResult

from integrations.alexa_mcp.phase2 import (
    build_app,
    ensure_development_certificate,
    temporary_development_certificate,
)
from scripts.mcp_test_process import running_test_server


async def accept_elicitation(context, params):
    return ElicitResult(action="accept")


def test_development_private_key_is_removed_after_context(tmp_path):
    with temporary_development_certificate(tmp_path) as directory:
        root = Path(directory)
        certificate, private_key = ensure_development_certificate(root)
        assert certificate.is_file()
        assert private_key.is_file()
    assert not root.exists()


def test_development_certificate_uses_browser_compatible_key(tmp_path):
    # Chrome and Windows Schannel reject Ed25519 TLS certificates.
    from cryptography import x509
    from cryptography.hazmat.primitives.asymmetric import ec

    certificate, _ = ensure_development_certificate(tmp_path)
    public_key = x509.load_pem_x509_certificate(certificate.read_bytes()).public_key()
    assert isinstance(public_key, ec.EllipticCurvePublicKey)
    assert public_key.curve.name == "secp256r1"


async def require_url(session, arguments):
    with pytest.raises(MCPError) as error:
        await session.call_tool("send_money", arguments)
    assert error.value.code == -32042
    return UrlElicitationRequiredError.from_error(error.value.error)


async def exercise_happy_path(base_url):
    messages = []

    async def collect(message):
        messages.append(message)

    arguments = {"destination": "simulated-wallet", "amount_cents": 5000,
                 "session_id": "session-a", "claimed_identity": "saved-family"}
    async with httpx2.AsyncClient(verify=False) as http:
        async with streamable_http_client(base_url + "/mcp", http_client=http) as streams:
            async with ClientSession(streams[0], streams[1],
                    elicitation_callback=accept_elicitation, message_handler=collect) as session:
                initialized = await session.initialize()
                assert initialized.protocol_version >= "2025-11-25"
                required = await require_url(session, arguments)
                elicitation = required.elicitations[0]
                assert elicitation.url.startswith(base_url + "/approval/")
                assert "5000" not in elicitation.url
                assert "simulated-wallet" not in elicitation.url
                page = await http.get(elicitation.url)
                assert page.status_code == 200
                assert all(value in page.text for value in
                           ("5000", "simulated-wallet", "saved-family"))
                wrong = await http.post(elicitation.url, json={"approved": True},
                    headers={"X-CallGate-Contact-Token": "wrong-contact"})
                assert wrong.status_code == 403
                approved = await http.post(elicitation.url, json={"approved": True},
                    headers={"X-CallGate-Contact-Token": "family-token"})
                assert approved.status_code == 200
                await anyio.sleep(0.05)
                assert any("ElicitComplete" in type(getattr(message, "root", message)).__name__
                           for message in messages)
                completed = await session.call_tool("send_money", arguments)
                assert completed.is_error is False
                await require_url(session, arguments)
                return session, http, arguments


def test_url_elicitation_approval_notification_and_one_time_retry(tmp_path):
    with running_test_server("phase2", tmp_path / "replay.sqlite3",
                             certificate_dir=tmp_path) as base_url:
        anyio.run(exercise_happy_path, base_url)


async def authorize_then_mutate(base_url, mutation):
    original = {"destination": "simulated-wallet", "amount_cents": 5000,
                "session_id": "session-a", "claimed_identity": "saved-family"}
    async with httpx2.AsyncClient(verify=False) as http:
        async with streamable_http_client(base_url + "/mcp", http_client=http) as streams:
            async with ClientSession(streams[0], streams[1],
                    elicitation_callback=accept_elicitation) as session:
                await session.initialize()
                required = await require_url(session, original)
                await http.post(required.elicitations[0].url, json={"approved": True},
                    headers={"X-CallGate-Contact-Token": "family-token"})
                try:
                    result = await session.call_tool("send_money", {**original, **mutation})
                    assert result.is_error is True
                except MCPError as error:
                    if "claimed_identity" in mutation:
                        raise AssertionError("expected a stable tool error, not MCP transport failure") from error
                    else:
                        assert error.code == -32042


@pytest.mark.parametrize("mutation", [
    {"amount_cents": 5001},
    {"destination": "other-wallet"},
    {"claimed_identity": "other-contact"},
    {"session_id": "other-session"},
])
def test_changed_scope_is_rejected(tmp_path, mutation):
    with running_test_server("phase2", tmp_path / "replay.sqlite3",
                             certificate_dir=tmp_path) as base_url:
        anyio.run(authorize_then_mutate, base_url, mutation)


def test_expired_cross_contact_and_self_approval_are_rejected(tmp_path):
    clock = [1000]
    _, flow = build_app(tmp_path / "expiry/replay.sqlite3", "https://127.0.0.1",
                        "family-token", clock=lambda: clock[0])
    with pytest.raises(UrlElicitationRequiredError) as required:
        class Session:
            async def send_elicit_complete(self, elicitation_id):
                pass
        async def create_expiring():
            await flow.authorize({"destination": "wallet", "amount_cents": 1,
                "claimed_identity": "saved-family"}, session_id="s",
                claimed_identity="saved-family", mcp_session=Session())
        anyio.run(create_expiring)
    elicitation_id = required.value.elicitations[0].elicitation_id
    clock[0] = 1120
    assert flow.coordinator.expired(flow.pending[elicitation_id].request)

    _, flow = build_app(tmp_path / "self/replay.sqlite3", "https://127.0.0.1",
                        "family-token", initiator_origin="participant-device",
                        contact_origin="participant-device")
    async def attempt_self_approval():
        await flow.authorize({"destination": "wallet", "amount_cents": 1,
            "claimed_identity": "saved-family"}, session_id="s",
            claimed_identity="saved-family", mcp_session=None)
    with pytest.raises(ValueError, match="self-approval"):
        anyio.run(attempt_self_approval)
