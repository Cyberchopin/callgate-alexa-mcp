# Demo video — script and shot list (target 2:50, hard limit 3:00)

Devpost rules: under 3 minutes, public on YouTube, showing the project working on the device it was built for, with no copyrighted music. Record in the **PayPal sandbox** with `ANTHROPIC_API_KEY` set, so the real PayPal approval page and the real AI assistant are both on screen.

**Setup before recording**
- Terminal 1:
  ```
  export PAYPAL_CLIENT_ID=… PAYPAL_CLIENT_SECRET=… ANTHROPIC_API_KEY=… CALLGATE_DEMO=1
  python -m integrations.paypal_checkout.server
  ```
  Use `CALLGATE_DEMO=1` so the "change the order" button stays available on the sandbox.
- Browser window 1 (seller): http://localhost:8787 at 1280 px wide.
- Browser window 2 (buyer): the payer link, in phone-sized responsive mode (390 px).
- A sandbox *personal* account logged in on window 2's PayPal.
- Run `python -m pytest tests/paypal_checkout -q` and `python -m evaluation_paypal.run` just before recording, so the numbers you say are today's.

**Voice:** calm, a little slower than normal. One idea per sentence. Each line below is about 8–10 seconds.

| Time | On screen | Say (word for word) |
|---|---|---|
| 0:00 | A real resale chat on your phone, names blurred | "My brother resells caps he buys in Japan. Every deal happens in a chat — and then he sends a PayPal link." |
| 0:08 | Same chat, zoom on "$80" and "deal" | "The chat and the payment never meet. That's where buyers and sellers both get burned." |
| 0:16 | Seller page → "Use a risky cross-border example" → "Read the agreement" | "CallGate Checkout reads the deal. A hundred and forty dollars, with the exact words each number came from." |
| 0:26 | Point at the two yellow flags | "It also catches the classic traps in this chat. 'Ship it to my cousin' — PayPal doesn't protect parcels sent to another address. And 'friends and family', which protects nobody." |
| 0:40 | "Confirm these terms". Passport form: "Acquired · Tokyo proxy" with the receipt photo → "Add to passport" | "The seller confirms the terms, and records where the cap came from. Each holder adds a signed entry, so the next buyer can check the whole chain." |
| 0:54 | "Let the AI sales assistant draft it" → the assistant panel opens | "Now the seller lets the AI assistant draft the PayPal order. It works through a gateway that can draft — and nothing else." |
| 1:06 | Assistant panel and PayPal order table (whatever it drafted) | "Whatever it drafts is checked, line by line, against what the seller confirmed. If it gets the price wrong, the order is blocked and the buyer never gets a link." |
| 1:18 | Seller copies the buyer link → buyer window: tag, flags, passport → "This is what we agreed — continue" | "The buyer sees the same terms, the same warnings, and where the item came from — then confirms this exact order." |
| 1:30 | "Approve in PayPal" → real PayPal sandbox page → approve | "They approve on PayPal, as usual." |
| 1:36 | Back on CallGate: "Complete payment" → payment held (if your sandbox buyer's address is outside the US) or paid | "Before any money moves, PayPal's shipping address is checked against the chat. This deal said 'within the US only'. If the address is somewhere else, the payment is held until the seller agrees." |
| 1:50 | Seller: demo button "Change the order to $180 after the payer confirmed" → buyer: "Complete payment" → refused | "And if anyone edits the order after the buyer confirmed — a bug, or a compromised agent — it can't be charged. Nothing moved." |
| 2:02 | Rebuild → confirm → pay. Seller history list | "Rebuilt from the terms, it's paid once. Double taps, timeouts after PayPal already charged — every case ends in exactly one capture." |
| 2:14 | Packing checklist: photo of the cap, the original box, the tags | "Now the promises in the chat become the packing list. 'Comes with the original box' — so the box gets a photo." |
| 2:24 | Label ZIP, weight, UPS → liability warning → ship | "The label has to go to PayPal's address. The weight is recorded — that's what settles 'the box was empty'. And UPS only covers a hundred dollars by default, so it warns." |
| 2:36 | Buyer: "It arrived as described". Then the consent JSON / evidence pack | "The buyer confirms it arrived. If there's ever a dispute, every step is signed and chained — the chat, the offer, the approval, the charge — already in PayPal's evidence format." |
| 2:46 | Title card: "CallGate Checkout — pay what you agreed, ship what you promised" | "CallGate Checkout. Pay what you agreed. Ship what you promised." |

**If you're running long**, cut the passport line at 0:40 and the "$180 after confirmation" scene at 1:50. Keep the AI assistant scene and the address hold: they are the two judges are most likely to remember.

**If you record offline instead of the sandbox**, say "simulated PayPal" once out loud, and use "Payer approves with a Toronto address" for the hold scene. Don't present the simulator as the real PayPal page.
