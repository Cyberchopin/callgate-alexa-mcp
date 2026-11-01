# YouTube upload copy

## Title

CallGate Checkout — Agentic PayPal Commerce Without Giving the Agent Authority

## Description

CallGate Checkout connects a buyer–seller chat to the PayPal order and the parcel that follows.

AI reads the negotiation and may draft an order through an MCP gateway. Deterministic code checks every amount against the exact words the seller confirmed, binds the buyer's approval to one order fingerprint and maximum amount, re-checks the PayPal ship-to address before capture, and preserves packing, tracking, provenance, and signed evidence afterwards.

This demo uses the PayPal sandbox and test accounts. It does not move real money and is not a production payment processor.

Source code and setup:
https://github.com/Cyberchopin/callgate-alexa-mcp

Technical deep dive:
https://github.com/Cyberchopin/callgate-alexa-mcp/tree/main/integrations/paypal_checkout

PayPal sandbox evidence:
https://github.com/Cyberchopin/callgate-alexa-mcp/blob/main/docs/paypal/sandbox-run.json

Built for the PayPal AI Hackathon 2026.

## Chapters

```text
0:00 The gap between chat and payment
0:16 Grounding the agreed terms
0:40 Risk flags and provenance
0:55 AI drafts through the MCP gateway
1:18 Buyer review and PayPal sandbox approval
1:48 Changed-order and destination gates
2:10 Idempotent capture, packing, and tracking
2:38 Signed evidence chain
```

Adjust chapter timestamps after the final edit. Do not publish timestamps that point to the wrong scene.

## Tags

```text
PayPal, PayPal Developer, PayPal Sandbox, AI agents, agentic commerce, MCP, Model Context Protocol, payment safety, FastAPI, Python, hackathon
```

## Thumbnail

Upload `docs/paypal/media/thumbnail.png`.
