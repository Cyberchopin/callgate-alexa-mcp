# CallGate Checkout

**Pay exactly what you agreed in the chat.**

My brother resells hats, blind boxes and sneakers. Deals happen in chat: the buyer asks, he quotes, they haggle, someone says "deal", and he sends a PayPal link. The money step is where it goes wrong — a typo, a link from a different listing, shipping counted twice, an assistant that drafted the order from the wrong message. The buyer often doesn't notice, and the mismatch surfaces later as a refund request or a dispute that's one person's word against the other's.

CallGate Checkout puts one check between the conversation and the charge:

1. Paste the chat. Two readers extract the agreed price, currency, shipping and the message where the other person said yes — every value comes with the exact words it was copied from.
2. A person confirms those terms. A value that is not in the chat cannot be confirmed.
3. The PayPal order (built by CallGate, or drafted elsewhere — by hand or by an AI sales agent) is compared with the terms field by field.
4. The payer confirms the exact order version they saw. If the order changes afterwards, it cannot be captured.
5. The capture runs once — through double clicks, timeouts, restarts and duplicate webhooks — and ends in a signed receipt.

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
