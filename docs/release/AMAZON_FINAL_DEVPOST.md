# Final Devpost text — Alexa+ track

Paste-ready. Text in **[OWNER: …]** must be filled or confirmed by the owner
before submitting. All numbers come from committed evidence files named inline.
Everything else was observed on 2026-10-21.

---

## Project name

CallGate — proof before a simulated voice-assistant payment

## Tagline (≤ 200 chars)

A self-hosted MCP gateway that pauses an agent's purchases and transfers until a separately registered contact approves the exact request, outside the poisoned conversation.

## Track and mini challenges

- Primary track: **Alexa+** (self-hosted MCP server, MCP 2025-11-25, Streamable HTTP; simulated assistant experience).
- Mini challenges: **None.** **[OWNER: enter Open Source only if you have an additional public contribution URL made during the window. Do not enter AWS Builder; no AWS service or Kiro was used.]**

## Inspiration

A voice shopping agent reads text it doesn't control, such as product descriptions,
reviews, and merchant notes. One poisoned description can tell the agent to send
money or read out a verification code. A scammer on the phone can add pressure
at the same moment. If the agent also writes the confirmation the shopper sees,
it can show a reassuring "$50 lamp" while the real tool call sends $5,000
elsewhere. We wanted a boundary where the conversation can be compromised and
money still doesn't move.

