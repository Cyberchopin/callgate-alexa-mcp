"""Local simulated authorization gate; issuer enrollment is trusted configuration.

Uses pyca Ed25519. Supply a shared SQLiteReplayStore for durable replay checks.
The default in-memory mode is for disposable single-instance tests only.
No real payment, identity enrollment, or user-confirmation transport is provided.
"""
import json
import secrets
import threading
import time
from typing import Annotated, Literal
from pydantic import Field, model_validator
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from .models import StrictModel
from .commitment import commitment_hash, parameters_hash


class VerificationClaim(StrictModel):
    version: Literal["callgate-verification-v1"] = "callgate-verification-v1"
    issuer: str = Field(min_length=1, max_length=80)
    session_id: str = Field(min_length=1, max_length=80)
    action: Literal["simulate_protected_action"] = "simulate_protected_action"
    resource: str = Field(min_length=1, max_length=120)
    issued_at: int = Field(ge=0)
    expires_at: int = Field(ge=0)
    nonce: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def lifetime(self):
        if not 0 < self.expires_at - self.issued_at <= 300:
            raise ValueError("credential lifetime must be within 300 seconds")
        return self


class VerificationClaimV2(StrictModel):
    version: Literal["callgate-verification-v2"] = "callgate-verification-v2"
    issuer: str = Field(min_length=1, max_length=80)
    session_id: str = Field(min_length=1, max_length=80)
    action: Literal["simulate_protected_action"] = "simulate_protected_action"
    resource: str = Field(pattern=r"^[a-f0-9]{64}$")
    operation_type: str = Field(min_length=1, max_length=80)
    substantive_parameters_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    subject: str = Field(min_length=1, max_length=160)
    commitment_version: Literal[2] = 2
    issued_at: int = Field(ge=0)
    expires_at: int = Field(ge=0)
    nonce: str = Field(pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def lifetime(self):
        if not 0 < self.expires_at - self.issued_at <= 300:
            raise ValueError("credential lifetime must be within 300 seconds")
        return self


class SignedVerification(StrictModel):
    claim: Annotated[VerificationClaim | VerificationClaimV2,
                     Field(discriminator="version")]
    signature: str = Field(pattern=r"^[a-f0-9]{128}$")


def signing_bytes(claim):
    return json.dumps(claim.model_dump(), sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("ascii")


def issue_for_demo(key: Ed25519PrivateKey, *, issuer, session_id, resource, now=None):
    """Trusted test issuer only. Calling this function does not verify a person."""
    now = int(time.time()) if now is None else now
    claim = VerificationClaim(issuer=issuer, session_id=session_id, resource=resource,
                              issued_at=now, expires_at=now+120, nonce=secrets.token_hex(32))
    return SignedVerification(claim=claim, signature=key.sign(signing_bytes(claim)).hex())


def issue_for_demo_v2(key: Ed25519PrivateKey, *, issuer, session_id, operation_type,
                      parameters, subject, now=None):
    """Trusted test issuer only; all v2 scope fields are signed in the claim."""
    parameter_digest = parameters_hash(parameters)
    resource = commitment_hash(operation_type=operation_type, parameters=parameters,
                               subject=subject)
    return issue_for_demo_v2_hash(key, issuer=issuer, session_id=session_id,
        operation_type=operation_type, substantive_parameters_hash=parameter_digest,
        subject=subject, resource=resource, now=now)


def issue_for_demo_v2_hash(key: Ed25519PrivateKey, *, issuer, session_id,
                           operation_type, substantive_parameters_hash, subject,
                           resource, now=None):
    """Issue from a server-computed hash already covered by reviewer approval."""
    now = int(time.time()) if now is None else now
    claim = VerificationClaimV2(issuer=issuer, session_id=session_id, resource=resource,
        operation_type=operation_type,
        substantive_parameters_hash=substantive_parameters_hash, subject=subject,
        issued_at=now, expires_at=now + 120, nonce=secrets.token_hex(32))
    return SignedVerification(claim=claim, signature=key.sign(signing_bytes(claim)).hex())


class DemoVerificationGate:
    def __init__(self, trusted_issuers, *, clock=time.time, replay_store=None):
        self._issuers = dict(trusted_issuers)
        self._clock = clock
        self._replay_store = replay_store
        self._consumed = {}
        self._lock = threading.Lock()

    def execute(self, credential, *, session_id, resource, human_confirmed=False,
                policy_allows=False, operation_type=None, parameters=None, subject=None,
                required_commitment_version=None):
        """Confirmation/policy inputs must come from trusted orchestration, not caller JSON."""
        credential = SignedVerification.model_validate(credential)
        c = credential.claim
        key = self._issuers.get(c.issuer)
        if key is None:
            raise ValueError("unknown issuer")
        try:
            key.verify(bytes.fromhex(credential.signature), signing_bytes(c))
        except InvalidSignature:
            raise ValueError("invalid signature") from None
        if required_commitment_version == 2 and not isinstance(c, VerificationClaimV2):
            raise ValueError("commitment v2 required")
        if isinstance(c, VerificationClaimV2):
            if operation_type is None or parameters is None or subject is None:
                raise ValueError("v2 scope required")
            expected_parameters_hash = parameters_hash(parameters)
            expected_resource = commitment_hash(operation_type=operation_type,
                parameters=parameters, subject=subject)
            if (c.operation_type != operation_type or
                    c.substantive_parameters_hash != expected_parameters_hash or
                    c.subject != subject or c.commitment_version != 2 or
                    c.resource != expected_resource):
                raise ValueError("scope mismatch")
        if c.session_id != session_id or c.resource != resource:
            raise ValueError("scope mismatch")
        if human_confirmed is not True or policy_allows is not True:
            raise ValueError("confirmation and policy approval required")
        if self._replay_store is not None:
            self._replay_store.consume(c.issuer, c.nonce, c.issued_at, c.expires_at, self._clock)
            return {"status":"simulated_action_completed", "session_id":session_id,
                    "resource":resource, "real_action_executed":False}
        with self._lock:
            now = int(self._clock())
            if not c.issued_at <= now < c.expires_at:
                raise ValueError("credential not currently valid")
            self._consumed = {k:v for k,v in self._consumed.items() if v > now}
            nonce_key = (c.issuer, c.nonce)
            if nonce_key in self._consumed:
                raise ValueError("credential already consumed")
            if len(self._consumed) >= 10000:
                raise ValueError("gate capacity reached")
            self._consumed[nonce_key] = c.expires_at
            return {"status":"simulated_action_completed", "session_id":session_id,
                    "resource":resource, "real_action_executed":False}
