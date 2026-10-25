"""Durable checkout state: one SQLite file, explicit transitions, idempotency keys.

Every state change is a compare-and-set on (id, state, version) inside
BEGIN IMMEDIATE, so two concurrent clicks cannot both move a checkout forward.
The CAPTURING state is written *before* PayPal is called; if the process dies
or the network times out, the row says "we may have captured" and the
reconciler finds out, instead of trying again blindly.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from contextlib import closing
from pathlib import Path

DRAFT = "DRAFT"                        # chat pasted, terms extracted, not yet confirmed
TERMS_CONFIRMED = "TERMS_CONFIRMED"    # a person confirmed the terms (and any conflicts)
ORDER_ATTACHED = "ORDER_ATTACHED"      # a PayPal order exists and is being checked
MISMATCH = "MISMATCH"                  # order differs from terms; must be fixed or rebuilt
READY = "READY"                        # order matches; waiting for the payer's confirmation
BUYER_CONFIRMED = "BUYER_CONFIRMED"    # payer confirmed this exact order version
ORDER_CHANGED = "ORDER_CHANGED"        # order was modified after confirmation
ADDRESS_HOLD = "ADDRESS_HOLD"          # PayPal ship-to is outside what the chat agreed; seller must decide
CAPTURING = "CAPTURING"                # capture call in flight (write-ahead)
CAPTURE_UNKNOWN = "CAPTURE_UNKNOWN"    # timeout / crash during capture; reconcile, never retry blind
CAPTURE_PENDING = "CAPTURE_PENDING"    # PayPal accepted but funds pending (e.g. eCheck, review)
CAPTURED = "CAPTURED"
CAPTURE_FAILED = "CAPTURE_FAILED"
SHIPPED = "SHIPPED"                    # tracking handed to PayPal, packing photos recorded
REFUNDED = "REFUNDED"
CANCELLED = "CANCELLED"

TRANSITIONS: dict[str, set[str]] = {
    DRAFT: {TERMS_CONFIRMED, CANCELLED},
    TERMS_CONFIRMED: {ORDER_ATTACHED, DRAFT, CANCELLED},
    ORDER_ATTACHED: {MISMATCH, READY, CANCELLED},
    MISMATCH: {ORDER_ATTACHED, CANCELLED},
    READY: {BUYER_CONFIRMED, ORDER_ATTACHED, CANCELLED},
    BUYER_CONFIRMED: {CAPTURING, ORDER_CHANGED, ORDER_ATTACHED, ADDRESS_HOLD, CANCELLED},
    ADDRESS_HOLD: {BUYER_CONFIRMED, ORDER_ATTACHED, CANCELLED},
    ORDER_CHANGED: {ORDER_ATTACHED, CANCELLED},
    CAPTURING: {CAPTURED, CAPTURE_PENDING, CAPTURE_FAILED, CAPTURE_UNKNOWN},
    CAPTURE_UNKNOWN: {CAPTURED, CAPTURE_PENDING, CAPTURE_FAILED, BUYER_CONFIRMED},
    CAPTURE_PENDING: {CAPTURED, CAPTURE_FAILED},
    CAPTURED: {SHIPPED, REFUNDED},
    SHIPPED: {REFUNDED},
    CAPTURE_FAILED: {BUYER_CONFIRMED, CANCELLED},
    REFUNDED: set(),
    CANCELLED: set(),
}
TERMINAL = {SHIPPED, REFUNDED, CANCELLED}


class Conflict(Exception):
    """State moved under us, or the transition is not allowed."""


class InProgress(Exception):
    """Same idempotency key is still being processed."""


def _now() -> int:
    return int(time.time())


class Ledger:
    def __init__(self, path, clock=_now):
        if str(path) == ":memory:":
            raise ValueError("ledger requires a file so state survives restarts")
        self.path = str(Path(path).resolve())
        self.clock = clock
        with closing(self._db()) as db, db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS checkouts (
              id TEXT PRIMARY KEY, state TEXT NOT NULL, version INTEGER NOT NULL,
              data TEXT NOT NULL, created_at INTEGER NOT NULL, updated_at INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS events (
              seq INTEGER PRIMARY KEY AUTOINCREMENT, checkout_id TEXT NOT NULL, at INTEGER NOT NULL,
              from_state TEXT, to_state TEXT NOT NULL, detail TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS idempotency (
              key TEXT PRIMARY KEY, op TEXT NOT NULL, request_hash TEXT NOT NULL,
              status TEXT NOT NULL, response TEXT, created_at INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS webhook_events (
              event_id TEXT PRIMARY KEY, checkout_id TEXT, type TEXT NOT NULL,
              received_at INTEGER NOT NULL, body_sha256 TEXT NOT NULL, outcome TEXT);
            CREATE INDEX IF NOT EXISTS events_by_checkout ON events(checkout_id, seq);
            """)

    def _db(self):
        db = sqlite3.connect(self.path, timeout=5, isolation_level=None)
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA synchronous=FULL")
        return db

    # ----------------------------------------------------------- checkouts
    def create(self, checkout_id: str, data: dict) -> dict:
        now = self.clock()
        with closing(self._db()) as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("INSERT INTO checkouts VALUES (?,?,?,?,?,?)",
                       (checkout_id, DRAFT, 1, json.dumps(data), now, now))
            db.execute("INSERT INTO events (checkout_id, at, from_state, to_state, detail) VALUES (?,?,?,?,?)",
                       (checkout_id, now, None, DRAFT, json.dumps({"note": "checkout created"})))
            db.execute("COMMIT")
        return self.get(checkout_id)

    def get(self, checkout_id: str) -> dict:
        with closing(self._db()) as db:
            row = db.execute("SELECT id, state, version, data, created_at, updated_at FROM checkouts WHERE id=?",
                             (checkout_id,)).fetchone()
        if row is None:
            raise KeyError(checkout_id)
        return {"id": row[0], "state": row[1], "version": row[2], "data": json.loads(row[3]),
                "created_at": row[4], "updated_at": row[5]}

    def find_by_order(self, order_id: str) -> dict | None:
        with closing(self._db()) as db:
            row = db.execute("SELECT id FROM checkouts WHERE json_extract(data, '$.order_id')=?",
                             (order_id,)).fetchone()
        return None if row is None else self.get(row[0])

    def transition(self, checkout_id: str, expect: str | set[str], to: str, *,
                   update: dict | None = None, detail: dict | None = None, mutate=None) -> dict:
        """`mutate(data)` runs inside the write lock, for read-modify-write of nested fields."""
        expected = {expect} if isinstance(expect, str) else set(expect)
        now = self.clock()
        with closing(self._db()) as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                row = db.execute("SELECT state, version, data FROM checkouts WHERE id=?", (checkout_id,)).fetchone()
                if row is None:
                    raise KeyError(checkout_id)
                state, version, data = row[0], row[1], json.loads(row[2])
                if state not in expected:
                    raise Conflict(f"checkout is {state}, expected {sorted(expected)}")
                if to != state and to not in TRANSITIONS[state]:
                    raise Conflict(f"transition {state} -> {to} not allowed")
                data.update(update or {})
                if mutate is not None:
                    mutate(data)
                db.execute("UPDATE checkouts SET state=?, version=?, data=?, updated_at=? WHERE id=? AND version=?",
                           (to, version + 1, json.dumps(data), now, checkout_id, version))
                db.execute("INSERT INTO events (checkout_id, at, from_state, to_state, detail) VALUES (?,?,?,?,?)",
                           (checkout_id, now, state, to, json.dumps(detail or {})))
                db.execute("COMMIT")
            except BaseException:
                db.execute("ROLLBACK")
                raise
        return self.get(checkout_id)

    def events(self, checkout_id: str) -> list[dict]:
        with closing(self._db()) as db:
            rows = db.execute("SELECT seq, at, from_state, to_state, detail FROM events WHERE checkout_id=? ORDER BY seq",
                              (checkout_id,)).fetchall()
        return [{"seq": r[0], "at": r[1], "from": r[2], "to": r[3], "detail": json.loads(r[4])} for r in rows]

    def in_state(self, states: set[str]) -> list[dict]:
        marks = ",".join("?" * len(states))
        with closing(self._db()) as db:
            ids = [r[0] for r in db.execute(f"SELECT id FROM checkouts WHERE state IN ({marks})", tuple(states))]
        return [self.get(i) for i in ids]

    # --------------------------------------------------------- idempotency
    def begin(self, key: str, op: str, request: dict) -> dict | None:
        """Return a stored response for a finished key, raise InProgress for a running one,
        or claim the key and return None.  Reusing a key for a different request is refused."""
        if not (8 <= len(key) <= 128):
            raise ValueError("idempotency key must be 8-128 characters")
        rh = hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()
        with closing(self._db()) as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                row = db.execute("SELECT op, request_hash, status, response FROM idempotency WHERE key=?",
                                 (key,)).fetchone()
                if row is None:
                    db.execute("INSERT INTO idempotency VALUES (?,?,?,?,?,?)",
                               (key, op, rh, "in_progress", None, self.clock()))
                    db.execute("COMMIT")
                    return None
                db.execute("COMMIT")
            except BaseException:
                db.execute("ROLLBACK")
                raise
        if row[0] != op or row[1] != rh:
            raise Conflict("idempotency key was already used for a different request")
        if row[2] == "in_progress":
            raise InProgress(key)
        return {"replayed": True, **json.loads(row[3])}

    def finish(self, key: str, response: dict) -> dict:
        with closing(self._db()) as db, db:
            db.execute("UPDATE idempotency SET status='done', response=? WHERE key=?", (json.dumps(response), key))
        return response

    def release(self, key: str) -> None:
        """Forget a claimed key when nothing irreversible happened, so the client may retry."""
        with closing(self._db()) as db, db:
            db.execute("DELETE FROM idempotency WHERE key=? AND status='in_progress'", (key,))

    # ------------------------------------------------------------ webhooks
    def record_webhook(self, event_id: str, checkout_id: str | None, type_: str, body: bytes) -> bool:
        """True the first time an event id is seen; False for PayPal's redeliveries."""
        try:
            with closing(self._db()) as db, db:
                db.execute("INSERT INTO webhook_events VALUES (?,?,?,?,?,?)",
                           (event_id, checkout_id, type_, self.clock(), hashlib.sha256(body).hexdigest(), None))
            return True
        except sqlite3.IntegrityError:
            return False

    def webhook_outcome(self, event_id: str, outcome: str) -> None:
        with closing(self._db()) as db, db:
            db.execute("UPDATE webhook_events SET outcome=? WHERE event_id=?", (outcome, event_id))
