import anyio
import pytest
from mcp.shared.exceptions import UrlElicitationRequiredError
from starlette.applications import Starlette
from starlette.testclient import TestClient

from callgate.workflow import ChallengeRateLimited
from integrations.alexa_mcp.phase2 import build_app


class Session:
    async def send_elicit_complete(self, _elicitation_id):
        pass


async def pending(flow):
    with pytest.raises(UrlElicitationRequiredError) as required:
        await flow.authorize({
            "destination": "server-wallet", "amount_cents": 4321,
            "claimed_identity": "saved-family",
        }, session_id="session-a", claimed_identity="saved-family", mcp_session=Session())
    return required.value.elicitations[0].elicitation_id


def test_assistant_page_has_calm_three_part_message_and_accessible_status(tmp_path):
    _, flow = build_app(tmp_path / "replay.sqlite3", "https://review.example", "family-token")
    with TestClient(Starlette(routes=flow.routes())) as client:
        response = client.get("/demo")
    assert response.status_code == 200
    assert "SIMULATED VOICE ASSISTANT" in response.text
    assert all(text in response.text for text in
               ("Why it paused", "What was protected", "What happens next", "aria-live"))
    assert "Reset demo" in response.text and "Proof panel" in response.text
    assert response.headers["Referrer-Policy"] == "no-referrer"


def test_contact_page_uses_server_request_not_query_parameters(tmp_path):
    _, flow = build_app(tmp_path / "replay.sqlite3", "https://review.example", "family-token")
    request_id = anyio.run(pending, flow)
    with TestClient(Starlette(routes=flow.routes())) as client:
        response = client.get(
            f"/approval/{request_id}?amount_cents=1&destination=forged-wallet&claimed_identity=attacker")
    assert response.status_code == 200
    assert all(text in response.text for text in ("4321", "server-wallet", "saved-family"))
    assert all(text not in response.text for text in ("forged-wallet", ">attacker<"))
    assert "Did you initiate this request?" in response.text
    assert "Parameter hash" in response.text and request_id not in response.text


def test_ui_assets_cover_keyboard_mobile_loading_and_error_states(tmp_path):
    _, flow = build_app(tmp_path / "replay.sqlite3", "https://review.example", "family-token")
    with TestClient(Starlette(routes=flow.routes())) as client:
        css = client.get("/ui/style.css").text
        script = client.get("/ui/demo.js").text
    assert ":focus-visible" in css
    assert "@media (max-width: 680px)" in css
    assert "min-height: 44px" in css
    assert "Submitting simulated contact decision" in script
    assert "The decision was not recorded" in script


def test_approval_origin_and_bearer_rules(tmp_path):
    _, flow = build_app(tmp_path / "replay.sqlite3", "https://review.example", "family-token")
    first = anyio.run(pending, flow)
    app = Starlette(routes=flow.routes())
    with TestClient(app) as client:
        cross_site_form = client.post(f"/approval/{first}", data={"approved": "true"},
            headers={"Origin": "https://attacker.example"})
        wrong_origin_bearer = client.post(f"/approval/{first}", json={"approved": True},
            headers={"Origin": "https://attacker.example",
                     "X-CallGate-Contact-Token": "family-token"})
        normal = client.post(f"/approval/{first}", json={"approved": True},
            headers={"Origin": "https://review.example",
                     "X-CallGate-Contact-Token": "family-token"})
    assert cross_site_form.status_code == 403
    assert wrong_origin_bearer.status_code == 403
    assert normal.status_code == 200


def test_non_browser_bearer_referrer_policy_and_token_redaction(tmp_path, caplog):
    _, flow = build_app(tmp_path / "replay.sqlite3", "https://review.example", "family-token")
    request_id = anyio.run(pending, flow)
    with TestClient(Starlette(routes=flow.routes())) as client:
        page = client.get(f"/approval/{request_id}")
        response = client.post(f"/approval/{request_id}", json={"approved": False},
            headers={"X-CallGate-Contact-Token": "family-token"})
        css = client.get("/ui/style.css")
    assert response.status_code == 200
    assert all(item.headers["Referrer-Policy"] == "no-referrer"
               for item in (page, response, css))
    assert "family-token" not in str(page.url)
    assert "family-token" not in page.text
    assert "family-token" not in caplog.text


def test_challenge_issuance_is_limited_per_subject(tmp_path):
    clock = [1000.0]
    _, flow = build_app(tmp_path / "replay.sqlite3", "https://review.example",
                        "family-token", clock=lambda: clock[0])

    async def issue(index):
        with pytest.raises(UrlElicitationRequiredError):
            await flow.authorize({
                "destination": f"wallet-{index}", "amount_cents": 1,
                "claimed_identity": "saved-family",
            }, session_id=f"session-{index}", claimed_identity="saved-family",
                mcp_session=Session())

    for index in range(5):
        anyio.run(issue, index)
    with pytest.raises(ChallengeRateLimited) as limited:
        anyio.run(issue, 5)
    assert limited.value.retry_after == 60
    clock[0] += 60
    anyio.run(issue, 6)
