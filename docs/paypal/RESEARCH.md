# What goes wrong in small-seller resale — and what CallGate Checkout does about it

Collected October 25, 2026. Each row is a problem people report publicly, the rule that decides who loses money, and the feature that answers it. Where we could not confirm a rule from a primary source, we say so.

## Problems and rules

| # | What happens | Who it hurts | The rule that decides it | Source |
|---|---|---|---|---|
| 1 | The PayPal link doesn't match what was agreed in chat (typo, wrong listing, shipping counted twice). | Buyer, then seller (refund) | For "not as described" claims the item and terms are compared with the seller's description; the chat is the only record of the deal. | PayPal Purchase Protection (US) |
| 2 | Buyer asks to ship to a different address ("it's a gift for my friend"), then files Item Not Received. | Seller | Seller Protection requires shipping to the address on the Transaction Details page; items redirected elsewhere are not covered. | PayPal Seller Protection (US); seller-scam write-ups |
| 3 | Buyer insists on using their own shipping company or label, reroutes the parcel, claims non-delivery. | Seller | Same address rule; PayPal advises against buyer-arranged shipping services. | PayPal Seller Protection; seller-scam write-ups |
| 4 | Buyer overpays and asks for the difference back by wire, or asks to pay as "friends and family". | Seller / buyer | Personal (friends and family) payments are not covered by Purchase Protection; refunds outside PayPal aren't protected. | PayPal Purchase Protection; seller-scam write-ups |
| 5 | "The box was empty." Tracking proves a box arrived, not what was in it. | Seller | Tracking alone is weak; what helped sellers was the carrier's acceptance weight on the counter receipt, carrier scan photos, and packing photos/video. | eBay seller community threads |
| 6 | Lost or damaged parcel worth more than the carrier's default liability. | Seller | UPS shipments generally carry a $100 default declared value; claims within 60 days, with proof of value, packaging photos and tracking. Default liability is not insurance. | UPS declared value guide (Unishippers) |
| 7 | Inflated shipping: an item that ships for $10–15 listed with $45–55 shipping; profit moved into the shipping line. | Buyer | Marketplaces say excessive shipping isn't allowed but rarely enforce it; buyers' advice is to compare total cost. | eBay community threads |
| 8 | Shipping agreed for one destination, then paid from an address elsewhere (domestic rate, international address). | Seller | No platform rule; the agreed shipping simply doesn't cover the destination. | Seller reports; our own design |
| 9 | Cross-border parcels into the US now owe duties: the de minimis exemption was suspended on August 29, 2025. Who pays (DDP = seller, DAP = recipient) must be explained before payment. | Buyer (surprise bill), seller (refused parcel) | Duties depend on the service and billing arrangement; explain charges before payment. | WooCommerce advisory on the end of US de minimis |
| 10 | Goods bought in Japan (stores, Mercari via proxies) and resold abroad. Sealed items are hardest to verify; proxies don't guarantee authenticity; cross-border purchases are often outside platform protection. Buyers are told to keep serial/shrinkwrap photos, cert numbers and conversations. | Buyer and every reseller in the chain | Purchase Protection excludes items bought for resale, so the reseller in the middle carries the risk alone. Counterfeit counts as "not as described" for the final buyer. | Buy&Ship Japan proxy guide; PayPal Purchase Protection |
| 11 | Non-delivery is the most common complaint in online-shopping scam reports (35% of ~121k BBB reports 2020–2025); fake tracking appears in about 10%. | Buyer | — | Incogni analysis of BBB Scam Tracker reports |

Not confirmed: we found references to a signature-confirmation threshold for high-value orders, but the current US Seller Protection page we read does not mention one, so the product does not enforce it.

## What the product does about each

| # | Feature | Where |
|---|---|---|
| 1 | Terms read from the chat with quotes; PayPal order compared field by field; payer confirms the exact order version. | `extract.py`, `order_check.py`, `service.py` |
| 2, 3 | **Ship-to lock.** The PayPal ship-to address is recorded at capture. Chat lines asking to redirect, use a forwarder, or use the buyer's own shipper are flagged with their quote. At "Mark shipped" the seller types the label's ZIP and country; a mismatch blocks shipping. | `risk.py`, `service.ship` |
| 4 | Chat lines asking for friends-and-family, wire, Zelle, crypto or overpayment refunds are flagged to both sides before payment. | `risk.py` |
| 5 | **Package-out record.** Packed weight and the carrier counter receipt photo are recorded before shipping and go into the signed receipt and the dispute evidence. | `shipping.py` |
| 6 | **Liability check.** If the item is worth more than the carrier's default liability and no declared value is entered, shipping warns before the label is used. | `risk.py` |
| 7 | The shipping line is shown to the payer with the exact chat words that set it; a shipping charge that was never discussed is flagged. | `order_check.py` |
| 8 | **Destination check.** If the chat fixed where shipping goes (a country, "US only", "domestic") and PayPal's ship-to is elsewhere, capture is refused until the seller and buyer re-agree. | `risk.py`, `service.capture` |
| 9 | **Duties check.** Cross-border orders where nobody said who pays duties get a warning to both sides before payment, with the DDP/DAP explanation. | `risk.py` |
| 10 | **Provenance passport.** Each holder adds a signed, hash-linked entry (where it was bought, when, receipt and serial photos as hashes). The chain travels with the item to the next seller, who can verify every link before adding their own. Shown to the payer before paying, labelled as seller-provided. | `provenance.py` |
| 11 | Tracking goes to PayPal through the Orders API so it can't be a screenshot; the payer can mark "received as described", which is recorded in the receipt. | `service.ship`, `service.acknowledge` |

## What we deliberately do not claim

- We don't authenticate items. A provenance passport proves who recorded what and when, and that nothing in the chain was altered — not that a receipt is genuine.
- We don't know carriers' delivery scans; delivery status comes from the carrier and PayPal.
- Seller and buyer protection decisions are PayPal's. We help each side keep the evidence those rules ask for.

## Sources

- PayPal Seller Protection (US): https://pep.paypal.com/legalhub/seller-protection
- PayPal Purchase Protection (US): https://pep.paypal.com/legalhub/buyer-protection
- Common PayPal scams targeting sellers: https://hongkiat.com/blog/paypal-scams-targeting-sellers
- eBay community, "Buyer claims box was empty": https://community.ebay.com/t5/Selling/Buyer-claims-box-was-empty/m-p/34322717
- eBay community, inflated shipping: https://community.ebay.ca/t5/Archive-1/I-am-finding-that-certain-sellers-are-overcharging-shipping-by-a/m-p/365316
- UPS declared value guide: https://www.unishippers.com/shipping-resources/parcel-resources/ups-declared-value
- End of US de minimis: https://woocommerce.com/document/end-of-us-de-minimis-what-to-do/
- Japan proxy shopping and fakes: https://www.buyandship.com.my/blog/japan-proxy-shopping-fake-guide-2482526/
- BBB online shopping scam reports (Incogni analysis): https://blog.incogni.com/holiday-online-shopping-scams-analyzed/
