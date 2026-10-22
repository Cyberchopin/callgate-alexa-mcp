# Amazon demo runbook and three-minute recording script

Everything shown is simulated: no Alexa+, no payment, no real contact or account.
The assistant is a scripted MCP client, not an LLM. Say "simulated voice
assistant" on camera. Do not show Amazon or Alexa logos.

Target length: **2:45** (the rules require under 3:00).

## 0. One-time setup (WSL, verified 2026-10-22)

The verified checkout is `~/release/callgate-alexa-mcp` on branch
`release/amazon-final-20261021`. Do **not** use `C:\Users\wangs\callgate-alexa-mcp`;
it is at old commit `f18eda5` and has many uncommitted changes.

```bash
cd ~/release/callgate-alexa-mcp && source .venv/bin/activate && python -m pytest -q tests/alexa_mcp
```

Expected: every test passes.

From a fresh clone instead:

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements-lock.txt -r requirements-verification.txt -r requirements-safety.txt -r integrations/alexa_mcp/requirements.txt
```

## 1. Reset before every take

1. Stop any running launcher with **Ctrl+C**. Ctrl+C also deletes the temporary certificate.
2. Reset with:

```bash
cd ~/release/callgate-alexa-mcp && rm -rf .test-tmp
```

This clears the simulated replay ledger. Restarting also resets the challenge
budget of 5 per minute. One take uses 3, so **restart between takes**.

## 2. Launch (terminal A)

```bash
cd ~/release/callgate-alexa-mcp && source .venv/bin/activate && python -m scripts.run_amazon_services --replay-db .test-tmp/demo-replay.sqlite3 --merchant-port 8001 --gateway-port 8443 --assistant-port 8002 --contact-token demo-contact-2026
```

Expected output:

```text
Merchant MCP: http://127.0.0.1:8001/mcp
Gateway MCP: https://127.0.0.1:8443/mcp
Live assistant: http://127.0.0.1:8002/
Illustrative fixture page: https://127.0.0.1:8443/demo
Simulated contact credential: demo-contact-2026
```

`demo-contact-2026` is a fictional, local-only demo value. It is fine to show it.

**Browser warm-up after each launch (not recorded):**

1. In Chrome, open `https://127.0.0.1:8443/demo`.
2. Choose **Advanced → Proceed to 127.0.0.1**. Each launch generates a new self-signed certificate, so you must repeat this every time.
3. Open `http://127.0.0.1:8002/`, the live assistant.

Do not present `/demo` as live. It is a fixed illustration.

## 3. Screen layout

- **Left (about 60 %):** Chrome window with the live assistant at `http://127.0.0.1:8002/`. Zoom to 110–125 %.
- **Right (about 40 %):** a second Chrome window, the "contact's device". Review links opened from the assistant land here; drag the new tab into this window.
- **Terminal A:** show it once, in the opening.
- **Optional:** tick **Read replies aloud** on the assistant to give it a voice. Chrome's built-in voice runs locally.

## 4. Recording script

### 0:00–0:20 — The problem (title card, or narration over terminal A)

> "Voice shopping agents read text they don't control. One poisoned product
> description can tell the agent to send money or read out a verification code.
> Older adults reported $2.4 billion in fraud losses to the FTC in 2024. CallGate
> is a self-hosted MCP gateway that won't execute a protected action until a
> separately registered contact approves the exact request, outside the
> conversation. Everything here is simulated. No real money, and no real Alexa+."

On screen: terminal A showing three local services, then switch to the assistant.

### 0:20–1:15 — A legitimate transfer, reviewed by the contact

Click **"Send $50 to my grandson"**.

On screen:
- **MCP connection:** `CallGate gateway: MCP 2025-11-25 over Streamable HTTP. Tools: send_money, place_order, share_verification_code.`
- The assistant line.
- The amber card: **Paused: $50.00 has not moved.**

> "The assistant connects to the CallGate gateway over MCP 2025-11-25 and asks
> to send fifty dollars. The gateway doesn't execute it. It answers with MCP
> URL-mode elicitation, and the link carries only a random ID."

