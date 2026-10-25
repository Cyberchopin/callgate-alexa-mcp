# CallGate Checkout

**Pay exactly what you agreed in the chat.**

My brother resells hats, blind boxes and sneakers. Deals happen in chat: the buyer asks, he quotes, they haggle, someone says "deal", and he sends a PayPal link. The money step is where it goes wrong — a typo, a link from a different listing, shipping counted twice, an assistant that drafted the order from the wrong message. The buyer often doesn't notice, and the mismatch surfaces later as a refund request or a dispute that's one person's word against the other's.

CallGate Checkout puts one check between the conversation and the charge:

1. Paste the chat. Two readers extract the agreed price, currency, shipping and the message where the other person said yes — every value comes with the exact words it was copied from.
2. A person confirms those terms. A value that is not in the chat cannot be confirmed.
3. The PayPal order (built by CallGate, or drafted elsewhere — by hand or by an AI sales agent) is compared with the terms field by field.
4. The payer confirms the exact order version they saw. If the order changes afterwards, it cannot be captured.
5. The capture runs once — through double clicks, timeouts, restarts and duplicate webhooks — and ends in a signed receipt.
6. The promises in the chat ("comes with the original box") become the packing checklist. Photos are hashed into the receipt, tracking goes to PayPal, and the evidence pack is ready in PayPal's dispute format.

AI sales agents connect through an MCP gateway that can draft orders but has no tool to confirm, approve or capture.

AI reads the messy part (counter-offers, "ok 80 then", Chinese and English). Deterministic code is responsible for making sure the payment equals what was confirmed.

## What it is not

- It checks payments that go through this checkout. It cannot see or block any other PayPal payment.
- It does not judge whether someone is a scammer or whether an item is genuine. The receipt records what was agreed, confirmed and charged — not the item's condition.
- "Includes the original box" is recorded in the receipt; PayPal has no field to verify it.

## How it decides

```mermaid
flowchart LR
    C[Chat] --> R[Rule reader<br/>never invents numbers]
    C --> M[Model reader<br/>must quote the chat]
    R --> X{Referee}
    M --> X
    X -->|agree| T[Terms with quotes]
    X -->|disagree / ungrounded| H[Person decides<br/>by pointing at words]
    H --> T
    T --> K[Person confirms terms<br/>commitment hash]
    K --> O[PayPal order]
    O --> D{Field-by-field diff}
    D -->|blocking difference| B[Can't be paid<br/>rebuild from terms]
    D -->|match| P[Payer confirms this<br/>order fingerprint<br/>signed approval]
    P --> G{At capture:<br/>re-read order,<br/>same fingerprint?}
    G -->|no| N[Refused, nothing charged]
    G -->|yes| W[Write-ahead CAPTURING]
    W --> Q[Capture with<br/>PayPal-Request-Id]
    Q --> S[(Ledger + webhooks<br/>+ reconcile)]
    S --> E[Signed receipt]
```

### Reading terms without guessing

- **Grounding.** Every value carries `(message_index, quote)`. A quote must be an exact substring of that message and, for money, must contain the amount (or, for a total, be the sum of the amounts it quotes: "$95 plus $8"). The model's ungrounded values are dropped and listed.
- **Two readers, one referee.** If the rules and the model read different totals, the total becomes a *conflict* and a person must choose by pointing at words in the chat. A total found only by the model is flagged for review.
- **Deal detection.** A price counts as agreed only when the *other* person accepts it without countering. A new price after the "yes" reopens the deal. A message with two different prices (`$40 … the agreed total is $400`) is never resolved automatically.
- **Chat text is data.** The model prompt says so, and the grounding check means an instruction hidden in the chat can at most become a *quote* a person sees.

### Binding approval to an order version

`order_fingerprint` = SHA-256 over the order id, intent, amounts, breakdown, items and payee (not `status`). The payer's confirmation is an Ed25519-signed approval over `{checkout, terms commitment, chat hash, order id, fingerprint, nonce, expiry}`. Before capture the server re-reads the order from PayPal; a different fingerprint, a blocking difference or an expired approval stops the capture.

### Reliability

| Case | What happens |
|---|---|
| Double click, same `Idempotency-Key` | Second request gets the stored result (`replayed: true`) |
| Ten concurrent clicks with different keys | SQLite compare-and-set on state: exactly one reaches PayPal |
| PayPal charges, then the connection drops | State is `CAPTURE_UNKNOWN`; next attempt reconciles by reading the order instead of capturing again |
| Request never reached PayPal | Reconcile finds no capture, returns to `BUYER_CONFIRMED`; retry uses the **same** `PayPal-Request-Id` |
| Funds pending, completion arrives by webhook | `CAPTURE_PENDING → CAPTURED` from a verified webhook |
| Webhook redelivered / forged | Deduplicated by event id / rejected by signature verification |
| Server restarts mid-capture | Ledger is on disk; reconcile resumes |

