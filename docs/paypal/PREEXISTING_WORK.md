# PayPal AI Hackathon — what existed before and what is new

Hackathon build window: October 1 – November 12, 2026. The rules allow existing projects that make meaningful progress during the event.

## Pre-existing (CallGate, before this work)

Base commit `00bdafb` on `main`: the CallGate voice-risk policy, signed decision receipts, reviewer confirmation protocol, SQLite replay store, the Alexa+ MCP gateway and their tests. Nothing in that code talks to PayPal or reads purchase agreements.

Reused unchanged: `callgate/receipt.py` (`canonical` JSON encoding used for signatures and hashes).

## New during the hackathon (branch `paypal/checkout`, from October 25, 2026)

- `integrations/paypal_checkout/` — terms reader (rules + grounded model + referee), order comparison and fingerprint, signed approval bound to an order version, SQLite checkout ledger with idempotency and webhook dedupe, PayPal Orders v2 client, offline PayPal stand-in, seller and payer web pages.
- `tests/paypal_checkout/` — 44 tests.
- `integrations/paypal_checkout/agent_gateway.py`, `scripts/paypal_agent_demo.py` — MCP gateway for AI sales agents.
- `integrations/paypal_checkout/shipping.py` — packing checklist, PayPal tracking, dispute evidence.
- `render.yaml`, `docs/paypal/` — hosted demo blueprint and submission materials.
- `evaluation_paypal/` — CheckoutBench-lite scenarios and runner.

Commit history on the branch is the authoritative record.
