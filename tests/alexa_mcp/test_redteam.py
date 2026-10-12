"""Red-team characterisation tests for the isolated phase-2 prototype.

Tests that describe a known gap deliberately assert the observed insecure or
incomplete behavior so the gap cannot disappear from the report unnoticed.
"""
from concurrent.futures import ThreadPoolExecutor
import re

import anyio
import httpx
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from mcp.shared.exceptions import UrlElicitationRequiredError
from starlette.applications import Starlette

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
    async def get_page():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                    base_url="https://review.example") as client:
            return await client.get(
                f"/approval/{identifier}?amount_cents=1&destination=attacker-wallet&approved=true")
    response = anyio.run(get_page)
    assert response.status_code == 200
    assert "5000" in response.text and "simulated-wallet" in response.text
    assert "attacker-wallet" not in response.text
    assert identifier in flow.pending


def test_csrf_and_cross_origin_bearer_requests_are_rejected(tmp_path):
    _, flow = build_app(tmp_path / "replay.sqlite3", "https://review.example",
                        "family-token")
    first, _ = anyio.run(create_pending, flow)
    app = Starlette(routes=flow.routes())
    async def exercise():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                    base_url="https://review.example") as client:
            missing = await client.post(f"/approval/{first.elicitation_id}",
                                        json={"approved": True})
            form = await client.post(f"/approval/{first.elicitation_id}",
                                     data={"approved": "true"},
                                     headers={"Origin": "https://attacker.example"})
            second, _ = await create_pending(flow, arguments={
                "destination": "other-wallet", "amount_cents": 5000,
                "claimed_identity": "saved-family",
            })
            cross_origin = await client.post(
                f"/approval/{second.elicitation_id}", json={"approved": True},
                headers={"Origin": "https://attacker.example",
                         "X-CallGate-Contact-Token": "family-token"})
            return missing, form, cross_origin
    missing, form, cross_origin = anyio.run(exercise)
    assert missing.status_code == 403
    assert form.status_code == 403
    assert cross_origin.status_code == 403


def test_elicitation_url_is_opaque_one_time_and_has_referrer_policy(tmp_path):
    _, flow = build_app(tmp_path / "replay.sqlite3", "https://review.example",
                        "family-token")
    elicitation, session = anyio.run(create_pending, flow)
    assert re.fullmatch(r"https://review\.example/approval/[a-f0-9]{32}", elicitation.url)
    assert all(secret not in elicitation.url for secret in
               ("5000", "simulated-wallet", "saved-family", "family-token"))
    app = Starlette(routes=flow.routes())
    async def exercise():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                    base_url="https://review.example") as client:
            page = await client.get(f"/approval/{elicitation.elicitation_id}")
            approved = await client.post(f"/approval/{elicitation.elicitation_id}",
                                         json={"approved": True},
                                         headers={"X-CallGate-Contact-Token": "family-token"})
            reused = await client.get(f"/approval/{elicitation.elicitation_id}")
            return page, approved, reused
    page, approved, reused = anyio.run(exercise)
    assert page.headers.get("Referrer-Policy") == "no-referrer"
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
