"""Checks for the ways resale deals actually go wrong (see docs/paypal/RESEARCH.md).

Every flag carries the evidence that raised it — a chat quote, or the two
values that disagree — and the rule or report that makes it matter, so a
seller or payer can see why, not just that, something is flagged.

Severity
  block  money or the parcel must not move until a person resolves it
  warn   shown to both sides before payment / shipping; recorded in the receipt
  info   context, e.g. duties were discussed
"""
from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from decimal import Decimal

from .terms import Message

BLOCK, WARN, INFO = "block", "warn", "info"

SOURCES = {
    "seller_protection": "https://pep.paypal.com/legalhub/seller-protection",
    "purchase_protection": "https://pep.paypal.com/legalhub/buyer-protection",
    "seller_scams": "https://hongkiat.com/blog/paypal-scams-targeting-sellers",
    "de_minimis": "https://woocommerce.com/document/end-of-us-de-minimis-what-to-do/",
    "ups_declared_value": "https://www.unishippers.com/shipping-resources/parcel-resources/ups-declared-value",
    "empty_box": "https://community.ebay.com/t5/Selling/Buyer-claims-box-was-empty/m-p/34322717",
}


@dataclass(frozen=True)
class Flag:
    code: str
    severity: str
    title: str          # one line, plain words
    why: str            # what it means for the buyer and the seller
    message_index: int | None = None
    quote: str | None = None
    source: str | None = None
    protects: str = "both"   # "seller" | "buyer" | "both"

    def to_dict(self):
        return asdict(self)


# ----------------------------------------------------------------- chat lines

_CHAT_PATTERNS: list[tuple[str, str, re.Pattern, str, str, str, str]] = [
    ("REDIRECT_REQUEST", WARN, re.compile(
        r"(ship|send|mail|deliver)\w*\s+(it\s+|this\s+)?to\s+(my|a|her|his|their)\s+"
        r"(friend|cousin|sister|brother|mom|mother|dad|father|son|daughter|relative|work|office|other)"
        r"|(different|another|new|second|other)\s+address|change\s+(the\s+|my\s+)?(shipping\s+)?address"
        r"|it'?s\s+a\s+gift\s+for|(freight|package|parcel)\s+forward|reship|"
        r"寄到我(朋友|同学|亲戚|家人)|换个地址|改(一下)?地址|地址改|别的地址|转运", re.I),
     "Buyer asked to ship somewhere else",
     "PayPal Seller Protection only covers parcels shipped to the address on the PayPal transaction. "
     "Shipping elsewhere and then getting an 'item not received' claim is a known scam.",
     "seller_protection", "seller"),
    ("BUYER_SHIPPER", WARN, re.compile(
        r"my\s+(own\s+)?(shipping\s+)?(courier|shipper|shipping\s+company|shipping\s+account|label|agent)"
        r"|(use|send)\s+(you\s+)?my\s+(ups|fedex|dhl|usps)\s+(account|label)|i'?ll\s+send\s+(you\s+)?(a|the|my)\s+label"
        r"|pick\s*up\s+by\s+my|my\s+driver\s+will|我(自己)?(叫|找)?(的)?快递(来)?(取|拿)|上门取件|我发你面单", re.I),
     "Buyer wants to arrange the shipping",
     "If the buyer controls the shipment they can reroute it and claim it never arrived; "
     "PayPal advises against buyer-arranged shipping.",
     "seller_scams", "seller"),
    ("OFF_PLATFORM_PAYMENT", WARN, re.compile(
        r"friends?\s*(and|&|n)\s*family|\bf\s*&\s*f\b|\bff\b|\bzelle\b|\bvenmo\b|cash\s*app|\bwire\b|western\s+union"
        r"|\bcrypto\b|\busdt\b|bitcoin|\bbtc\b|gift\s*card|朋友(和|与)?家人|微信转账|支付宝|直接转(账|我)", re.I),
     "Someone suggested paying outside this checkout",
     "Friends-and-family and other off-platform payments are not covered by PayPal Purchase Protection, "
     "so neither side can claim if something goes wrong.",
     "purchase_protection", "both"),
    ("OVERPAYMENT", WARN, re.compile(
        r"over\s*paid|paid\s+(you\s+)?too\s+much|(refund|send|return)\s+(me\s+)?(back\s+)?the\s+(difference|extra|rest)"
        r"|多付了|退(我)?差价|把多的(钱)?(转|退)", re.I),
     "Overpayment and a request to send money back",
     "A classic scam: the extra payment is reversed later and the money sent back is gone. "
     "Refund through PayPal only.",
     "seller_scams", "seller"),
]

