# Demo video — under 3:00

Record in the PayPal sandbox if you can (real approval page). Every step also works offline with the demo buttons. Use "Use a risky cross-border example" — one chat shows most of the product.

| Time | Screen | Say |
|---|---|---|
| 0:00–0:15 | Phone screenshot of a real resale chat (blur names) | "My brother resells caps he buys in Japan. Deals happen in chat, then he sends a PayPal link. The chat and the payment never meet — and that's where both sides get burned." |
| 0:15–0:40 | Seller page: risky example → "Read the agreement". Point at the tag and the two flags | "CallGate reads the deal: $140 total, with the exact words it came from. It also catches the two classic traps in this chat: 'ship it to my cousin' — PayPal doesn't protect parcels sent elsewhere — and 'friends and family', which protects nobody. Both sides see these." |
| 0:40–0:55 | Confirm terms. Passport form: add "Acquired · Tokyo proxy" with the receipt photo | "Where did it come from? Each seller adds a signed entry with the receipt photo's hash. The next seller can verify the whole chain before adding theirs." |
| 0:55–1:10 | Demo: "AI sales agent drafts the order at $180" → red | "Sellers let assistants send the link now. This one was told to charge $180. The order is checked against the chat — can't be paid. Rebuild from the terms." |
| 1:10–1:30 | Phone: payer page — tag, flags, passport — "This is what we agreed" → PayPal approval | "The buyer sees everything before paying, including where the cap came from, and confirms this exact order." |
| 1:30–1:50 | Demo: "Payer approves with a Toronto address" → Complete payment → held | "Shipping was agreed 'within the US only'. PayPal says Toronto. The payment is held — nothing charged — until the seller decides. He agrees and gives a reason; it's in the receipt." |
| 1:50–2:10 | Release hold → pay. Demo: "PayPal times out after charging", "Send two payment requests at once", "How many charges?" → 1 | "And it charges once, even when PayPal times out after taking the money, or the buyer double-taps." |
| 2:10–2:40 | Packing checklist → label ZIP, weight, UPS → liability warning → ship. Phone: "It arrived as described" | "The promises in the chat become the packing list. The label has to go to PayPal's address, the weight is recorded — that's what wins 'the box was empty' — and UPS only covers $100 by default, so it warns. Tracking goes to PayPal. The buyer confirms it arrived." |
| 2:40–3:00 | Evidence pack JSON, test count | "If there's a dispute, the evidence is already in PayPal's format. 74 tests, zero wrong totals on our benchmark. Pay what you agreed, ship what you promised." |

Before recording: `python -m pytest tests/paypal_checkout -q` and `python -m evaluation_paypal.run` so the numbers you say are today's numbers.
