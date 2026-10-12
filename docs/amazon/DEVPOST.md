# Devpost submission draft

## Inspiration

**Lies in the Loop, at home.** A shopping agent can be shown poisoned product text while a scammer keeps the shopper under pressure on the phone. The agent may render a reassuring confirmation that describes a small purchase even though the protected tool request contains a different amount, destination, or cart. CallGate asks whether authorization can remain trustworthy when the conversational context is not.

The intended audience is households supporting a scam-vulnerable family member who uses voice purchasing. `{{SOURCE_NEEDED: add one current, clickable public-authority statistic; do not convert this placeholder into a factual claim without a source.}}`

## What it does

CallGate exposes simulated high-risk actions through a self-hosted MCP server. Requests without valid policy proof fail closed. For a simulated transfer, URL-mode elicitation moves review to a saved-contact simulation outside the assistant conversation. That page fetches the true amount, destination, cart, and requesting subject from server state rather than trusting display text or URL parameters. A verification-code canary remains blocked even after approval.

ApprovalBench compares CallGate with author-written reference implementations of common approval designs, including agent-authored confirmation, relayed codes, same-principal approval, and approval not bound to parameters. Submission metrics must be inserted only from `CLAIMS.md`: `{{CLAIMS:APPROVALBENCH_HEADLINE}}`.

## How we built it

The server uses Streamable HTTP and a pinned Python MCP SDK. The adapter delegates policy, signature verification, contact selection, and replay decisions to the existing CallGate gateway instead of copying them. The review path uses the MCP 2025-11-25 URL-elicitation error and completion notification. A separate simulated merchant server supplies a poisoned product fixture, and a deterministic deliberately vulnerable test double follows it so the authorization boundary can be tested without pretending to evaluate a production assistant.

## Challenges

The SDK exposed concrete integration gaps: a renamed FastMCP import disrupted an older quick-start path, and a client surfaced a URL-elicitation error as a generic MCP error that had to be reconstructed from its code and data. The original errors and workarounds remain in the friction log. Environment-only process failures are recorded separately and are not presented as product friction.

The hardest product question was fairness: a deny-all system would look safe but be useless. ApprovalBench therefore records legitimate completion and delay alongside attack success, uses fixed assumptions and a fixed seed, and labels every result as an author-written simulation rather than human research.

## Accomplishments

- A self-hosted MCP path delegates protected actions to the existing gateway.
- Missing proof fails closed, and the verification-code canary has no approval path.
- The demonstration distinguishes what the agent says from what the server will execute.
- Reference designs and attacks are reproducible from generated JSON rather than hand-filled charts.
- The repository preserves blocked tests, friction, limitations, and pre-existing work instead of hiding them.

Final quantitative claims: `{{CLAIMS:APPROVALBENCH_SECURITY}}`; `{{CLAIMS:APPROVALBENCH_UTILITY}}`; `{{CLAIMS:INJECTION_COMPARISON}}`.

## What we learned

Prompt-injection defenses and authorization are different jobs. A model can remain vulnerable to poisoned context while a deterministic gateway still refuses to act. We also learned that reviewer independence is not enough by itself: the review must show server-held parameters, bind the permitted operation, and consume approval once.

## What's next

Production work would require real identity enrollment, secure reviewer recovery, audited payment integrations, tenant isolation, privacy review, independent user research, and validation in the intended assistant client. The prototype deliberately stops before those claims.

## What is simulated

The voice assistant, phone pressure, payments, orders, merchants, contacts, identities, approval credentials, reviewer availability, and timing study are simulated. The vulnerable agent is a deterministic test double, not a real assistant. No LLM participates in authorization. The project is not connected to a bank, payment network, SMS provider, real merchant, or production assistant runtime.

## We will not claim

- That CallGate makes an agent immune to prompt injection.
- Discovery of a new vulnerability class or priority over prior Lies-in-the-Loop and tool-poisoning work.
- Integration with a production voice-assistant runtime.
- Real payments, purchases, code delivery, identity proofing, or independently enrolled contacts.
- Human-study or population-level outcomes from an author-written simulation.
- That URL elicitation is supported by every MCP client.
- That a compromised or unavailable saved contact is solved.
- That a blocked, reverted, skipped, or unrun test passed.

