"""URL-elicitation approval adapter for the simulated send_money tool."""

import html
import secrets
from dataclasses import dataclass
from typing import Any

from mcp.shared.exceptions import UrlElicitationRequiredError
from mcp.types import ElicitRequestURLParams
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse
from starlette.routing import Route

from callgate.confirmation import ConfirmationCoordinator, ReviewerDecision, decision_bytes

from .app import CapabilityGateway, operation_resource


@dataclass
class PendingApproval:
    request: Any
    arguments: dict[str, Any]
    session_id: str
    mcp_session: Any


class ApprovalFlow:
    def __init__(self, gateway: CapabilityGateway, coordinator: ConfirmationCoordinator,
                 reviewer_keys: dict[str, Any], contact_tokens: dict[str, str], *,
                 approval_base_url: str, subject: str):
        if not approval_base_url.startswith("https://"):
            raise ValueError("approval URL must use HTTPS")
        self.gateway = gateway
        self.coordinator = coordinator
        self.reviewer_keys = dict(reviewer_keys)
        self.contact_tokens = dict(contact_tokens)
        self.approval_base_url = approval_base_url.rstrip("/")
        self.subject = subject
        self.pending: dict[str, PendingApproval] = {}
        self.approved: dict[str, Any] = {}

    def _key(self, arguments):
        return f"{self.subject}:{operation_resource('send_money', arguments, self.subject)}"

    async def authorize(self, arguments, *, session_id, claimed_identity, mcp_session):
        key = self._key(arguments)
        credential = self.approved.pop(key, None)
        if credential is not None:
            return self.gateway.authorize("send_money", arguments, session_id=session_id,
                                          proof=credential.model_dump())
        confirmation = self.coordinator.create_v2(session_id=session_id,
            operation_type="send_money", parameters=arguments, subject=self.subject,
            claimed_identity=claimed_identity)
        elicitation_id = secrets.token_hex(16)
        self.pending[elicitation_id] = PendingApproval(
            confirmation, dict(arguments), session_id, mcp_session)
        raise UrlElicitationRequiredError([ElicitRequestURLParams(
            message="A saved contact must review this simulated transfer.",
            url=f"{self.approval_base_url}/approval/{elicitation_id}",
            elicitationId=elicitation_id)])

    async def view(self, request: Request):
        item = self.pending.get(request.path_params["elicitation_id"])
        if item is None or self.coordinator.expired(item.request):
            return JSONResponse({"error": "approval unavailable"}, status_code=410)
        operation = item.arguments
        body = ("<h1>Simulated contact review</h1>"
                f"<p>Amount: {int(operation['amount_cents'])} cents</p>"
                f"<p>Destination: {html.escape(operation['destination'])}</p>"
                f"<p>Requested identity: {html.escape(item.request.claimed_identity or '')}</p>"
                "<p>No real payment will occur.</p>")
        return HTMLResponse(body)

    async def decide(self, request: Request):
        elicitation_id = request.path_params["elicitation_id"]
        item = self.pending.get(elicitation_id)
        if item is None or self.coordinator.expired(item.request):
            self.pending.pop(elicitation_id, None)
            return JSONResponse({"error": "approval unavailable"}, status_code=410)
        reviewer = item.request.reviewer
        supplied = request.headers.get("x-callgate-contact-token", "")
        if not secrets.compare_digest(supplied, self.contact_tokens.get(reviewer, "")):
            return JSONResponse({"error": "wrong saved contact"}, status_code=403)
        approved = (await request.json()).get("approved") is True
        reviewer_key = self.reviewer_keys[reviewer]
        decision = ReviewerDecision(request=item.request, approved=approved,
            signature=reviewer_key.sign(decision_bytes(item.request, approved)).hex())
        credential = self.coordinator.decide(decision)
        self.pending.pop(elicitation_id, None)
        if credential is None:
            return JSONResponse({"status": "denied"})
        self.approved[self._key(item.arguments)] = credential
        await item.mcp_session.send_elicit_complete(elicitation_id)
        return JSONResponse({"status": "approved", "simulated": True})

    def routes(self):
        return [
            Route("/approval/{elicitation_id}", self.view, methods=["GET"]),
            Route("/approval/{elicitation_id}", self.decide, methods=["POST"]),
        ]


def add_approval_routes(app, flow: ApprovalFlow):
    app.routes.extend(flow.routes())
    return app
