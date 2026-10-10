import anyio
import pytest
from mcp.shared.exceptions import UrlElicitationRequiredError
from starlette.applications import Starlette
from starlette.testclient import TestClient

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
