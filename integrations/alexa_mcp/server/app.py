"""MCP transport adapter; authorization remains in CallGate's existing gate."""

import hashlib
import json
from pathlib import Path
from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from callgate.replay_store import SQLiteReplayStore
from callgate.verification import DemoVerificationGate


class PolicyProofRequired(ToolError):
    pass


class PolicyBlocked(ToolError):
    pass


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
            raise PolicyBlocked(f"403 BLOCKED: {error}") from None


def create_server(gateway: CapabilityGateway) -> MCPServer:
    server = MCPServer(name="callgate-simulated-voice-assistant", version="0.1.0",
        instructions="Simulated protected actions only; no real payment or Alexa+ connection.")

    @server.tool(description="Simulate sending money after CallGate authorization.")
    def send_money(destination: str, amount_cents: int, session_id: str,
                   proof: dict[str, Any] | None = None) -> dict[str, Any]:
        arguments = {"destination": destination, "amount_cents": amount_cents}
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