_DUTIES = re.compile(r"\bduties\b|\bduty\b|customs|tariff|import\s+tax|\bvat\b|\bddp\b|\bdap\b|\bddu\b|关税|清关|进口税|税费", re.I)

COUNTRIES = {
    "US": r"(?-i:\bUS\b)|\bu\.s\.(a\.)?|\busa\b|united\s+states|美国",
    "CA": r"\bcanada\b|加拿大",
    "GB": r"(?-i:\bUK\b)|\bu\.k\.|united\s+kingdom|britain|england|英国",
    "JP": r"\bjapan\b|日本",
    "AU": r"\baustralia\b|澳大利亚|澳洲",
    "CN": r"\bchina\b|中国",
    "HK": r"hong\s*kong|香港",
    "TW": r"\btaiwan\b|台湾",
    "DE": r"\bgermany\b|德国",
    "FR": r"\bfrance\b|法国",
    "MX": r"\bmexico\b|墨西哥",
    "KR": r"\bkorea\b|韩国",
}
_SHIP_CONTEXT = re.compile(r"ship|shipping|deliver|mail|post|send|运|邮|寄", re.I)
_DOMESTIC = re.compile(r"domestic|within\s+the\s+(us|u\.s\.|states|country)|(?-i:\bUS\s+only\b)|lower\s*48|只发美国", re.I)


def chat_flags(messages: list[Message]) -> list[Flag]:
    out = []
    for code, sev, pat, title, why, src, protects in _CHAT_PATTERNS:
        for m in messages:
            hit = pat.search(m.text)
            if hit:
                out.append(Flag(code, sev, title, why, m.index, _quote_around(m.text, hit), SOURCES[src], protects))
                break
    return out


def agreed_destinations(messages: list[Message], seller_country: str) -> tuple[set[str], tuple[int, str] | None]:
    """Countries the chat tied shipping to, with the quote that did it."""
    found: set[str] = set()
    where = None
    for m in messages:
        if not _SHIP_CONTEXT.search(m.text):
            continue
        if dm := _DOMESTIC.search(m.text):
            found.add(seller_country)
            where = where or (m.index, _quote_around(m.text, dm))
        for code, pat in COUNTRIES.items():
            for cm in re.finditer(pat, m.text, re.I):
                window = m.text[max(0, cm.start() - 30): cm.end() + 30]
                if _SHIP_CONTEXT.search(window):
                    found.add(code)
                    where = where or (m.index, _quote_around(m.text, cm))
    return found, where


def duties_discussed(messages: list[Message]) -> tuple[int, str] | None:
    for m in messages:
        if hit := _DUTIES.search(m.text):
            return m.index, _quote_around(m.text, hit)
    return None


def _quote_around(text: str, match: re.Match) -> str:
    """A readable span around the hit that is still an exact substring of the message."""
    start = max(0, text.rfind(" ", 0, max(0, match.start() - 20)) + 1)
    end = text.find(" ", min(len(text), match.end() + 20))
    return text[start: len(text) if end == -1 else end].strip()


# ------------------------------------------------------------- order address

def ship_to(order: dict) -> dict | None:
    """Only what checks and receipts need: no street lines, no name."""
    pu = (order.get("purchase_units") or [{}])[0]
    addr = ((pu.get("shipping") or {}).get("address")) or {}
    if not addr.get("country_code"):
        return None
    return {"country_code": addr["country_code"].upper(), "postal_code": normalize_postal(addr.get("postal_code", ""), addr["country_code"]),
            "city": addr.get("admin_area_2"), "region": addr.get("admin_area_1")}


def normalize_postal(code: str, country: str) -> str:
    code = re.sub(r"[\s-]", "", str(code or "")).upper()
    if country.upper() == "US":
        code = code[:5]
    return code


