from concurrent.futures import ThreadPoolExecutor
import multiprocessing as mp

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from callgate.commitment import (
    MAX_CANONICAL_BYTES,
    commitment_hash,
    parameters_hash,
    parse_json_parameters,
)
from callgate.confirmation import ConfirmationCoordinator, ReviewerDecision, decision_bytes
from callgate.replay_store import SQLiteReplayStore
from callgate.verification import (
    DemoVerificationGate,
    issue_for_demo,
    issue_for_demo_v2,
    signing_bytes,
)
from integrations.alexa_mcp.server import CapabilityGateway
from integrations.alexa_mcp.server.app import PolicyBlocked


SUBJECT = "simulated-household"
SEND = {"destination": "merchant-a", "amount_cents": 5000}


def _v2_setup(tmp_path, *, parameters=SEND, operation_type="send_money", subject=SUBJECT):
    key = Ed25519PrivateKey.generate()
    proof = issue_for_demo_v2(key, issuer="issuer", session_id="session-a",
        operation_type=operation_type, parameters=parameters, subject=subject, now=1000)
    gateway = CapabilityGateway(tmp_path / "replay.sqlite3", {"issuer": key.public_key()},
                                clock=lambda: 1001, subject=subject)
    return key, proof, gateway


def test_signed_v2_payload_contains_all_commitment_fields():
    key = Ed25519PrivateKey.generate()
    proof = issue_for_demo_v2(key, issuer="issuer", session_id="session-a",
        operation_type="send_money", parameters=SEND, subject=SUBJECT, now=1000)
    payload = proof.claim.model_dump()
    assert payload["operation_type"] == "send_money"
    assert payload["substantive_parameters_hash"] == parameters_hash(SEND)
    assert payload["subject"] == SUBJECT
    assert payload["commitment_version"] == 2
    key.public_key().verify(bytes.fromhex(proof.signature), signing_bytes(proof.claim))


def test_integer_float_and_key_order_normalize_equally():
    left = {"amount": 5000, "nested": {"b": 2, "a": 1.0}}
    right = {"nested": {"a": 1, "b": 2.0}, "amount": 5000.0}
    assert parameters_hash(left) == parameters_hash(right)


def test_unicode_nfc_normalization_and_colliding_keys():
    assert parameters_hash({"name": "Cafe\u0301"}) == parameters_hash({"name": "Caf\u00e9"})
    with pytest.raises(ValueError, match="duplicate normalized"):
        parameters_hash({"e\u0301": 1, "\u00e9": 2})


def test_duplicate_raw_json_keys_are_rejected():
    with pytest.raises(ValueError, match="duplicate JSON key"):
        parse_json_parameters('{"amount": 1, "amount": 2}')


def test_whitespace_and_case_remain_substantive():
    baseline = parameters_hash({"destination": "Merchant A"})
    assert baseline != parameters_hash({"destination": "merchant a"})
    assert baseline != parameters_hash({"destination": " Merchant A "})


def test_oversized_substantive_parameters_are_rejected():
    with pytest.raises(ValueError, match="too large"):
        parameters_hash({"value": "x" * (MAX_CANONICAL_BYTES + 1)})


def test_send_money_proof_cannot_authorize_place_order(tmp_path):
    _, proof, gateway = _v2_setup(tmp_path)
    order = {"merchant": "merchant-a", "cart": [{"sku": "one", "quantity": 1}],
             "total_amount_cents": 5000}
    with pytest.raises(PolicyBlocked, match="scope mismatch"):
        gateway.authorize("place_order", order, session_id="session-a",
                          proof=proof.model_dump())


@pytest.mark.parametrize("mutation", [
    {"merchant": "merchant-b"},
    {"cart": [{"sku": "two", "quantity": 1}]},
])
def test_place_order_merchant_or_cart_mutation_invalidates_proof(tmp_path, mutation):
    order = {"merchant": "merchant-a", "cart": [{"sku": "one", "quantity": 1}],
             "total_amount_cents": 5000}
    _, proof, gateway = _v2_setup(tmp_path, parameters=order, operation_type="place_order")
    with pytest.raises(PolicyBlocked, match="scope mismatch"):
        gateway.authorize("place_order", {**order, **mutation}, session_id="session-a",
                          proof=proof.model_dump())


