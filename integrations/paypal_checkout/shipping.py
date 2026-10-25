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
from pathlib import Path

from callgate.receipt import canonical

# Magic numbers for the image types phones produce.
_IMAGE_SIGNATURES = [
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"RIFF", "image/webp"),
]
MAX_PHOTO_BYTES = 8 * 1024 * 1024
CARRIERS = {"USPS", "UPS", "FEDEX", "DHL", "CANADA_POST", "ROYAL_MAIL", "AUSTRALIA_POST", "OTHER"}


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


def tracking_body(capture_id: str, tracking_number: str, carrier: str, item_name: str | None) -> dict:
    tracking_number = tracking_number.strip()
    if not re.fullmatch(r"[A-Za-z0-9-]{4,64}", tracking_number):
        raise ValueError("tracking number must be 4-64 letters, digits or dashes")
    carrier = carrier.strip().upper()
    body = {"capture_id": capture_id, "tracking_number": tracking_number, "notify_payer": True}
    if carrier in CARRIERS and carrier != "OTHER":
        body["carrier"] = carrier
    else:
        body["carrier"] = "OTHER"
        body["carrier_name_other"] = (carrier.title() if carrier not in CARRIERS else "Other")[:64]
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
