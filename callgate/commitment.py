"""Canonical, versioned commitments for simulated protected operations."""

import hashlib
import json
import unicodedata
from decimal import Decimal, InvalidOperation


MAX_CANONICAL_BYTES = 16_384


def _normalized_number(value):
    try:
        number = Decimal(str(value))
    except InvalidOperation as error:
        raise ValueError("finite JSON number required") from error
    if not number.is_finite():
        raise ValueError("finite JSON number required")
    if number == 0:
        number = Decimal(0)
    else:
        number = number.normalize()
    return {"$number": format(number, "f")}


def normalize(value):
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, (int, float, Decimal)):
        return _normalized_number(value)
    if isinstance(value, list):
        return [normalize(item) for item in value]
    if isinstance(value, dict) and all(isinstance(key, str) for key in value):
        normalized = {}
        for key, item in value.items():
            normalized_key = unicodedata.normalize("NFC", key)
            if normalized_key in normalized:
                raise ValueError("duplicate normalized JSON key")
            normalized[normalized_key] = normalize(item)
        return {key: normalized[key] for key in sorted(normalized)}
    raise ValueError("JSON-compatible substantive parameters required")


def _reject_duplicate_pairs(pairs):
    result = {}
    for key, value in pairs:
        normalized_key = unicodedata.normalize("NFC", key)
        if normalized_key in result:
            raise ValueError("duplicate JSON key")
        result[normalized_key] = value
    return result


def parse_json_parameters(raw):
    """Parse raw JSON without silently accepting duplicate or NFC-colliding keys."""
    value = json.loads(raw, object_pairs_hook=_reject_duplicate_pairs,
                       parse_constant=lambda _: (_ for _ in ()).throw(
                           ValueError("finite JSON number required")))
    if not isinstance(value, dict):
        raise ValueError("JSON object required")
    return value


def canonical_bytes(parameters):
    raw = json.dumps(normalize(parameters), sort_keys=True, separators=(",", ":"),
                     ensure_ascii=True, allow_nan=False).encode("ascii")
    if len(raw) > MAX_CANONICAL_BYTES:
        raise ValueError("substantive parameters too large")
    return raw


def parameters_hash(parameters):
    return hashlib.sha256(canonical_bytes(parameters)).hexdigest()


def commitment_hash(*, operation_type, parameters, subject, commitment_version=2):
    if commitment_version != 2:
        raise ValueError("commitment version 2 required")
    if not isinstance(operation_type, str) or not operation_type.strip():
        raise ValueError("operation type required")
    if not isinstance(subject, str) or not subject.strip():
        raise ValueError("subject required")
    body = {
        "commitment_version": 2,
        "operation_type": operation_type,
        "substantive_parameters_hash": parameters_hash(parameters),
        "subject": subject,
    }
    raw = json.dumps(body, sort_keys=True, separators=(",", ":"),
                     ensure_ascii=True, allow_nan=False).encode("ascii")
    return hashlib.sha256(raw).hexdigest()