def test_different_subject_invalidates_v2_proof(tmp_path):
    key = Ed25519PrivateKey.generate()
    proof = issue_for_demo_v2(key, issuer="issuer", session_id="session-a",
        operation_type="send_money", parameters=SEND, subject=SUBJECT, now=1000)
    other = CapabilityGateway(tmp_path / "replay.sqlite3", {"issuer": key.public_key()},
        clock=lambda: 1001, subject="other-subject")
    with pytest.raises(PolicyBlocked, match="scope mismatch"):
        other.authorize("send_money", SEND, session_id="session-a",
                        proof=proof.model_dump())


def test_legacy_v1_non_mcp_path_still_verifies():
    key = Ed25519PrivateKey.generate()
    proof = issue_for_demo(key, issuer="issuer", session_id="legacy-session",
                           resource="legacy-resource", now=1000)
    gate = DemoVerificationGate({"issuer": key.public_key()}, clock=lambda: 1001)
    result = gate.execute(proof, session_id="legacy-session", resource="legacy-resource",
                          human_confirmed=True, policy_allows=True)
    assert result["status"] == "simulated_action_completed"


def test_challenge_then_parameter_change_before_execute_is_rejected(tmp_path):
    issuer = Ed25519PrivateKey.generate()
    reviewer = Ed25519PrivateKey.generate()
    coordinator = ConfirmationCoordinator("issuer", issuer,
        {"reviewer": reviewer.public_key()}, clock=lambda: 1000)
    request = coordinator.create_v2(session_id="session-a", operation_type="send_money",
        parameters=SEND, subject=SUBJECT, reviewer="reviewer")
    decision = ReviewerDecision(request=request, approved=True,
        signature=reviewer.sign(decision_bytes(request, True)).hex())
    proof = coordinator.decide(decision)
    gateway = CapabilityGateway(tmp_path / "replay.sqlite3", {"issuer": issuer.public_key()},
                                clock=lambda: 1001, subject=SUBJECT)
    with pytest.raises(PolicyBlocked, match="scope mismatch"):
        gateway.authorize("send_money", {**SEND, "amount_cents": 5001},
                          session_id="session-a", proof=proof.model_dump())


def test_thread_concurrent_double_spend_allows_exactly_one(tmp_path):
    _, proof, gateway = _v2_setup(tmp_path)

    def attempt(_):
        try:
            gateway.authorize("send_money", SEND, session_id="session-a",
                              proof=proof.model_dump())
            return "allowed"
        except PolicyBlocked:
            return "blocked"

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(attempt, range(2))) == ["allowed", "blocked"]


def _process_attempt(database, public_key_hex, proof, start, results):
    public_key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key_hex))
    gate = DemoVerificationGate({"issuer": public_key}, clock=lambda: 1001,
                                replay_store=SQLiteReplayStore(database))
    start.wait(10)
    try:
        resource = commitment_hash(operation_type="send_money", parameters=SEND,
                                   subject=SUBJECT)
        gate.execute(proof, session_id="session-a", resource=resource,
            operation_type="send_money", parameters=SEND, subject=SUBJECT,
            required_commitment_version=2, human_confirmed=True, policy_allows=True)
        results.put("allowed")
    except ValueError:
        results.put("blocked")


def test_process_concurrent_double_spend_allows_exactly_one(tmp_path):
    key = Ed25519PrivateKey.generate()
    proof = issue_for_demo_v2(key, issuer="issuer", session_id="session-a",
        operation_type="send_money", parameters=SEND, subject=SUBJECT, now=1000)
    public_key_hex = key.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex()
    database = str(tmp_path / "replay.sqlite3")
    SQLiteReplayStore(database)
    context = mp.get_context("spawn")
    start, results = context.Event(), context.Queue()
    workers = [context.Process(target=_process_attempt,
        args=(database, public_key_hex, proof.model_dump(), start, results)) for _ in range(2)]
    for worker in workers:
        worker.start()
    start.set()
    answers = [results.get(timeout=15) for _ in workers]
    for worker in workers:
        worker.join(timeout=15)
        assert worker.exitcode == 0
    assert sorted(answers) == ["allowed", "blocked"]
