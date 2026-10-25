# Demo video — under 3:00

Record in the PayPal sandbox if you can (real approval page). Every step also works offline with the demo buttons.

| Time | Screen | Say |
|---|---|---|
| 0:00–0:15 | Phone screenshot of a real resale chat (blur names) | "My brother sells hats online. Deals happen in chat, then he sends a PayPal link. The chat and the payment never meet." |
| 0:15–0:35 | Seller page: paste the hat chat, "Read the agreement" | "CallGate reads the deal. $95 plus $8, haggled to $80. It shows $88 and the exact words each number came from. AI reads the messy part; it can't add a number that isn't in the chat." |
| 0:35–0:55 | Confirm terms → demo: "AI sales agent drafts the order at $180" | "Sellers now let assistants send the link. This one was told by a message in the chat to charge $180. The order is checked against the confirmed terms: red, can't be paid, and it points back to the line where they agreed." |
| 0:55–1:10 | "Rebuild the order from the agreed terms" → READY | "Rebuilt from the terms, it can only say $88." |
| 1:10–1:35 | Phone: payer page → "This is what we agreed" → PayPal sandbox approval | "The buyer sees the same thing and confirms this exact version of the order." |
| 1:35–1:55 | Seller demo: "Change the order to $180 after the payer confirmed" → buyer taps Complete payment → refused | "If anyone edits the order after the buyer confirmed — a bug, a compromised agent — it won't be captured. Nothing was charged." |
| 1:55–2:20 | Rebuild, confirm, approve. Demo: "PayPal times out after charging", then "Send two payment requests at once", then "How many charges did PayPal make?" → 1 | "Payments fail in boring ways: double taps, timeouts after the money moved. It's charged once, and the history shows why." |
| 2:20–2:45 | Packing checklist: photos for the cap, the original box, the tags; tracking number → Shipped; payer page shows photos | "The promises in the chat become the packing list. Tracking goes to PayPal; the buyer sees what was packed. If there's a dispute, the evidence is already in PayPal's format." |
| 2:45–3:00 | Terminal: `python -m scripts.paypal_agent_demo` output, then test count | "Agents get a gateway that can draft orders and never charge. 44 tests, zero wrong totals on our benchmark. Pay exactly what you agreed." |

Before recording: `python -m pytest tests/paypal_checkout -q` and `python -m evaluation_paypal.run` so the numbers you say are today's numbers.
