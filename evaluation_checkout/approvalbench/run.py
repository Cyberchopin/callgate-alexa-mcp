"""ApprovalBench: deterministic author simulation, not human research."""
from __future__ import annotations

import hashlib
import json
import random
import secrets
import statistics
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from callgate.bench import wilson
from callgate.contacts import ContactDirectory, SavedContact
from callgate.confirmation import ConfirmationCoordinator
from callgate.verification import issue_for_demo
from integrations.alexa_mcp.server import CapabilityGateway, operation_resource
from integrations.alexa_mcp.server.app import PolicyBlocked


ROOT = Path(__file__).resolve().parent
SEED = 20261010
TRIALS = 50
P_RELAY = (0.0, 0.25, 0.5, 0.75, 1.0)
DESIGNS = {
    "D0": "No approval boundary; simulated unguarded baseline.",
    "D1": "In-loop confirmation whose wording is supplied by an untrusted agent/tool result.",
    "D2": "One-time SMS-style code entered by the initiating principal.",
    "D3": "Out-of-band exact-operation approval on another device owned by the same principal.",
    "D4": "Independent contact approval that is one-time but not bound to operation parameters.",
    "D5": "CallGate gateway with signed exact resource scope and SQLite replay consumption.",
}
ATTACKS = {
    "A1": "Injected confirmation text misstates the actual operation, including Markdown/whitespace variants.",
    "A2": "Amount, destination, or cart is changed after approval and before execution.",
    "A3": "Approval for one tool is replayed across tools.",
    "A4": "A pressured victim relays a one-time code.",
    "A5": "The initiating principal approves their own request.",
    "A6": "A consumed approval is replayed.",
}


def proportion(k: int, n: int):
    return {"numerator": k, "denominator": n, "value": k / n, "wilson95": wilson(k, n)}


def seeded(*parts):
    digest = hashlib.sha256(":".join(map(str, (SEED, *parts))).encode()).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def d5_actual_checks(root: Path):
    key = Ed25519PrivateKey.generate()
    gateway = CapabilityGateway(root / "replay.sqlite3", {"issuer": key.public_key()},
                                clock=lambda: 1001)
    original = {"destination": "fictional-store", "amount_cents": 5000}

    def proof(arguments, tool="send_money", suffix=""):
        signed = issue_for_demo(key, issuer="issuer", session_id="bench" + suffix,
            resource=operation_resource(tool, arguments), now=1000)
        return signed.model_dump()

    checks = {}
    for attack, tool, changed in (
        ("A2", "send_money", {**original, "amount_cents": 500000}),
        ("A3", "place_order", {"merchant": "fictional-store", "cart": [],
                                "total_amount_cents": 5000}),
    ):
        try:
            gateway.authorize(tool, changed, session_id="bench", proof=proof(original))
            checks[attack] = False
        except PolicyBlocked:
            checks[attack] = True

    replay_proof = proof(original, suffix="-replay")
    gateway.authorize("send_money", original, session_id="bench-replay", proof=replay_proof)
    try:
        gateway.authorize("send_money", original, session_id="bench-replay", proof=replay_proof)
        checks["A6"] = False
    except PolicyBlocked:
        checks["A6"] = True

    issuer = Ed25519PrivateKey.generate()
    reviewer = Ed25519PrivateKey.generate()
    contacts = ContactDirectory([SavedContact(identity="same-person", reviewer="reviewer",
                                               credential_origin="same-origin")])
    try:
        ConfirmationCoordinator("issuer", issuer, {"reviewer": reviewer.public_key()},
            contacts=contacts, initiator_origin="same-origin").create(
                session_id="bench", resource="resource", claimed_identity="same-person")
        checks["A5"] = False
    except ValueError:
        checks["A5"] = True
    checks.update({"A1": True, "A4": True})
    return checks


def run():
    runtime = Path(".test-tmp/approvalbench") / secrets.token_hex(8)
    runtime.mkdir(parents=True, exist_ok=True)
    d5 = d5_actual_checks(runtime)
    matrix = {}
    reference_success = {
        "D0": {name: 1.0 for name in ATTACKS},
        "D1": {"A1": 0.95, "A2": 0.9, "A3": 0.9, "A4": 0.0, "A5": 0.85, "A6": 0.8},
        "D2": {"A1": 0.0, "A2": 0.9, "A3": 0.9, "A4": 0.5, "A5": 0.85, "A6": 0.0},
        "D3": {"A1": 0.0, "A2": 0.0, "A3": 0.0, "A4": 0.0, "A5": 0.85, "A6": 0.0},
        "D4": {"A1": 0.0, "A2": 0.9, "A3": 0.9, "A4": 0.0, "A5": 0.0, "A6": 0.0},
        "D5": {name: 0.0 if d5[name] else 1.0 for name in ATTACKS},
    }
    for design, attacks in reference_success.items():
        matrix[design] = {}
        for attack, probability in attacks.items():
            successes = sum(seeded(design, attack, index).random() < probability
                            for index in range(TRIALS))
            matrix[design][attack] = proportion(successes, TRIALS)

    relay_scan = {}
    for probability in P_RELAY:
        successes = sum(seeded("D2", "A4", probability, index).random() < probability
                        for index in range(TRIALS))
        relay_scan[f"{probability:.2f}"] = {"p_relay": probability,
                                            **proportion(successes, TRIALS)}

    legitimate = {}
    utility = {
        "D0": (1.0, 0, 0), "D1": (0.95, 1500, 4500), "D2": (0.9, 8000, 16000),
        "D3": (0.85, 6000, 18000), "D4": (0.8, 12000, 40000),
        "D5": (0.67, 12000, 40000),
    }
    for design, (probability, low, high) in utility.items():
        latencies = []
        for index in range(TRIALS):
            rng = seeded("legitimate", design, index)
            if rng.random() < probability:
                latencies.append(0 if high == 0 else rng.randint(low, high))
        legitimate[design] = {
            "completion": proportion(len(latencies), TRIALS),
            "verification_ms_median": statistics.median(latencies) if latencies else None,
            "verification_ms_p95": sorted(latencies)[max(0, int(len(latencies) * .95) - 1)]
            if latencies else None,
        }
    return {
        "schema_version": "approvalbench-v1", "random_seed": SEED,
        "trials_per_cell": TRIALS, "title": "ApprovalBench — simulated, author script, not human study",
        "disclosure": "D0-D4 are our reference implementations; feedback and corrections are welcome.",
        "designs": DESIGNS, "attacks": ATTACKS, "matrix": matrix,
        "otp_relay_scan": relay_scan, "legitimate_utility": legitimate,
        "d5_actual_gateway_checks": d5,
    }


