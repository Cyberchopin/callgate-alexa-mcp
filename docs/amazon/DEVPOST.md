# Devpost submission draft

## Inspiration

Pressure scams turn speed into a weapon: a caller keeps the victim engaged while asking a digital assistant to move money or complete a purchase. CallGate explores a narrow question: can an assistant remain useful while moving authorization for high-risk actions outside the pressured conversation?

The intended audience is households supporting a scam-vulnerable family member who uses voice purchasing. `{{SOURCE_NEEDED: add one current, clickable public-authority statistic about impersonation-scam losses; do not submit this placeholder as a factual claim.}}`

## What it does

CallGate exposes simulated high-risk actions as tools on a self-hosted MCP server. A request without valid policy proof fails closed. For a simulated money transfer, the server can require URL-mode elicitation so that a saved-contact simulation reviews the exact request away from the assistant conversation. An approved request may be retried once; replay is rejected by SQLite-backed nonce consumption. A verification-code canary remains blocked even after approval.

## How we built it

The server uses Streamable HTTP and the pinned Python MCP SDK. The MCP adapter delegates policy, signature verification, contact selection, and replay decisions to the existing CallGate gateway instead of copying that logic. The URL-elicitation path follows the MCP 2025-11-25 error shape and completion notification. Local development uses an HTTPS review page and generated development certificates.

## Challenges

The SDK exposed two concrete integration gaps during development: a renamed FastMCP import disrupted an older quick-start path, and a client surfaced the server's URL-elicitation error as a generic MCP error that had to be reconstructed from its code and data. We preserved the original errors and workarounds in the friction log. Windows process startup also blocked some full-suite runs; that is recorded separately as a build-environment problem, not product friction.

## Accomplishments

- A real MCP client can discover and call the self-hosted tools on the isolated phase branches.
- Protected actions fail closed without policy proof.
- The verification-code canary cannot be approved into existence.
- Consumed proof nonces survive a server restart in SQLite.
- The repository includes an evidence ledger, reproducible synthetic evaluation, and an honest pre-existing-work report.

The final submission must not claim commitment-v2 binding, merchant-injection containment, cross-session resume, or a finished UI unless their blocked branches are completed and retested.

## What we learned

MCP is not only a transport for adding more agent capabilities. Its elicitation boundary can also keep sensitive review steps out of the model-mediated conversation. We also learned that a secure design needs two kinds of evidence: adversarial tests for authorization invariants and utility measurements that expose the cost of unavailable reviewers. A deny-all result is not a useful safety product.

## What's next

The next engineering gate is an approved, regression-clean commitment-v2 implementation that binds the operation type, normalized material parameters, stable simulated subject, and version inside the signed payload. After that, the plan is to finish the independent merchant server, injection-control experiment, accessible review UI, cross-session resume threat model, and red-team report. Real identity enrollment, payment integration, and production assistant support remain outside this prototype.

## What is simulated

The voice assistant, payments, orders, merchants, contacts, identities, approval credential, coercion scenarios, reviewer availability, and timing study are simulated. The project is not connected to a real assistant runtime, bank, payment network, SMS provider, or merchant. The MCP server, transport, client calls, policy-gateway delegation, URL-elicitation wire behavior, and SQLite replay store are executable software on their isolated branches.

## We will not claim

- Integration with a real voice-assistant runtime.
- Real payments, purchases, verification-code delivery, or identity proofing.
- That an LLM decides authorization.
- That the author-written simulation predicts fraud or human behavior.
- That URL elicitation is supported by every MCP client.
- That an unavailable or compromised saved contact is solved.
- That a blocked, reverted, skipped, or unrun test passed.