The people this matters most for are older adults and the families who support
them. The FTC reports that adults 60 and over reported fraud losses rising from
about $600 million in 2020 to $2.4 billion in 2024 ([FTC, Dec 1 2025](https://www.ftc.gov/news-events/news/press-releases/2025/12/ftc-issues-annual-report-congress-agencys-actions-protect-older-adults)).
Voice purchasing makes it easier for those losses to happen inside a single
conversation.

## What it does

CallGate puts protected actions behind a self-hosted MCP gateway. You can watch
it work in a live, simulated voice-assistant page. The page shows each MCP
connection, product cards from the merchant, a "paused" card linking to the
contact's review, and the final outcome.

- **Shopping stays useful.** A separate simulated merchant MCP server provides `search_products`, `get_product`, `add_to_cart`, and `view_cart`. Their output is treated as untrusted.
- **Protected actions fail closed.** `send_money` and `place_order` never run on the agent's say-so. Without proof they return a stable refusal (`403 POLICY_PROOF_REQUIRED`) or pause for review.
- **Review happens outside the agent.** For a transfer, the gateway answers with MCP **URL-mode elicitation** (JSON-RPC `-32042`). The review link carries only a random ID. The saved contact's page loads the true amount, destination, and requesting identity from server-held state, never from URL parameters or agent text.
- **Approval is exact and one-time.** After approval the server sends `notifications/elicitation/complete` to the initiating session. The exact retry executes once, and the proof stays server-side, out of the model's context. The same request again needs a new review. Changing the amount, destination, identity, or session also needs a new review.
- **Some things are never approvable.** `share_verification_code` is a canary that is permanently blocked, even with a valid proof.

## How we built it

- **MCP Python SDK 2.3.0** (`MCPServer`, Streamable HTTP) for two independent servers: the merchant and the CallGate gateway. A real `ClientSession` drives both in tests and in the demo client.
- **MCP 2025-11-25 URL-mode elicitation:** the SDK's `UrlElicitationRequiredError`, plus `send_elicit_complete` for the completion notification.
- **The CallGate core:** the MCP adapter is thin. It delegates signature checks, policy, contact selection, and replay decisions to CallGate's existing `DemoVerificationGate`, `ConfirmationCoordinator`, and `ContactDirectory` instead of copying them.
- **Ed25519** signatures for issuer and reviewer decisions. Proofs bind a SHA-256 hash of the exact tool and arguments.
- **SQLite** replay ledger, so a consumed proof stays consumed after a server restart.
- **Local HTTPS** with a short-lived, self-signed ECDSA certificate for the review page. It is deleted on exit.
- A deterministic, deliberately vulnerable **test double** for the injection comparison. It uses no LLM, and no LLM takes part in authorization.
- A **live simulated-assistant page** with a small Starlette backend. The backend is itself a real MCP client of both servers and checks the gateway's certificate. The no-build HTML/CSS/JS frontend builds every element with `textContent`. It can optionally read replies aloud with the browser's local speech synthesis.

## What we built during the submission period

The Git history starts 2026-09-02, after the 2026-08-31 start of the submission
period. The CallGate voice-risk research prototype (risk policy, signed
receipts, reviewer flow) was built in September. Everything Alexa+-specific was
built from 2026-10-10 onward:

- Self-hosted MCP gateway and the MCP error mapping (`integrations/alexa_mcp/server/`)
- URL-elicitation approval flow and independent review page
- SQLite-backed replay integration across restarts
- Simulated merchant MCP server and the injected-product fixture
- Deterministic injection comparison and ApprovalBench Lite
- Real-client MCP test suites, dependency audits, secret scanning, and CI on Ubuntu and Windows
- On 2026-10-21 and 22: the live simulated-assistant page, a scripted terminal client, a browser-compatible certificate fix, a readable review page (dollars and UTC times), and a dependency-audit fix

**[OWNER: confirm that no CallGate code existed outside this repository before 2026-08-31. If any part of CallGate was submitted to another hackathon, name it here.]**

## Challenges we ran into

- **SDK 2.x migration:** the familiar FastMCP import is gone in `mcp` 2.x. The SDK's own error message pointed to `MCPServer`.
- **Policy refusals vs. crashes:** an ordinary exception surfaced as a generic "Error executing tool". Expected refusals have to be SDK `ToolError`s to carry a stable reason code.
- **URL elicitation on the client:** the Python client surfaced `-32042` as a generic `MCPError`, so we rebuild `UrlElicitationRequiredError` ourselves.
- **A rejected retry closed the stream:** an unmapped rejection during a URL-elicitation retry ended the SSE stream ("SSE stream ended without a response"). Mapping every expected rejection to `ToolError` fixed it.
- **Browsers:** our first self-signed certificate used Ed25519. Python accepted it, but Windows Schannel did not, so the review page could not open from a Windows browser. We switched to ECDSA P-256.
- **Fairness:** a deny-everything system looks safe and helps nobody. So we report legitimate completion alongside attack outcomes.

## Accomplishments we're proud of

- The poisoned conversation can ask for anything, but it cannot mint proof. The approval decision lives on a different page, owned by a different principal, and loads server-held facts.
- **Exact, once:** approval binds the tool and its arguments, and it is consumed on use.
- In our deterministic offline fixture, a deliberately vulnerable test double executed **2 of 2** injected simulated actions without CallGate and **0 of 2** with CallGate (`docs/amazon/merchant_injection_results.json`). These are fixture counts, not a real-world rate.
- ApprovalBench Lite is an author-scripted simulation (`evaluation_checkout/approvalbench/REPORT.md`). Agent-authored confirmation (D1) was fooled by a changed display in **100/100** runs. CallGate (D5) had **0/100** successes in each of three attack cells. The legitimate-completion and latency figures there are author-selected parameters, not measurements.
- Public CI passes on Ubuntu and Windows, with dependency audits and a redacted full-history secret scan.

## What we learned

Prompt-injection resistance and authorization are different jobs. The model can
stay fooled while a deterministic gateway still refuses to act. An independent
reviewer is not enough on its own, either. The review must show server-held
parameters, bind the exact operation, and be consumed once.

## What's next

Real deployment needs identity enrollment and recovery for contacts, audited
payment integrations, multi-tenant isolation, a privacy review, user research
with older adults and their families, and validation inside the actual
assistant runtime.

## What is simulated (please read)

The voice assistant, the merchant, products, payments, orders, contacts,
identities, and approval credentials are all simulated. The assistant page and
the terminal client are scripted MCP clients. In the shopping scenario the
assistant deliberately obeys injected text. The offline vulnerable agent is a
deterministic test double. None of these is Alexa+ or an LLM. Nothing connects to Alexa+, Amazon accounts,
banks, payment networks, or SMS. The contact credential is a local demo value,
not proof of a person.

## Try it

Public repository (MIT): https://github.com/Cyberchopin/callgate-alexa-mcp

```bash
git clone https://github.com/Cyberchopin/callgate-alexa-mcp.git && cd callgate-alexa-mcp
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements-lock.txt -r requirements-verification.txt -r requirements-safety.txt -r integrations/alexa_mcp/requirements.txt
python -m scripts.run_amazon_services --replay-db .test-tmp/demo-replay.sqlite3 --merchant-port 8001 --gateway-port 8443 --assistant-port 8002
# open http://127.0.0.1:8002/ (live assistant); review links open on https://127.0.0.1:8443
# terminal alternative: python -m scripts.amazon_live_demo --merchant http://127.0.0.1:8001/mcp --gateway https://127.0.0.1:8443/mcp
python -m pytest -q
```

The full walkthrough is in `docs/release/AMAZON_DEMO_RUNBOOK.md`.

**[OWNER: these commands are on `main` only after the release branch is merged. See AMAZON_BLOCKERS.md, item B-1.]**

Video: **[OWNER: YouTube or Vimeo URL]**

Gallery images (real captures, 2026-10-22), in `docs/release/screenshots/`:

1. `transfer-1-paused.png`: the transfer paused at the gateway.
2. `transfer-2-contact.png`: the contact's independent review.
3. `transfer-3-final.png`: completed once, then a new review required.
4. `shopping-3-final.png`: poisoned product text, the contact's denial, and the blocked canary.
5. `shopping-2-contact.png`: the contact sees $5,000.00 to injected-wallet.

---

## Product feedback (required, per tool)

### Model Context Protocol specification 2025-11-25

- **Used for:** Streamable HTTP transport, URL-mode elicitation (`-32042`), and `notifications/elicitation/complete`.
- **What worked well:** URL-mode elicitation is exactly the right primitive for out-of-band approval. It lets a server move a sensitive decision out of the model's context without the client holding secrets.
- **What needs work:** there are few end-to-end examples of a URL-elicitation *retry* (pause → out-of-band approval → completion → retry), and no guidance on mapping expected domain rejections during that retry.
- **Onboarding:** reading the specification directly was necessary to implement URL mode correctly.
- **Would we build with it again?** **[OWNER: Yes/No + one sentence]**

### MCP Python SDK (`mcp==2.3.0`)

- **Used for:** both MCP servers (`MCPServer`, typed tools, Streamable HTTP app), the real `ClientSession` in tests and the demo client, `UrlElicitationRequiredError`, and `send_elicit_complete`.
- **What worked well:** a real client discovered typed tools over Streamable HTTP with very little code. The `-32042` error and the completion notification worked end to end.
- **What needs work:**
  - The v2 rename from `FastMCP` to `MCPServer` should appear in the Streamable HTTP quickstart. The runtime error message already explains it well.
  - The docs need an example of an expected policy denial using `ToolError`, as opposed to an unexpected exception.
  - The client should rebuild `UrlElicitationRequiredError` from `-32042` automatically, or the docs should show the manual `from_error` conversion.
  - An unmapped exception during a URL-elicitation retry ended the SSE stream. That needs a regression test or documentation.
- **Workarounds:** use the `MCPServer` import; subclass `ToolError` for refusals; call `UrlElicitationRequiredError.from_error(error.error)` after checking the code.
- **Onboarding:** reaching a hello-world server was quick once we knew about the v2 rename. URL elicitation took specification reading plus real-client tests.
- **Would we build with it again?** **[OWNER: Yes/No + one sentence]**

---

## Friction log (optional; up to 10 % bonus)

**F-1 — SDK 2.x server rename** (severity: medium; 2026-10-10)
- **Task:** build a Streamable HTTP MCP server with the pinned SDK.
- **Steps:** imported the familiar FastMCP server class.
- **Expected:** the import succeeds.
- **Actual:** `ModuleNotFoundError: No module named 'mcp.server.fastmcp'`. The message itself pointed to `MCPServer` and the migration guide.
- **Workaround:** `from mcp.server.mcpserver import MCPServer`, pinned to `mcp==2.3.0`.
- **Suggestion:** show the v2 import beside the Streamable HTTP quickstart examples.

**F-2 — Expected refusals look like crashes** (severity: medium; 2026-10-10)
- **Task:** return a stable policy code when an unauthorized tool call is refused.
- **Steps:** raised an integration-specific `ValueError` containing the code.
- **Expected:** the client receives the code in the tool error content.
- **Actual:** the client received only "Error executing tool send_money" (`UnexpectedToolError`).
- **Workaround:** subclass `mcp.server.mcpserver.exceptions.ToolError`.
- **Suggestion:** document a policy-denial example that contrasts `ToolError` with an unexpected exception.

**F-3 — Client does not specialize the URL-elicitation error** (severity: medium; 2026-10-10)
- **Task:** read the URL-mode fields after the server raised `UrlElicitationRequiredError`.
- **Steps:** caught the exception from `ClientSession.call_tool`.
- **Expected:** a specialized error type exposing `.elicitations`.
- **Actual:** `mcp.shared.exceptions.MCPError: URL elicitation required`.
- **Workaround:** check `code == -32042`, then call `UrlElicitationRequiredError.from_error(error.error)`.
- **Suggestion:** reconstruct the specialized error automatically in the client dispatcher.

**F-4 — A rejected retry ended the SSE stream** (severity: medium; 2026-10-11)
- **Task:** reject a retry whose `claimed_identity` changed after approval.
- **Steps:** called `send_money` with the changed identity via `ClientSession.call_tool`.
- **Expected:** a `ToolError` result with a stable reason, with the stream still open.
- **Actual:** `MCPError: SSE stream ended without a response` (code `-32000`).
- **Workaround:** map every expected approval rejection to a `ToolError` at the adapter boundary.
- **Suggestion:** document rejection mapping during URL-elicitation retries, and add an SDK regression test so an expected rejection never closes the stream.
