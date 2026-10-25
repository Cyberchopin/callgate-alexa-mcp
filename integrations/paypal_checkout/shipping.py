"""After the payment: pack what was agreed, prove it, and hand PayPal the tracking.

The packing checklist comes from the same confirmed terms the payment was
checked against, so "comes with the original box" in the chat becomes "photo of
the original box" on the checklist.  Photos are stored by SHA-256; the hashes go
into the signed receipt and into the dispute evidence pack.

What this proves: these exact photos existed when the seller marked the order
shipped, tied to this agreement and this capture.  What it does not prove: that
the photo shows the item that went into the box.
"""
from __future__ import annotations

import hashlib
import re
from decimal import Decimal
from pathlib import Path

from callgate.receipt import canonical

# Magic numbers for the image types phones produce.
_IMAGE_SIGNATURES = [
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"RIFF", "image/webp"),
]
MAX_PHOTO_BYTES = 8 * 1024 * 1024
# What sellers type -> PayPal Add Tracking carrier code (developer.paypal.com/track-orders/carriers).
# Only codes we confirmed in PayPal's list or examples; anything else is sent as OTHER with its name.
CARRIERS = {
    "USPS": "USPS", "UPS": "UPS", "FEDEX": "FEDEX", "DHL": "DHL",
    "CANADA_POST": "CA_CANADA_POST", "AUSTRALIA_POST": "AU_AU_POST", "JAPAN_POST": "JPN_JAPAN_POST",
    "YAMATO": "YAMATO", "SAGAWA": "SAGAWA", "CHINA_POST": "CN_CHINA_POST_EMS", "EMS": "EMS",
    "YUNEXPRESS": "YUNEXPRESS", "HK_POST": "HK_POST",
}
CARRIER_LABELS = {"USPS": "USPS", "UPS": "UPS", "FEDEX": "FedEx", "DHL": "DHL", "CANADA_POST": "Canada Post",
                  "AUSTRALIA_POST": "Australia Post", "JAPAN_POST": "Japan Post", "YAMATO": "Yamato",
                  "SAGAWA": "Sagawa", "CHINA_POST": "China Post", "EMS": "EMS", "YUNEXPRESS": "YunExpress",
                  "HK_POST": "Hongkong Post"}


def checklist(terms: dict, title: str | None = None) -> list[dict]:
    """One line per thing the buyer was promised, plus the packing shot."""
    item = (terms.get("items") or [{}])[0].get("name", {}).get("value") if terms.get("items") else None
    lines = [{"id": "item", "label": f"The item: {item or title or 'what was agreed'}",
              "why": "Shows what was sent", "quote": None}]
    seen = set()
    for inc in terms.get("inclusions", []):
        key = re.sub(r"[^a-z0-9一-鿿]+", "-", inc["value"].lower()).strip("-")[:40] or "included"
        if key in seen:
            continue
        seen.add(key)
        lines.append({"id": f"inc-{key}", "label": f"Included: {inc['value']}",
                      "why": "The chat promised it", "quote": inc["evidence"][0]["quote"]})
    lines.append({"id": "packed", "label": "Everything in the box, before sealing",
                  "why": "Shows it left complete", "quote": None})
    lines.append({"id": "carrier_receipt", "label": "Carrier counter receipt or label with weight",
                  "why": "The weight the carrier accepted is the best answer to 'the box was empty'", "quote": None})
    return lines


def sniff_image(data: bytes) -> str | None:
    for sig, mime in _IMAGE_SIGNATURES:
        if data.startswith(sig) and (mime != "image/webp" or data[8:12] == b"WEBP"):
            return mime
    if data[4:12] in (b"ftypheic", b"ftypheix", b"ftypmif1"):
        return "image/heic"
    return None


def store_photo(root: Path, data: bytes) -> dict:
    if not data or len(data) > MAX_PHOTO_BYTES:
        raise ValueError("photo must be 1 byte to 8 MB")
    mime = sniff_image(data)
    if mime is None:
        raise ValueError("only JPEG, PNG, WebP or HEIC photos")
    digest = hashlib.sha256(data).hexdigest()
    root.mkdir(parents=True, exist_ok=True)
    path = root / digest
    if not path.exists():
        tmp = root / (digest + ".tmp")
        tmp.write_bytes(data)
        tmp.replace(path)
    return {"sha256": digest, "bytes": len(data), "content_type": mime}


_UNITS = {"oz": Decimal("0.0283495"), "lb": Decimal("0.453592"), "g": Decimal("0.001"), "kg": Decimal("1")}


