"""Agreed terms: what both people said in the chat, each field tied to its source quote.

A field is only *grounded* when its quote is an exact substring of the cited
message and, for money, the quote actually contains that amount.  Anything the
extractor cannot ground is dropped and reported, never silently kept.  This is
the "refuse to guess" rule: a model can propose, but only text the user can see
in their own chat can become a term.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field, asdict
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from callgate.receipt import canonical

# ISO 4217 minor units for the currencies PayPal commonly settles; default 2.
ZERO_DECIMAL = {"JPY", "HUF", "TWD"}
SUPPORTED_CURRENCIES = {"USD", "CAD", "EUR", "GBP", "AUD", "JPY", "CNY", "HKD", "TWD", "SGD", "MXN"}


def money(value, currency: str) -> Decimal:
    """Exact decimal amount in the currency's minor-unit precision; never float."""
    try:
        d = Decimal(str(value).replace(",", ""))
    except (InvalidOperation, ValueError):
        raise ValueError(f"not an amount: {value!r}") from None
    if not d.is_finite() or d < 0:
        raise ValueError(f"amount must be finite and non-negative: {value!r}")
    exp = Decimal("1") if currency in ZERO_DECIMAL else Decimal("0.01")
    return d.quantize(exp, rounding=ROUND_HALF_UP)


def money_str(d: Decimal) -> str:
    return format(d, "f")


@dataclass(frozen=True)
class Message:
    index: int
    sender: str
    text: str


@dataclass(frozen=True)
class Evidence:
    message_index: int
    quote: str

    def to_dict(self):
        return asdict(self)


@dataclass
class Field:
    """One agreed value plus the exact words that support it."""
    value: str
    evidence: list[Evidence]
    source: str                  # "rules" | "model" | "both" | "human"

    def to_dict(self):
        return {"value": self.value, "source": self.source,
                "evidence": [e.to_dict() for e in self.evidence]}


@dataclass
class Item:
    name: Field
    quantity: Field
    unit_amount: Field | None = None

    def to_dict(self):
        return {"name": self.name.to_dict(), "quantity": self.quantity.to_dict(),
                "unit_amount": None if self.unit_amount is None else self.unit_amount.to_dict()}


@dataclass
class AgreedTerms:
    currency: Field | None
    total: Field | None              # what the payer agreed to pay, including shipping
    shipping: Field | None = None
    items: list[Item] = field(default_factory=list)
    inclusions: list[Field] = field(default_factory=list)   # "with original box", "extra laces"
    acceptance: Field | None = None  # the message where the other side said yes
    unresolved: list[str] = field(default_factory=list)     # why something could not be grounded

    def to_dict(self):
        def f(x):
            return None if x is None else x.to_dict()
        return {"currency": f(self.currency), "total": f(self.total), "shipping": f(self.shipping),
                "items": [i.to_dict() for i in self.items],
                "inclusions": [i.to_dict() for i in self.inclusions],
                "acceptance": f(self.acceptance), "unresolved": list(self.unresolved)}

    def ready(self) -> bool:
        """Payment can only be proposed when the core money terms are grounded."""
        return self.currency is not None and self.total is not None and self.acceptance is not None

    def commitment(self) -> str:
        """Hash of what a person confirms: values and their quotes, not the extractor's identity."""
        body = self.to_dict()
        body.pop("unresolved")
        for key in ("currency", "total", "shipping", "acceptance"):
            if body[key]:
                body[key].pop("source")
        for item in body["items"]:
            for k in ("name", "quantity", "unit_amount"):
                if item[k]:
                    item[k].pop("source")
        for inc in body["inclusions"]:
            inc.pop("source")
        return hashlib.sha256(canonical(body)).hexdigest()


_NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")


def quote_is_grounded(messages: list[Message], ev: Evidence) -> bool:
    if not (0 <= ev.message_index < len(messages)):
        return False
    q = ev.quote.strip()
    return bool(q) and len(q) <= 400 and q in messages[ev.message_index].text