def payment_flags(messages: list[Message], order: dict, *, seller_country: str) -> list[Flag]:
    """Checks that need PayPal's ship-to address, i.e. after the payer approved on PayPal."""
    flags: list[Flag] = []
    dest = ship_to(order)
    if dest is None:
        flags.append(Flag("NO_SHIP_TO", WARN, "PayPal has no shipping address for this order",
                          "Seller Protection needs proof of delivery to the address on the transaction. "
                          "Without one, an 'item not received' claim is hard to defend.",
                          source=SOURCES["seller_protection"], protects="seller"))
        return flags
    agreed, where = agreed_destinations(messages, seller_country)
    if agreed and dest["country_code"] not in agreed:
        flags.append(Flag("DESTINATION_MISMATCH", BLOCK,
                          f"Shipping was agreed for {', '.join(sorted(agreed))}; PayPal says {dest['country_code']}",
                          "The agreed shipping price doesn't cover this destination. The seller has to re-agree "
                          "shipping with the buyer before the payment is taken.",
                          where[0] if where else None, where[1] if where else None, protects="seller"))
    if dest["country_code"] != seller_country:
        said = duties_discussed(messages)
        if said is None:
            extra = (" The US suspended its duty-free de minimis exemption on August 29, 2025, so low-value parcels "
                     "into the US can owe duties." if dest["country_code"] == "US" else "")
            flags.append(Flag("DUTIES_NOT_DISCUSSED", WARN,
                              f"International parcel ({seller_country} → {dest['country_code']}): nobody said who pays import duties",
                              "If the seller doesn't prepay duties (DDP), the buyer may get a bill from the carrier "
                              "on delivery (DAP) — a common reason parcels are refused." + extra,
                              source=SOURCES["de_minimis"], protects="both"))
        else:
            flags.append(Flag("DUTIES_DISCUSSED", INFO, "Import duties were discussed in the chat",
                              "Recorded in the receipt.", said[0], said[1], protects="both"))
    return flags


# ---------------------------------------------------------------- shipping

DEFAULT_LIABILITY = {"UPS": Decimal("100")}   # confirmed from the source; other carriers: ask the carrier


def ship_flags(*, ship_to_addr: dict | None, label_country: str, label_postal: str, carrier: str,
               item_value: Decimal, declared_value: Decimal | None) -> list[Flag]:
    flags: list[Flag] = []
    if ship_to_addr:
        want_c, want_p = ship_to_addr["country_code"], ship_to_addr["postal_code"]
        got_c = (label_country or "").strip().upper()
        got_p = normalize_postal(label_postal, got_c or want_c)
        if got_c != want_c or (want_p and got_p != want_p):
            flags.append(Flag("LABEL_ADDRESS_MISMATCH", BLOCK,
                              f"The label goes to {got_c or '?'} {got_p or '?'}, PayPal's address is {want_c} {want_p}",
                              "Seller Protection requires shipping to the address on the PayPal transaction. "
                              "Fix the label, or ask the buyer to change the address in PayPal and pay again.",
                              source=SOURCES["seller_protection"], protects="seller"))
    cap = DEFAULT_LIABILITY.get(carrier.upper())
    covered = declared_value if declared_value is not None else cap
    if cap is not None and item_value > (covered or 0):
        flags.append(Flag("OVER_CARRIER_LIABILITY", WARN,
                          f"{carrier.upper()} covers ${covered} by default; this item is worth ${item_value}",
                          "Declare a higher value when you buy the label, or the carrier won't pay the difference if it's lost. "
                          "Claims need proof of value, packaging photos and tracking, filed within 60 days.",
                          source=SOURCES["ups_declared_value"], protects="seller"))
    elif cap is None and declared_value is None and item_value > 100:
        flags.append(Flag("CHECK_CARRIER_LIABILITY", INFO,
                          f"Check {carrier.upper()}'s default liability for a ${item_value} item",
                          "Carriers cap what they pay for lost parcels unless you declare a higher value.",
                          protects="seller"))
    return flags


def blocking(flags: list[Flag]) -> list[Flag]:
    return [f for f in flags if f.severity == BLOCK]