def parse_weight(value: str, unit: str) -> dict:
    """Packed weight as weighed by the seller; kept in the unit they used plus kilograms."""
    unit = (unit or "").strip().lower()
    try:
        v = Decimal(str(value).strip())
    except ArithmeticError:
        raise ValueError("packed weight must be a number") from None
    if unit not in _UNITS or not v.is_finite() or v <= 0:
        raise ValueError("packed weight is required (oz, lb, g or kg)")
    kg = (v * _UNITS[unit]).quantize(Decimal("0.001"))
    if kg > 70:
        raise ValueError("packed weight over 70 kg; check the unit")
    return {"value": str(v), "unit": unit, "kg": str(kg)}


def parse_money(value: str) -> Decimal:
    try:
        d = Decimal(str(value).replace(",", "").replace("$", "").strip())
    except ArithmeticError:
        raise ValueError("declared value must be an amount") from None
    if not d.is_finite() or d < 0:
        raise ValueError("declared value must be an amount")
    return d.quantize(Decimal("0.01"))


def tracking_body(capture_id: str, tracking_number: str, carrier: str, item_name: str | None) -> dict:
    tracking_number = tracking_number.strip()
    if not re.fullmatch(r"[A-Za-z0-9-]{4,64}", tracking_number):
        raise ValueError("tracking number must be 4-64 letters, digits or dashes")
    typed = re.sub(r"[\s-]+", "_", carrier.strip()).upper()
    body = {"capture_id": capture_id, "tracking_number": tracking_number, "notify_payer": True}
    code = CARRIERS.get(typed) or (typed if typed in CARRIERS.values() else None)
    if code:
        body["carrier"] = code
    else:
        name = re.sub(r"\s+", " ", carrier).strip()[:64]
        if not name or typed == "OTHER":
            raise ValueError("type the carrier's name")
        body["carrier"] = "OTHER"
        body["carrier_name_other"] = name if not name.isupper() else name.title()
    if item_name:
        body["items"] = [{"name": item_name[:127], "quantity": "1"}]
    return body


def evidence_input(co: dict, receipt: dict) -> dict:
    """The JSON part of PayPal's provide-evidence call (documents are attached separately)."""
    d = co["data"]
    t = d["terms"]
    ship = d.get("shipment") or {}
    total = (t.get("total") or {})
    quotes = "; ".join(f"message {e['message_index'] + 1}: \"{e['quote']}\"" for e in total.get("evidence", []))
    accept = (t.get("acceptance") or {}).get("evidence", [{}])[0]
    lines = [
        f"Agreed in chat: {total.get('value')} {(t.get('currency') or {}).get('value')} ({quotes}).",
        f"Accepted by {(t.get('acceptance') or {}).get('value')} in message {accept.get('message_index', 0) + 1}: \"{accept.get('quote')}\".",
        f"Payer confirmed PayPal order {d.get('order_id')} before paying; capture {d.get('capture_id')}.",
    ]
    photos = d.get("photos", {})
    for line in d.get("checklist", []):
        p = photos.get(line["id"])
        lines.append(f"{line['label']}: " + (f"photo sha256 {p['sha256'][:16]}… taken before shipping" if p
                                             else f"not photographed ({(d.get('skipped') or {}).get(line['id'], 'no reason given')})"))
    if ship.get("packed_weight"):
        w = ship["packed_weight"]
        lines.append(f"Packed weight recorded before shipping: {w['value']} {w['unit']} ({w['kg']} kg).")
    if ship.get("label_destination") and d.get("ship_to"):
        lines.append(f"Label destination {ship['label_destination']['country_code']} {ship['label_destination']['postal_code']} "
                     f"matches the PayPal ship-to address.")
    chain = (d.get("provenance") or {}).get("chain") or []
    if chain:
        from .provenance import entry_hash, verify_chain
        v = verify_chain(chain)
        lines.append(f"Provenance passport: {len(chain)} signed entries from {v['holders']} holder(s), "
                     f"{'all links intact' if v['ok'] else 'ALTERED'}; head {entry_hash(chain[-1])[:16]}….")
    if d.get("destination_override"):
        lines.append(f"Shipped to {d['destination_override']['country_code']} after the seller re-agreed: "
                     f"\"{d['destination_override']['reason']}\".")
    ack = d.get("buyer_ack")
    if ack:
        lines.append("Payer confirmed it arrived as described." if ack["as_described"]
                     else f"Payer reported: {ack['note']}")
    lines.append(f"Signed receipt sha256 {hashlib.sha256(canonical(receipt['payload'])).hexdigest()[:16]}…")
    evidences = []
    if ship:
        evidences.append({"evidence_type": "PROOF_OF_FULFILLMENT",
                          "evidence_info": {"tracking_info": [{"carrier_name": ship.get("carrier_name_other") or ship["carrier"],
                                                               "tracking_number": ship["tracking_number"]}]},
                          "notes": "\n".join(lines)[:2000]})
    else:
        evidences.append({"evidence_type": "OTHER", "notes": "\n".join(lines)[:2000]})
    return {"evidences": evidences}
