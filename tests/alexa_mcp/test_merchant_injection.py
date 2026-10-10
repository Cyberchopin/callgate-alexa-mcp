import anyio
import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from mcp.shared.exceptions import UrlElicitationRequiredError

from callgate.confirmation import ReviewerDecision, decision_bytes
from integrations.alexa_mcp.merchant import MerchantStore, PRODUCTS
from integrations.alexa_mcp.phase2 import build_app
from integrations.alexa_mcp.server.app import PolicyBlocked
from integrations.alexa_mcp.vulnerable_demo_agent import VulnerableDemoAgent


class Session:
    async def send_elicit_complete(self, _elicitation_id):
        pass


def approve_pending(flow, elicitation_id):
    item = flow.pending[elicitation_id]
    key = flow.reviewer_keys[item.request.reviewer]
    decision = ReviewerDecision(request=item.request, approved=True,
        signature=key.sign(decision_bytes(item.request, True)).hex())
    credential = flow.coordinator.decide(decision)
    flow.pending.pop(elicitation_id)
    flow.approved[flow._key(item.arguments)] = credential
    return credential


def test_simulated_merchant_search_cart_checkout_approval_and_replay(tmp_path):
    store = MerchantStore()
    products = store.search_products("lamp")
    assert {item["id"] for item in products} == {"lamp-safe", "lamp-injected"}
    product = store.get_product("lamp-injected")
    cart = store.add_to_cart("shopping-session", product["id"])
    assert cart["total_amount_cents"] == 5000

    _, flow = build_app(tmp_path / "replay.sqlite3", "https://review.example",
                        "family-contact")
    arguments = {"destination": "fictional-home-store", "amount_cents": 5000,
                 "claimed_identity": "saved-family"}

    async def request():
        await flow.authorize(arguments, session_id="shopping-session",
                             claimed_identity="saved-family", mcp_session=Session())

    with pytest.raises(UrlElicitationRequiredError) as required:
        anyio.run(request)
    credential = approve_pending(flow, required.value.elicitations[0].elicitation_id)

    async def retry():
        return await flow.authorize(arguments, session_id="shopping-session",
                                    claimed_identity="saved-family", mcp_session=Session())

    result = anyio.run(retry)
    assert result["status"] == "simulated_action_completed"
    with pytest.raises(PolicyBlocked, match="already consumed"):
        flow.gateway.authorize("send_money", arguments, session_id="shopping-session",
                               proof=credential.model_dump())


def test_injected_description_is_blocked_by_gateway_and_canary(tmp_path):
    description = PRODUCTS["lamp-injected"]["description"]
    agent = VulnerableDemoAgent()
    unguarded = agent.run(description)
    protected = agent.run(description, gateway=build_app(
        tmp_path / "replay.sqlite3", "https://review.example", "family-contact")[1].gateway)
    assert (unguarded["executed"], unguarded["attempted"]) == (2, 2)
    assert (protected["executed"], protected["attempted"]) == (0, 2)
    assert {item["tool"] for item in protected["outcomes"]} == {
        "send_money", "share_verification_code"}
    assert all(item["outcome"] == "blocked" for item in protected["outcomes"])


def test_demo_agent_is_deterministic_and_llm_free():
    agent = VulnerableDemoAgent()
    first = agent.run(PRODUCTS["lamp-injected"]["description"])
    second = agent.run(PRODUCTS["lamp-injected"]["description"])
    assert first == second
    assert first["test_double"] is True and first["llm_used"] is False