def quote_contains_amount(quote: str, amount: Decimal) -> bool:
    for m in _NUM.finditer(quote):
        try:
            if Decimal(m.group(0).replace(",", "")) == amount:
                return True
        except InvalidOperation:
            continue
    return False


def quote_supports_total(quote: str, amount: Decimal) -> bool:
    """A total is supported when stated outright or when it is the sum of the quoted numbers ("$95 plus $8")."""
    if quote_contains_amount(quote, amount):
        return True
    nums = []
    for m in _NUM.finditer(quote):
        try:
            nums.append(Decimal(m.group(0).replace(",", "")))
        except InvalidOperation:
            return False
    return len(nums) >= 2 and sum(nums) == amount


_LINE = re.compile(r"^\s*(?:\[[^\]]{0,40}\]\s*)?([^:：\n]{1,40}?)\s*[:：]\s*(.+?)\s*$")


def parse_chat(raw: str | list[dict]) -> list[Message]:
    """Accept 'Name: text' lines or a list of {sender, text}; continuation lines join the previous message."""
    if isinstance(raw, list):
        out = []
        for i, m in enumerate(raw):
            sender, text = str(m.get("sender", "unknown"))[:40], str(m.get("text", ""))
            if len(text) > 4000:
                raise ValueError("message too long")
            out.append(Message(i, sender, text))
        return out
    msgs: list[Message] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        m = _LINE.match(line)
        if m:
            msgs.append(Message(len(msgs), m.group(1).strip(), m.group(2)))
        elif msgs:
            last = msgs[-1]
            msgs[-1] = Message(last.index, last.sender, last.text + "\n" + line.strip())
        else:
            msgs.append(Message(0, "unknown", line.strip()))
    if len(msgs) > 300:
        raise ValueError("chat too long; paste the part where the deal was made")
    return msgs


def _field_from(d: dict | None) -> Field | None:
    if d is None:
        return None
    return Field(str(d["value"]), [Evidence(int(e["message_index"]), str(e["quote"])) for e in d["evidence"]],
                 str(d.get("source", "human")))


def terms_from_dict(d: dict) -> AgreedTerms:
    items = [Item(_field_from(i["name"]), _field_from(i["quantity"]), _field_from(i.get("unit_amount")))
             for i in d.get("items", [])]
    return AgreedTerms(_field_from(d.get("currency")), _field_from(d.get("total")), _field_from(d.get("shipping")),
                       items, [_field_from(i) for i in d.get("inclusions", [])], _field_from(d.get("acceptance")),
                       list(d.get("unresolved", [])))


def ground_terms(terms: AgreedTerms, messages: list[Message]) -> list[str]:
    """Re-check every quote against the chat. Used when a person edits or resolves terms."""
    problems = []
    fields = [("currency", terms.currency), ("total", terms.total), ("shipping", terms.shipping),
              ("acceptance", terms.acceptance)]
    fields += [(f"inclusion {i.value}", i) for i in terms.inclusions]
    for it in terms.items:
        fields += [(f"item {it.name.value}", it.name), (f"quantity {it.name.value}", it.quantity)]
        if it.unit_amount:
            fields.append((f"price {it.name.value}", it.unit_amount))
    for name, f in fields:
        if f is None:
            continue
        if not f.evidence:
            problems.append(f"{name}: no quote")
        for ev in f.evidence:
            if not quote_is_grounded(messages, ev):
                problems.append(f"{name}: quote '{ev.quote[:40]}' is not in message {ev.message_index + 1}")
    if terms.total is not None and terms.currency is not None:
        amt = money(terms.total.value, terms.currency.value)
        quotes = [e.quote for e in terms.total.evidence]
        nums = []
        for q in quotes:
            nums += [Decimal(m.group(0).replace(",", "")) for m in _NUM.finditer(q)]
        if not any(quote_contains_amount(q, amt) for q in quotes) and sum(nums) != amt:
            problems.append(f"total: {terms.total.value} is neither stated in nor the sum of its quotes")
    return problems
