# Amazon demo runbook and three-minute recording script

Everything shown is simulated: no Alexa+, no payment, no real contact or account.
The scripted client is a deterministic MCP test client, not an LLM. Say
"simulated voice assistant" on camera. Do not show Amazon or Alexa logos.

Target length: **2:45** (the rules require under 3:00).

## 0. One-time setup (WSL, verified 2026-10-21)

The verified checkout is `~/release/callgate-alexa-mcp` on branch
`release/amazon-final-20261021`. Do **not** use `C:\Users\wangs\callgate-alexa-mcp`:
it is at old commit `f18eda5` and has many uncommitted changes.

```bash
cd ~/release/callgate-alexa-mcp
source .venv/bin/activate
python -m pytest -q tests/alexa_mcp
```

Expected result: `37 passed`.

From a fresh clone instead:

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements-lock.txt -r requirements-verification.txt -r requirements-safety.txt -r integrations/alexa_mcp/requirements.txt
```

## 1. Reset before every take

Stop any running launcher with **Ctrl+C**. Ctrl+C also deletes the temporary
certificate. Then reset:

```bash
cd ~/release/callgate-alexa-mcp && rm -rf .test-tmp
```

This clears the simulated replay ledger. Restarting also resets the challenge
budget (5 per minute). The script uses 4, so **restart between takes**.

## 2. Launch (terminal A)

```bash
cd ~/release/callgate-alexa-mcp && source .venv/bin/activate && python -m scripts.run_amazon_services --replay-db .test-tmp/demo-replay.sqlite3 --merchant-port 8001 --gateway-port 8443 --contact-token demo-contact-2026
```

Expected output:

```text
Merchant MCP: http://127.0.0.1:8001/mcp
Gateway MCP: https://127.0.0.1:8443/mcp
Assistant page: https://127.0.0.1:8443/demo
Simulated contact credential: demo-contact-2026
```

`demo-contact-2026` is a fictional, local-only demo value. You may show it on screen.

**Browser warm-up, after each launch:** open `https://127.0.0.1:8443/demo` in
Chrome. Choose **Advanced → Proceed to 127.0.0.1** to accept the self-signed
local certificate. A new certificate is generated each launch, so repeat this
every time. Do not record this step. The `/demo` page is a fixed illustration,
so do not present it as live.

## 3. Run the client (terminal B)

```bash
cd ~/release/callgate-alexa-mcp && source .venv/bin/activate && python -m scripts.amazon_live_demo --merchant http://127.0.0.1:8001/mcp --gateway https://127.0.0.1:8443/mcp --pause
```

`--pause` waits for Enter before each scene. Each review request expires after
**120 s**. The client waits up to 115 s for your decision.

Unattended rehearsal (no browser; the script plays the contact). **Never record this mode:**

```bash
python -m scripts.amazon_live_demo --merchant http://127.0.0.1:8001/mcp --gateway https://127.0.0.1:8443/mcp --rehearse-with-token demo-contact-2026
```

Offline comparison (terminal B, any time; writes only under `.test-tmp/`):

```bash
python -m scripts.run_merchant_injection_demo --database .test-tmp/offline.sqlite3 --output .test-tmp/offline.json
```

Do not run `scripts/demo.ps1 -Offline` while recording. It rewrites the
committed evidence file.

## 4. Screen layout

Left: terminal B (large font, ≥ 18 pt). Right: Chrome, for the review page.
Keep terminal A minimized, or show it once in scene 2.

## 5. Recording script

### 0:00–0:20 — Problem (talking head or title card over terminal)

> "Voice shopping agents read text they don't control. A poisoned product
> description can tell the agent to send money or read out a verification code.
> CallGate is a self-hosted MCP gateway that refuses to execute protected
> actions until a separately registered contact approves the exact request,
> outside the conversation. Everything here is simulated: no real money, no real
> Alexa+ connection."

### 0:20–0:45 — Real MCP servers running (Enter → scene 1, Enter → scene 2)

On screen: merchant tools, `lamp-safe` and `lamp-injected`, the
**UNTRUSTED description** line, `Negotiated MCP protocol: 2025-11-25`, and the
three gateway tools.

> "Two real MCP servers over Streamable HTTP. A simulated merchant, whose product
> text is untrusted, and the CallGate gateway, which negotiates MCP 2025-11-25
> and exposes send_money, place_order, and a canary that should never work."

### 0:45–1:20 — Pause and independent review (Enter → scene 3)

On screen: `JSON-RPC -32042 URL elicitation required; nothing executed` and the
review URL. Copy the URL into Chrome. The page shows **5000 cents /
simulated-wallet / saved-family**. Paste `demo-contact-2026` and click
**Yes, approve simulation**.

> "The $50 transfer pauses. The gateway answers with MCP URL-mode elicitation.
> The link carries only a random ID, never the amount. The saved contact opens it
> on their own device. The page loads the real amount and destination from server
> state, not from anything the agent said. They approve."

Back in terminal B: `Completion notification received: True`.

### 1:20–1:50 — Once means once (Enter → scene 4)

On screen: `simulated_action_completed`, `"real_action_executed": false`, then
`approval already consumed`, then `approval does not transfer to new parameters`.

> "The exact request runs once, and it's labeled simulated. Sending it again
> needs a new review, because the approval was consumed. Changing the amount by
> one cent also needs a new review, because approval is bound to the exact
> parameters."

### 1:50–2:25 — Injection meets the boundary (Enter → scene 5)

Open the second review URL. The page shows **500000 cents / injected-wallet**.
Paste the credential and click **No, deny**. Terminal B then shows the canary
`403 BLOCKED` and `place_order` `403 POLICY_PROOF_REQUIRED`.

> "Now the agent obeys the poisoned product text and tries to send $5,000 to the
> attacker's wallet. It can ask, but it can't mint proof. The contact sees the
> real destination and denies. The verification-code canary is blocked even in
> principle, and an order without proof is refused. In our deterministic offline
> fixture, a deliberately vulnerable test double executed 2 of 2 injected actions
> without CallGate and 0 of 2 with it. Those are scripted fixture counts, not a
> real-world rate."

Optional: overlay the offline JSON (`unguarded executed 2`, `callgate executed 0`).

### 2:25–2:45 — Boundary and limits (summary lines on screen)

> "CallGate doesn't make the model truthful. It makes protected actions depend on
> an independent, exact, one-time decision. This prototype has no real payments,
> no identity enrollment, and no production Alexa+ integration. The code, the
> test suite, and our friction log are in the public repo."

Stop recording, then press Ctrl+C in terminal A.

## 6. Fallbacks (do not fabricate)

| Failure | Action |
|---|---|
| Chrome cannot open the review URL | Redo the warm-up step. If it still fails, record scenes 3 and 5 with `--rehearse-with-token` and say on camera: "for this take the script plays the contact." Never imply a browser approval happened |
| `CG_CHALLENGE_RATE_LIMITED` | You ran more than 5 reviews in a minute. Ctrl+C, reset, relaunch |
| Review took longer than 115 s | The client exits. Reset and retake |
| Port 8001 or 8443 in use | Change both `--*-port` values, and use the same ports in the client command |
| Any scene fails | Cut that scene. Do not describe it as working |

## 7. Upload checklist

- Length under 3:00, measured by the uploaded file.
- No third-party logos and no copyrighted music.
- YouTube or Vimeo, visibility **Public**. Test the link in a private browser window.