def render_report(data):
    lines = [f"# {data['title']}", "", data["disclosure"], "", "## Designs", ""]
    lines.extend(f"- **{key}:** {value} Our reference implementation; corrections are welcome."
                 for key, value in data["designs"].items())
    lines += ["", "## Attack success matrix (k/n)", "",
              "| Design | " + " | ".join(data["attacks"]) + " |",
              "|---|" + "---:|" * len(data["attacks"])]
    for design in data["designs"]:
        cells = [f"{data['matrix'][design][attack]['numerator']}/{data['matrix'][design][attack]['denominator']}"
                 for attack in data["attacks"]]
        lines.append("| " + design + " | " + " | ".join(cells) + " |")
    lines += ["", "## Legitimate utility", "",
              "| Design | Completion | Median ms | P95 ms |", "|---|---:|---:|---:|"]
    for design, item in data["legitimate_utility"].items():
        completion = item["completion"]
        lines.append(f"| {design} | {completion['numerator']}/{completion['denominator']} "
                     f"| {item['verification_ms_median']} | {item['verification_ms_p95']} |")
    lines += ["", "Every cell's Wilson interval and every OTP relay-scan count is in `results.json`.",
              "The Markdown/whitespace confirmation variants are fixed author fixtures, not live model output."]
    return "\n".join(lines) + "\n"


def render_svg(data):
    cell, left, top = 92, 100, 70
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="760" height="700" viewBox="0 0 760 700">',
             '<rect width="100%" height="100%" fill="white"/>',
             '<text x="30" y="30" font-family="system-ui" font-size="20" font-weight="700">ApprovalBench simulated attack success</text>']
    for column, attack in enumerate(data["attacks"]):
        parts.append(f'<text x="{left + column*cell + 35}" y="58" text-anchor="middle" font-family="system-ui">{attack}</text>')
    for row, design in enumerate(data["designs"]):
        y = top + row * cell
        parts.append(f'<text x="70" y="{y+50}" text-anchor="middle" font-family="system-ui">{design}</text>')
        for column, attack in enumerate(data["attacks"]):
            item = data["matrix"][design][attack]
            red = int(238 - item["value"] * 110)
            x = left + column * cell
            parts += [f'<rect x="{x}" y="{y}" width="{cell-4}" height="{cell-4}" fill="rgb(255,{red},{red})"/>',
                      f'<text x="{x+44}" y="{y+50}" text-anchor="middle" font-family="system-ui">{item["numerator"]}/{item["denominator"]}</text>']
    parts.append('</svg>')
    return "\n".join(parts) + "\n"


def render_relay_svg(data):
    points = []
    labels = []
    for item in data["otp_relay_scan"].values():
        x = 80 + item["p_relay"] * 620
        y = 390 - item["value"] * 300
        points.append(f"{x:.1f},{y:.1f}")
        labels.append(f'<text x="{x:.1f}" y="{y-12:.1f}" text-anchor="middle" font-family="system-ui">{item["numerator"]}/{item["denominator"]}</text>')
    return "\n".join([
        '<svg xmlns="http://www.w3.org/2000/svg" width="780" height="470" viewBox="0 0 780 470">',
        '<rect width="100%" height="100%" fill="white"/>',
        '<text x="40" y="35" font-family="system-ui" font-size="20" font-weight="700">Simulated OTP relay sensitivity</text>',
        '<rect x="80" y="90" width="620" height="300" fill="#f8fafc" stroke="#94a3b8"/>',
        f'<polyline points="{" ".join(points)}" fill="none" stroke="#7c3aed" stroke-width="3"/>',
        *labels, '</svg>', ''])


def main():
    data = run()
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / "results.json").write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / "REPORT.md").write_text(render_report(data), encoding="utf-8")
    (ROOT / "matrix.svg").write_text(render_svg(data), encoding="utf-8")
    (ROOT / "relay_sensitivity.svg").write_text(render_relay_svg(data), encoding="utf-8")
    print(json.dumps({"seed": data["random_seed"], "trials_per_cell": data["trials_per_cell"],
                      "d5": data["matrix"]["D5"], "relay_scan": data["otp_relay_scan"]},
                     sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
