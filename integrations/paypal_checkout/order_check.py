"""Compare a PayPal order with the agreed terms, and fingerprint the parts that matter.

The fingerprint covers what changes what the payer pays or receives: amounts,
breakdown, items, payee and intent.  It deliberately excludes `status`, so the
same order keeps the same fingerprint as it moves CREATED -> APPROVED, but any
PATCH to the amount or items produces a new one.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, asdict
from decimal import Decimal

from callgate.receipt import canonical

from .terms import AgreedTerms, money, money_str

BLOCK, WARN, INFO = "block", "warn", "info"


@dataclass(frozen=True)
class Difference:
    field: str
    agreed: str | None
    order: str | None
    severity: str
    why: str
    evidence: list[dict]

    def to_dict(self):
        return asdict(self)


def _amt(obj, currency) -> Decimal | None:
    if not obj:
        return None
    return money(obj["value"], obj.get("currency_code", currency))


def order_fingerprint(order: dict) -> str:
    units = []
    for pu in order.get("purchase_units", []):
        amount = pu.get("amount", {})
        units.append({
            "reference_id": pu.get("reference_id", "default"),
            "custom_id": pu.get("custom_id"),
            "currency": amount.get("currency_code"),
            "value": amount.get("value"),
            "breakdown": amount.get("breakdown", {}),
            "items": [{"name": i.get("name"), "quantity": str(i.get("quantity")),
                       "unit_amount": i.get("unit_amount")} for i in pu.get("items", [])],
            "payee": pu.get("payee", {}),
        })
    body = {"id": order.get("id"), "intent": order.get("intent"), "purchase_units": units}
    return hashlib.sha256(canonical(body)).hexdigest()


def _tokens(s: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]+|[一-鿿]", s.lower()) if len(t) > 1 or not t.isascii()}


def _name_match(a: str, b: str) -> bool:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return False
    return len(ta & tb) / min(len(ta), len(tb)) >= 0.5


def compare(terms: AgreedTerms, order: dict) -> list[Difference]:
    diffs: list[Difference] = []

    def ev(f):
        return [] if f is None else [e.to_dict() for e in f.evidence]

    units = order.get("purchase_units") or []
    if len(units) != 1:
        return [Difference("purchase_units", "1", str(len(units)), BLOCK,
                           "Only single-purchase-unit orders can be checked", [])]
    pu = units[0]
    amount = pu.get("amount") or {}
    if order.get("intent") not in ("CAPTURE", "AUTHORIZE"):
        diffs.append(Difference("intent", "CAPTURE", order.get("intent"), BLOCK, "Unknown order intent", []))

    if not terms.ready():
        diffs.append(Difference("terms", None, None, BLOCK,
                                "Agreed price, currency or the other person's 'yes' is not confirmed yet", []))
        return diffs

    cur = terms.currency.value
    order_cur = amount.get("currency_code")
    if order_cur != cur:
        diffs.append(Difference("currency", cur, order_cur, BLOCK,
                                "The order charges in a different currency than you agreed", ev(terms.currency)))
        return diffs

    agreed_total = money(terms.total.value, cur)
    order_total = _amt(amount, cur)
    if order_total != agreed_total:
        diffs.append(Difference("total", money_str(agreed_total), money_str(order_total), BLOCK,
                                "The amount to pay is not what was agreed in the chat", ev(terms.total)))

    bd = amount.get("breakdown") or {}
    if terms.shipping is not None:
        agreed_ship = money(terms.shipping.value, cur)
        order_ship = _amt(bd.get("shipping"), cur) or money(0, cur)
        if order_ship != agreed_ship:
            diffs.append(Difference("shipping", money_str(agreed_ship), money_str(order_ship), BLOCK,
                                    "Shipping differs from what was agreed", ev(terms.shipping)))
    else:
        order_ship = _amt(bd.get("shipping"), cur)
        if order_ship:
            diffs.append(Difference("shipping", "not discussed", money_str(order_ship), WARN,
                                    "The order lists shipping that the chat never mentioned (total is unchanged)", []))
    for extra in ("handling", "insurance", "tax_total"):
        v = _amt(bd.get(extra), cur)
        if v and v > 0:
            diffs.append(Difference(extra, "0", money_str(v), BLOCK,
                                    f"The order adds a {extra.replace('_', ' ')} charge that was never discussed", []))

    order_items = pu.get("items") or []
    matched: set[int] = set()
    for item in terms.items:
        hit = next((i for i, oi in enumerate(order_items)
                    if i not in matched and _name_match(item.name.value, oi.get("name", ""))), None)
        if hit is None:
            diffs.append(Difference(f"item:{item.name.value}", item.name.value, None, WARN,
                                    "An agreed item does not appear by name in the order", ev(item.name)))
            continue
        matched.add(hit)
        oi = order_items[hit]
        if str(oi.get("quantity")) != item.quantity.value:
            diffs.append(Difference(f"quantity:{item.name.value}", item.quantity.value, str(oi.get("quantity")),
                                    BLOCK, "Quantity differs from what was agreed", ev(item.quantity)))
        if item.unit_amount is not None and oi.get("unit_amount"):
            if _amt(oi["unit_amount"], cur) != money(item.unit_amount.value, cur):
                diffs.append(Difference(f"unit_price:{item.name.value}", item.unit_amount.value,
                                        oi["unit_amount"]["value"], BLOCK,
                                        "Item price differs from what was agreed", ev(item.unit_amount)))
    if terms.items:
        for i, oi in enumerate(order_items):
            if i not in matched and (_amt(oi.get("unit_amount"), cur) or 0) > 0:
                diffs.append(Difference(f"extra_item:{oi.get('name')}", None, oi.get("name"), BLOCK,
                                        "The order contains a paid item nobody agreed to", []))
    for inc in terms.inclusions:
        diffs.append(Difference(f"included:{inc.value}", inc.value, None, INFO,
                                "PayPal cannot check this; it is recorded in the signed receipt", ev(inc)))
    return diffs


def blocking(diffs: list[Difference]) -> list[Difference]:
    return [d for d in diffs if d.severity == BLOCK]


def order_from_terms(terms: AgreedTerms, *, checkout_id: str, title: str | None = None) -> dict:
    """The order CallGate itself would create: built only from confirmed terms."""
    if not terms.ready():
        raise ValueError("terms are not confirmed")
    cur = terms.currency.value
    total = money(terms.total.value, cur)
    ship = money(terms.shipping.value, cur) if terms.shipping else money(0, cur)
    item_total = total - ship
    if item_total < 0:
        raise ValueError("shipping exceeds total")
    desc_parts = [i.value for i in terms.inclusions]
    name = (title or (terms.items[0].name.value if terms.items else "Agreed purchase"))[:127]
    qty = terms.items[0].quantity.value if len(terms.items) == 1 else "1"
    unit = item_total / int(qty)
    if money(unit, cur) * int(qty) != item_total:
        qty, unit = "1", item_total     # never round a price to make quantities fit
    return {
        "intent": "CAPTURE",
        "purchase_units": [{
            "reference_id": "default",
            "custom_id": checkout_id,
            "description": ("Agreed in chat. Includes: " + ", ".join(desc_parts))[:127] if desc_parts else "Agreed in chat",
            "amount": {"currency_code": cur, "value": money_str(total),
                       "breakdown": {"item_total": {"currency_code": cur, "value": money_str(item_total)},
                                     "shipping": {"currency_code": cur, "value": money_str(ship)}}},
            "items": [{"name": name, "quantity": qty,
                       "unit_amount": {"currency_code": cur, "value": money_str(money(unit, cur))}}],
        }],
    }
