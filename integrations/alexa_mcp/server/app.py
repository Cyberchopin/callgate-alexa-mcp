"""MCP transport adapter; authorization remains in CallGate's existing gate."""

import hashlib
import json
from pathlib import Path
from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver import Context
from mcp.server.mcpserver.exceptions import ToolError

from callgate.replay_store import SQLiteReplayStore
from callgate.verification import DemoVerificationGate
from callgate.workflow import ChallengeRateLimited


class PolicyProofRequired(ToolError):
    pass


class PolicyBlocked(ToolError):
    pass


PROOF_REJECTION_CODES = {
    "unknown issuer": "CG_PROOF_ISSUER_UNKNOWN",
    "invalid signature": "CG_PROOF_SIGNATURE_INVALID",
    "scope mismatch": "CG_PROOF_SCOPE_MISMATCH",
    "confirmation and policy approval required": "CG_POLICY_APPROVAL_REQUIRED",
    "credential not currently valid": "CG_PROOF_EXPIRED_OR_NOT_YET_VALID",
    "credential already consumed": "CG_PROOF_REPLAYED",
    "gate capacity reached": "CG_GATE_CAPACITY_REACHED",
    "replay storage unavailable": "CG_REPLAY_STORE_UNAVAILABLE",
}


APPROVAL_REJECTION_CODES = {
    "unknown saved identity; no fallback reviewer": "CG_CONTACT_NOT_REGISTERED",
    "self-approval credential origin rejected": "CG_SELF_APPROVAL_REJECTED",
    "confirmation capacity reached": "CG_APPROVAL_CAPACITY_REACHED",
}


def _proof_rejection(error: ValueError) -> str:
    return PROOF_REJECTION_CODES.get(str(error), "CG_PROOF_INVALID")


def _approval_rejection(error: ValueError) -> str:
    if isinstance(error, ChallengeRateLimited):
        return "CG_CHALLENGE_RATE_LIMITED"
    return APPROVAL_REJECTION_CODES.get(str(error), "CG_APPROVAL_REJECTED")


def operation_resource(tool_name: str, arguments: dict[str, Any]) -> str:
    payload = {"tool": tool_name, "arguments": arguments}
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=True, allow_nan=False).encode("ascii")
    return hashlib.sha256(raw).hexdigest()


class CapabilityGateway:
    """Thin adapter into DemoVerificationGate with a durable replay ledger."""

    def __init__(self, replay_db: str | Path, trusted_issuers=None, *, clock=None):
        kwargs = {"replay_store": SQLiteReplayStore(replay_db)}
        if clock is not None:
            kwargs["clock"] = clock
        self.gate = DemoVerificationGate(trusted_issuers or {}, **kwargs)

    def authorize(self, tool_name: str, arguments: dict[str, Any], *, session_id: str,
                  proof: dict[str, Any] | None):
        resource = operation_resource(tool_name, arguments)
        if tool_name == "share_verification_code":
            if proof is not None:
                try:
                    self.gate.execute(proof, session_id=session_id, resource=resource,
                                      human_confirmed=True, policy_allows=False)
                except ValueError:
                    pass
            raise PolicyBlocked("403 BLOCKED: canary tool is permanently disabled")
        if proof is None:
            raise PolicyProofRequired("403 POLICY_PROOF_REQUIRED")
        try:
            return self.gate.execute(proof, session_id=session_id, resource=resource,
                                     human_confirmed=True, policy_allows=True)
        except ValueError as error:
            raise PolicyBlocked(f"403 BLOCKED: {_proof_rejection(error)}") from None


def create_server(gateway: CapabilityGateway, approval_flow=None) -> MCPServer:
    server = MCPServer(name="callgate-simulated-voice-assistant", version="0.1.0",
        instructions="Simulated protected actions only; no real payment or Alexa+ connection.")

    @server.tool(description="Simulate sending money after CallGate authorization.")
    async def send_money(destination: str, amount_cents: int, session_id: str,
                         ctx: Context, claimed_identity: str | None = None,
                         proof: dict[str, Any] | None = None) -> dict[str, Any]:
        arguments = {"destination": destination, "amount_cents": amount_cents}
        if claimed_identity is not None:
            arguments["claimed_identity"] = claimed_identity
        if approval_flow is not None and proof is None:
            try:
                authorization = await approval_flow.authorize(arguments, session_id=session_id,
                    claimed_identity=claimed_identity, mcp_session=ctx.session)
            except ValueError as error:
                raise PolicyBlocked(f"403 BLOCKED: {_approval_rejection(error)}") from None
        else:
            authorization = gateway.authorize("send_money", arguments,
                                              session_id=session_id, proof=proof)
        return {**authorization, "tool": "send_money", "simulated": True}

    @server.tool(description="Simulate placing an order after CallGate authorization.")
    def place_order(merchant: str, cart: list[dict[str, Any]], total_amount_cents: int,
                    session_id: str, proof: dict[str, Any] | None = None) -> dict[str, Any]:
        arguments = {"merchant": merchant, "cart": cart,
                     "total_amount_cents": total_amount_cents}
        authorization = gateway.authorize("place_order", arguments,
                                          session_id=session_id, proof=proof)
        return {**authorization, "tool": "place_order", "simulated": True}

    @server.tool(description="Canary: always blocks attempts to share a verification code.")
    def share_verification_code(recipient: str, session_id: str,
                                proof: dict[str, Any] | None = None) -> dict[str, Any]:
        gateway.authorize("share_verification_code", {"recipient": recipient},
                          session_id=session_id, proof=proof)
        raise AssertionError("permanently blocked canary returned")

    return server