Click **Open review on the contact's device**. In the right window the page shows
**$50.00 (5000 cents) · simulated-wallet · saved-family**. Paste
`demo-contact-2026` and click **Yes, approve simulation**.

> "The saved contact opens it on their own device. The amount and destination
> come from server state, not from anything the agent said. They approve."

### 1:15–1:40 — Once means once

Back in the left window: the green **Done… simulated, no real money moved**
card, then **Let me try sending the same thing again**, then the red
**Not without a new review: that approval was used once.**

> "The approved transfer runs exactly once, and it's labeled simulated. Asking
> again needs a new review. Approval is bound to the exact parameters and spent
> on use."

### 1:40–2:25 — Poisoned product text meets the boundary

Click **"Find me a reading lamp"**.

On screen:
- **MCP connection** to the simulated merchant.
- Two product cards.
- **UNTRUSTED PRODUCT TEXT** card.
- The assistant saying it will obey.
- **Paused: $5,000.00 · injected-wallet**.

> "Now the assistant shops at a simulated store. One product description is
> poisoned, and this deliberately obedient test assistant follows it and tries to
> send five thousand dollars. It can ask, but it can't mint proof."

Open the review and confirm it shows **$5,000.00 · injected-wallet**. Paste the
credential and click **No, deny**. Back on the left: **Denied… Nothing moved**,
then **Sharing a verification code is permanently blocked, even with approval.**

> "The contact sees the real destination and says no. The verification-code
> canary can't be approved at all. In our offline fixture, a vulnerable test
> double executed two of two injected actions without CallGate and zero of two
> with it. That's a scripted fixture count, not a real-world rate."

### 2:25–2:45 — Limits (assistant page; right panel visible)

> "CallGate doesn't make the model truthful. It makes protected actions depend on
> an independent, exact, one-time decision. There are no real payments, no
> identity enrollment, and no production Alexa+ integration here. The code, the
> test suite, and our friction log are in the public repo."

Stop recording, then press Ctrl+C in terminal A.

## 5. Terminal fallback (same chain, no assistant page)

Run in terminal B. `--pause` waits for Enter before each scene. Each review
expires after **120 s**.

```bash
cd ~/release/callgate-alexa-mcp && source .venv/bin/activate && python -m scripts.amazon_live_demo --merchant http://127.0.0.1:8001/mcp --gateway https://127.0.0.1:8443/mcp --pause
```

Unattended rehearsal, where the script plays the contact. **Never record this mode:**

```bash
python -m scripts.amazon_live_demo --merchant http://127.0.0.1:8001/mcp --gateway https://127.0.0.1:8443/mcp --rehearse-with-token demo-contact-2026
```

Offline comparison (writes only under `.test-tmp/`):

```bash
python -m scripts.run_merchant_injection_demo --database .test-tmp/offline.sqlite3 --output .test-tmp/offline.json
```

Do not run `scripts/demo.ps1 -Offline` while recording; it rewrites the
committed evidence file.

## 6. When something fails (do not fake it)

| Symptom | Action |
|---|---|
| Review link shows a certificate error | Redo the warm-up step for this launch |
| "a scenario is already running" | Wait for the current run to finish, or for its 115 s timeout |
| "No decision arrived in time" | Decide within 115 s. Reset and retake |
| `CG_CHALLENGE_RATE_LIMITED` / "stopped" | More than 5 reviews in a minute. Ctrl+C, reset, relaunch |
| Port 8001, 8002, or 8443 in use | Change the `--*-port` values. The assistant URL changes too |
| Any scene fails | Cut it, or use the terminal fallback. Never describe a failed scene as working |

## 7. Upload checklist

- Length under 3:00, measured on the uploaded file.
- No third-party logos and no copyrighted music.
- YouTube or Vimeo, visibility **Public**. Test the link in a private window.
- Devpost gallery images, real captures from 2026-10-22: `docs/release/screenshots/*.png`.
