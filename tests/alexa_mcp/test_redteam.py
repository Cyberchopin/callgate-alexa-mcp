"""Red-team characterisation tests for the isolated phase-2 prototype.

Tests that describe a known gap deliberately assert the observed insecure or
incomplete behavior so the gap cannot disappear from the report unnoticed.
"""
from concurrent.futures import ThreadPoolExecutor
import re

import anyio
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from mcp.shared.exceptions import UrlElicitationRequiredError
from starlette.applications import Starlette
from starlette.testclient import TestClient

from callgate.verification import issue_for_demo
from integrations.alexa_mcp.phase2 import build_app
from integrations.alexa_mcp.server import CapabilityGateway, operation_resource
from integrations.alexa_mcp.server.app import PolicyBlocked


class Session:
    def __init__(self):
        self.completed = []

    async def send_elicit_complete(self, elicitation_id):
        self.completed.append(elicitation_id)


async def create_pending(flow, *, arguments=None, session_id="session-a"):
    arguments = arguments or {
        "destination": "simulated-wallet",
        "amount_cents": 5000,
        "claimed_identity": "saved-family",
    }
    session = Session()
    with pytest.raises(UrlElicitationRequiredError) as required:
        await flow.authorize(arguments, session_id=session_id,
                             claimed_identity="saved-family", mcp_session=session)
    return required.value.elicitations[0], session


def test_cross_tool_replay_and_parameter_mutation_are_rejected(tmp_path):
    key = Ed25519PrivateKey.generate()
    send = {"destination": "simulated-wallet", "amount_cents": 5000}
    proof = issue_for_demo(key, issuer="issuer", session_id="session-a",
                           resource=operation_resource("send_money", send), now=1000)
    gateway = CapabilityGateway(tmp_path / "replay.sqlite3", {"issuer": key.public_key()},
                                clock=lambda: 1001)
    with pytest.raises(PolicyBlocked, match="scope mismatch"):
        gateway.authorize("place_order", {
            "merchant": "fictional-shop", "cart": [{"sku": "one", "quantity": 1}],
            "total_amount_cents": 5000,
        }, session_id="session-a", proof=proof.model_dump())
    with pytest.raises(PolicyBlocked, match="scope mismatch"):
        gateway.authorize("send_money", {**send, "amount_cents": 5001},
                          session_id="session-a", proof=proof.model_dump())


def test_concurrent_double_spend_allows_exactly_one_use(tmp_path):
    key = Ed25519PrivateKey.generate()
    arguments = {"destination": "simulated-wallet", "amount_cents": 5000}
    proof = issue_for_demo(key, issuer="issuer", session_id="session-a",
                           resource=operation_resource("send_money", arguments), now=1000)
    gateway = CapabilityGateway(tmp_path / "replay.sqlite3", {"issuer": key.public_key()},
                                clock=lambda: 1001)

    def attempt():
        try:
            gateway.authorize("send_money", arguments, session_id="session-a",
                              proof=proof.model_dump())
            return "allowed"
        except PolicyBlocked:
            return "blocked"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: attempt(), range(2)))
    assert sorted(outcomes) == ["allowed", "blocked"]


def test_approval_page_ignores_query_forgery_and_get_does_not_mutate(tmp_path):
    _, flow = build_app(tmp_path / "replay.sqlite3", "https://review.example",
                        "family-token")
    elicitation, _ = anyio.run(create_pending, flow)
    identifier = elicitation.elicitation_id
    app = Starlette(routes=flow.routes())
    with TestClient(app) as client:
        response = client.get(
            f"/approval/{identifier}?amount_cents=1&destination=attacker-wallet&approved=true")
    assert response.status_code == 200
    assert "5000" in response.text and "simulated-wallet" in response.text
    assert "attacker-wallet" not in response.text
    assert identifier in flow.pending


def test_csrf_requests_without_contact_token_are_rejected_but_origin_is_not_checked(tmp_path):
    _, flow = build_app(tmp_path / "replay.sqlite3", "https://review.example",
                        "family-token")
    first, _ = anyio.run(create_pending, flow)
    app = Starlette(routes=flow.routes())
    with TestClient(app) as client:
        missing = client.post(f"/approval/{first.elicitation_id}", json={"approved": True})
        form = client.post(f"/approval/{first.elicitation_id}", data={"approved": "true"},
                           headers={"Origin": "https://attacker.example"})
        async def create_second():
            return await create_pending(flow, arguments={
                "destination": "other-wallet", "amount_cents": 5000,
                "claimed_identity": "saved-family",
            })
        second, _ = anyio.run(create_second)
        accepted_cross_origin = client.post(
            f"/approval/{second.elicitation_id}", json={"approved": True},
            headers={"Origin": "https://attacker.example",
                     "X-CallGate-Contact-Token": "family-token"})
    assert missing.status_code == 403
    assert form.status_code == 403
    assert accepted_cross_origin.status_code == 200  # Documented bearer-token/origin gap.


def test_elicitation_url_is_opaque_one_time_and_page_lacks_referrer_policy(tmp_path):
    _, flow = build_app(tmp_path / "replay.sqlite3", "https://review.example",
                        "family-token")
    elicitation, session = anyio.run(create_pending, flow)
    assert re.fullmatch(r"https://review\.example/approval/[a-f0-9]{32}", elicitation.url)
    assert all(secret not in elicitation.url for secret in
               ("5000", "simulated-wallet", "saved-family", "family-token"))
    app = Starlette(routes=flow.routes())
    with TestClient(app) as client:
        page = client.get(f"/approval/{elicitation.elicitation_id}")
        approved = client.post(f"/approval/{elicitation.elicitation_id}",
                               json={"approved": True},
                               headers={"X-CallGate-Contact-Token": "family-token"})
        reused = client.get(f"/approval/{elicitation.elicitation_id}")
    assert page.headers.get("Referrer-Policy") is None  # Documented hardening gap.
    assert approved.status_code == 200 and reused.status_code == 410
    assert session.completed == [elicitation.elicitation_id]


def test_challenge_issuance_has_capacity_cap_but_no_per_subject_rate_limit(tmp_path):
    _, flow = build_app(tmp_path / "replay.sqlite3", "https://review.example",
                        "family-token")

    async def fill():
        for index in range(1000):
            with pytest.raises(UrlElicitationRequiredError):
                await flow.authorize({
                    "destination": f"wallet-{index}", "amount_cents": 1,
                    "claimed_identity": "saved-family",
                }, session_id="same-subject-session", claimed_identity="saved-family",
                    mcp_session=Session())
        with pytest.raises(ValueError, match="capacity reached"):
            await flow.authorize({
                "destination": "one-too-many", "amount_cents": 1,
                "claimed_identity": "saved-family",
            }, session_id="same-subject-session", claimed_identity="saved-family",
                mcp_session=Session())

    anyio.run(fill)


def test_gateway_emits_no_sensitive_python_log_text(caplog, tmp_path):
    gateway = CapabilityGateway(tmp_path / "replay.sqlite3")
    with pytest.raises(Exception, match="POLICY_PROOF_REQUIRED"):
        gateway.authorize("send_money", {
            "destination": "sensitive-destination", "amount_cents": 987654,
        }, session_id="session-a", proof=None)
    assert "sensitive-destination" not in caplog.text
    assert "987654" not in caplog.text
