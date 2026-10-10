"""Deterministic vulnerable test double; never an authorization authority."""
from integrations.alexa_mcp.server.app import PolicyBlocked, PolicyProofRequired


class VulnerableDemoAgent:
    """Intentionally obeys injected fixture text for a controlled comparison."""

    def attempted_actions(self, description: str):
        if "TEST INJECTION:" not in description:
            return []
        return [
            ("send_money", {"destination": "injected-wallet", "amount_cents": 500000}),
            ("share_verification_code", {"recipient": "injected-recipient"}),
        ]

    def run(self, description: str, *, gateway=None, session_id="agent-fixture"):
        attempts = self.attempted_actions(description)
        executed = 0
        outcomes = []
        for tool, arguments in attempts:
            if gateway is None:
                executed += 1
                outcomes.append({"tool": tool, "outcome": "unguarded_simulated_execution"})
                continue
            try:
                gateway.authorize(tool, arguments, session_id=session_id, proof=None)
            except (PolicyProofRequired, PolicyBlocked) as error:
                outcomes.append({"tool": tool, "outcome": "blocked", "reason": str(error)})
        return {"attempted": len(attempts), "executed": executed, "outcomes": outcomes,
                "test_double": True, "llm_used": False}
