"""Provenance passport: a signed, hash-linked history that travels with an item between resellers.

Resale goods often pass through several hands — a store in Tokyo, a proxy
buyer, a reseller in Los Angeles, a buyer in Toronto.  Each hand knows a piece
of where the item came from and none of them can see the rest.  A passport is
a list of entries, one per event, where each entry:

  * names the holder, where and when, and what they observed (serial numbers,
    receipt and tag photos stored as SHA-256 only),
  * includes the hash of the previous entry (so nothing earlier can be edited
    or removed without breaking every later link), and
  * is signed with the recording holder's Ed25519 key.

The next seller imports the passport, verifies every link and signature, and
appends their own entry.  The buyer sees the whole chain before paying.

What it proves: who recorded what, in what order, and that nobody changed it
afterwards.  What it does not prove: that a receipt is genuine or an item is
authentic.  The page says so.
"""
from __future__ import annotations

import hashlib
import re
import secrets
from datetime import date

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

from callgate.receipt import canonical

VERSION = "callgate-provenance-v1"
EVENTS = {"acquired", "inspected", "listed", "sold", "note"}
MAX_ENTRIES = 50


def entry_hash(envelope: dict) -> str:
    return hashlib.sha256(canonical(envelope)).hexdigest()


def key_id(public_hex: str) -> str:
    return hashlib.sha256(bytes.fromhex(public_hex)).hexdigest()[:12]


def _clean(text, limit):
    return re.sub(r"\s+", " ", str(text or "")).strip()[:limit]


def make_entry(chain: list[dict], key: Ed25519PrivateKey, *, event: str, holder: str, where: str = "",
               when: str | None = None, serials: list[str] | None = None, evidence: list[dict] | None = None,
               note: str = "", recorded_at: int) -> dict:
    if event not in EVENTS:
        raise ValueError(f"event must be one of {sorted(EVENTS)}")
    if len(chain) >= MAX_ENTRIES:
        raise ValueError("passport is full")
    holder = _clean(holder, 60)
    if not holder:
        raise ValueError("say who is recording this (a shop or seller name)")
    if when:
        try:
            date.fromisoformat(when)
        except ValueError:
            raise ValueError("date must be YYYY-MM-DD") from None
    prev = chain[-1] if chain else None
    entry = {
        "v": VERSION,
        "item_id": prev["entry"]["item_id"] if prev else "itm_" + secrets.token_hex(8),
        "seq": len(chain),
        "prev": entry_hash(prev) if prev else None,
        "event": event, "holder": holder, "where": _clean(where, 120), "when": when,
        "serials": [_clean(s, 60) for s in (serials or []) if _clean(s, 60)][:10],
        "evidence": [{"kind": _clean(e.get("kind", "photo"), 20), "sha256": e["sha256"],
                      "content_type": e.get("content_type")} for e in (evidence or [])][:10],
        "note": _clean(note, 300),
        "recorded_at": recorded_at,
        "signer": key.public_key().public_bytes_raw().hex(),
    }
    return {"entry": entry, "signature": key.sign(canonical(entry)).hex()}


def verify_chain(chain: list[dict]) -> dict:
    """Check every signature and link.  Returns per-entry status so the page can show where a break is."""
    problems, rows = [], []
    if not isinstance(chain, list) or not chain:
        return {"ok": False, "problems": ["empty passport"], "entries": [], "holders": 0}
    if len(chain) > MAX_ENTRIES:
        return {"ok": False, "problems": ["passport too long"], "entries": [], "holders": 0}
    item_id = None
    for i, env in enumerate(chain):
        status = "ok"
        try:
            e = env["entry"]
            if e.get("v") != VERSION:
                raise ValueError("unknown version")
            Ed25519PublicKey.from_public_bytes(bytes.fromhex(e["signer"])).verify(
                bytes.fromhex(env["signature"]), canonical(e))
            if e["seq"] != i:
                raise ValueError(f"entry {i + 1} is out of order")
            if i == 0:
                item_id = e["item_id"]
                if e["prev"] is not None:
                    raise ValueError("first entry must not point backwards")
            else:
                if e["item_id"] != item_id:
                    raise ValueError(f"entry {i + 1} belongs to a different item")
                if e["prev"] != entry_hash(chain[i - 1]):
                    raise ValueError(f"entry {i + 1} does not link to entry {i}: something before it was changed")
        except InvalidSignature:
            status = "bad signature"
            problems.append(f"entry {i + 1}: signature does not verify — it was edited after signing")
        except (KeyError, TypeError, ValueError) as exc:
            status = "broken"
            problems.append(f"entry {i + 1}: {exc}")
        e = env.get("entry", {}) if isinstance(env, dict) else {}
        rows.append({"seq": i, "status": status, "event": e.get("event"), "holder": e.get("holder"),
                     "where": e.get("where"), "when": e.get("when"), "serials": e.get("serials", []),
                     "evidence": e.get("evidence", []), "note": e.get("note"),
                     "signer": key_id(e["signer"]) if isinstance(e.get("signer"), str) and len(e["signer"]) == 64 else None})
    return {"ok": not problems, "problems": problems, "entries": rows, "item_id": item_id,
            "holders": len({r["signer"] for r in rows if r["signer"]}),
            "note": "Shows who recorded what and that nothing was changed afterwards. It does not prove authenticity."}


def find_photo(chain: list[dict], sha256: str) -> list[int]:
    return [i for i, env in enumerate(chain) for ev in env["entry"].get("evidence", []) if ev.get("sha256") == sha256]