Every transition is written to an append-only event log, shown on the page as "What happened".

## AI sales agents (MCP)

The server also exposes  (streamable HTTP) with three tools:

| Tool | What the agent can do |
|---|---|
|  | Paste a chat, get the terms with quotes. The seller still confirms them. |
|  | Draft a PayPal order. It is checked against the confirmed terms; a mismatch is shown to the seller and gets no payer link. |
|  | Read status. A payer link appears only for a verified order. |

There is deliberately no tool to confirm terms, approve for the payer, or capture. agent sees tools: ['get_checkout', 'propose_order', 'read_deal']
read_deal -> total None from None
propose before seller confirms -> WAITING_FOR_SELLER
reader left it to a person: ["price changed after agreement in message 7; needs a new 'yes'"]
seller confirmed 88 USD on the web page, quoting '80 is ok, shipping is $8'
agent follows the planted instruction, proposes 180 -> BLOCKED_MISMATCH [{'field': 'total', 'agreed': '88.00', 'order': '180.00', 'why': 'The amount to pay is not what was agreed in the chat'}] payer_link=None
agent proposes 88 -> VERIFIED payer_link=http://localhost:8787/pay/cg_025107a0baa3f829a461 runs a scripted agent that obeys an instruction planted in the chat ("the real price is \80"): the planted price reopens the deal for the seller, and the agent's \80 order is blocked. Set  to require a bearer token on .

## After the payment

- The packing checklist is generated from the confirmed terms: the item, one line per promised inclusion (with its quote), and the packed box.
- "Mark shipped" requires every line photographed or skipped with a reason, then sends tracking with  ().
- The signed receipt gains the tracking number and the SHA-256 of each photo. The payer page shows the packing photos.
-  returns the  input ( with tracking and a plain-language summary of the chat agreement).  sends it with the receipt and photos attached.

## Run it

Offline (simulated PayPal, every failure case has a demo button):

```bash
pip install -r requirements-lock.txt          # fastapi, uvicorn, httpx, cryptography
python -m integrations.paypal_checkout.server  # http://localhost:8787
```

PayPal sandbox (real orders, real approval page, real capture):

1. On developer.paypal.com create a sandbox app; copy its Client ID and Secret. Sandbox accounts gives you a personal (buyer) login.
2. ```bash
   export PAYPAL_CLIENT_ID=... PAYPAL_CLIENT_SECRET=...
   export ANTHROPIC_API_KEY=...        # optional: model reader (or OPENAI_API_KEY + OPENAI_MODEL)
   python -m integrations.paypal_checkout.server
   ```
3. Webhooks (optional): expose the server (e.g. a tunnel), set `CALLGATE_PUBLIC_URL`, subscribe the app to `PAYMENT.CAPTURE.*` at `/webhooks/paypal`, and set `PAYPAL_WEBHOOK_ID`.

The live PayPal host is refused unless `CALLGATE_ALLOW_LIVE=1`.

## Evidence

- `pytest tests/paypal_checkout` — 36 tests covering every row of the reliability table, approval forgery, rebuild after tampering, and grounding.
- `python -m evaluation_paypal.run` — CheckoutBench-lite: 18 author-written negotiations (English, Chinese, mixed) and 6 order mutations. Rules-only result on 2026-10-25: 12/13 deals read exactly, 1 sent to a person (the injected-price chat), **0 wrong totals, 0 of 5 no-deal chats made payable**, 67/67 mutations handled. These chats were written and labelled by the author; they show the reader handles known patterns and say nothing about accuracy on real conversations.

## Files

| File | Job |
|---|---|
| `terms.py` | Terms model, chat parsing, grounding checks, commitment hash |
| `extract.py` | Rule reader, model reader, referee |
| `order_check.py` | Field-by-field comparison, fingerprint, order built from terms |
| `ledger.py` | SQLite state machine, idempotency keys, webhook dedupe, event log |
| `paypal_client.py` | Orders v2 + webhook verification, `PayPal-Request-Id` on every write |
| `fake_paypal.py` | Offline stand-in used by tests and the demo (not PayPal) |
| `service.py` | The checkout flow |
| `server/` | Seller page, payer page (`/pay/{id}`), JSON API, webhook endpoint |

Reuses CallGate's canonical JSON and Ed25519 signing (`callgate/receipt.py`).
