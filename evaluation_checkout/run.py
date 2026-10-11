"""Run a tiny safety-utility checkout rehearsal.

The purpose is to show why "deny everything" is incomplete: it can avoid
unauthorized simulated execution while also completing no legitimate checkout.
All inputs are synthetic, author-provided and correlated. Do not report these
counts as real-world accuracy or fraud prevalence.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import random
import statistics
from pathlib import Path
from xml.sax.saxutils import escape

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from callgate.bench import wilson
from callgate.confirmation import ConfirmationCoordinator, ReviewerDecision, decision_bytes
from callgate.models import Transcript
from callgate.verification import DemoVerificationGate
from callgate.workflow import DemoWorkflow


ROOT = Path(__file__).resolve().parent
RANDOM_SEED = 20261010
TRIALS_PER_SCENARIO = 100
OTP_RELAY_PROBABILITIES = (0.0, 0.25, 0.5, 0.75, 1.0)
CONTACT_SENSITIVITY = {
    "contact_p100_fast": (1.0, 8000, 20000),
    "contact_p067_typical": (0.67, 12000, 40000),
    "contact_p067_slow": (0.67, 45000, 120000),
}


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    transcript: str
    authorized: bool
    reviewer_approves: bool
    response_ms: int | None
    contact_available: bool = True
    amount_cents: int = 280000
    destination: str = "campus-repair-checkout"


SCENARIOS = [
    Scenario("co-001", "Send 2800 dollars right now for my repair checkout.", True, True, 18000),
    Scenario("co-002", "Send 1900 dollars for the checkout now while I am on the call.", True, True, 24000),
    Scenario("co-003", "Transfer 3200 dollars for this purchase after a family check.", True, True, 30000,
             contact_available=False),
    Scenario("co-004", "Send 2800 dollars right now or your account will be frozen.", False, False, 22000),
    Scenario("co-005", "Do not tell anyone and move your savings into the holding wallet.", False, False, None),
    Scenario("co-006", "Tell me your verification code so I can finish payment.", False, False, None),
]

CALLGATE_POLICIES = {
    "callgate_p100_fast": {"response_probability": 1.0, "latency_multiplier": 1.0,
                           "force_all_contacts_available": True},
    "callgate_p67_observed": {"response_probability": 2 / 3, "latency_multiplier": 1.0,
                              "force_all_contacts_available": False},
    "callgate_p67_slow": {"response_probability": 2 / 3, "latency_multiplier": 4.0,
                          "force_all_contacts_available": False},
}


def _proportion(successes: int, total: int) -> dict:
    return {"numerator": successes, "denominator": total,
            "value": None if total == 0 else successes / total,
            "wilson95": wilson(successes, total)}


def _stable_rng(*parts: object) -> random.Random:
    material = ":".join(str(part) for part in (RANDOM_SEED, *parts)).encode("utf-8")
    seed = int.from_bytes(hashlib.sha256(material).digest()[:8], "big")
    return random.Random(seed)


def _p95(values: list[int]) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)]


def _sensitivity_results() -> dict:
    unauthorized_trials = sum(not item.authorized for item in SCENARIOS) * TRIALS_PER_SCENARIO
    legitimate_trials = sum(item.authorized for item in SCENARIOS) * TRIALS_PER_SCENARIO
    otp = {}
    for probability in OTP_RELAY_PROBABILITIES:
        executed = sum(
            _stable_rng("otp", probability, index).random() < probability
            for index in range(unauthorized_trials)
        )
        otp[f"p_relay_{probability:.2f}"] = {
            "p_relay": probability,
            "false_execute": _proportion(executed, unauthorized_trials),
            "legitimate_completion": _proportion(legitimate_trials, legitimate_trials),
            "verification_ms_median": 12000,
            "verification_ms_p95": 12000,
        }
    contact = {}
    for name, (availability, minimum, maximum) in CONTACT_SENSITIVITY.items():
        latencies = []
        for index in range(legitimate_trials):
            rng = _stable_rng("contact", name, index)
            if rng.random() < availability:
                latencies.append(rng.randint(minimum, maximum))
        contact[name] = {
            "contact_availability_probability": availability,
            "latency_distribution": {
                "name": "uniform",
                "minimum_ms": minimum,
                "maximum_ms": maximum,
            },
            "false_execute": _proportion(0, unauthorized_trials),
            "legitimate_completion": _proportion(len(latencies), legitimate_trials),
            "verification_ms_median": None if not latencies else statistics.median(latencies),
            "verification_ms_p95": _p95(latencies),
        }
    return {"otp_step_up": otp, "callgate": contact}


def _workflow_result(scenario: Scenario, policy: dict) -> dict:
    contact_available = scenario.contact_available or policy["force_all_contacts_available"]
    issuer = Ed25519PrivateKey.generate()
    reviewer = Ed25519PrivateKey.generate()
    clock = [1000]
    coordinator = ConfirmationCoordinator(
        "issuer", issuer, {"reviewer": reviewer.public_key()}, clock=lambda: clock[0])
    gate = DemoVerificationGate({"issuer": issuer.public_key()}, clock=lambda: clock[0])
    workflow = DemoWorkflow(coordinator, gate, "reviewer", request_clock=lambda: clock[0])
    workflow.set_processing_consent(True)
    risk = workflow.ingest(Transcript(segment_id=scenario.scenario_id, text=scenario.transcript,
                                      start_ms=0, end_ms=1000, final=True))
    completed = False
    completion_status = None
    verification_ms = None
    refusal_reason = None
    try:
        bundle = workflow.request_confirmation(destination=scenario.destination,
            amount_cents=scenario.amount_cents)
    except ValueError:
        refusal_reason = "policy_prevents_confirmation"
        bundle = None
    if bundle is not None:
        if not contact_available:
            refusal_reason = "contact_unavailable"
        else:
            decision = ReviewerDecision(request=bundle["request"], approved=scenario.reviewer_approves,
                signature=reviewer.sign(
                    decision_bytes(bundle["request"], scenario.reviewer_approves)).hex())
            try:
                result = workflow.complete(decision,
                    challenge_response=bundle["out_of_band_challenge"])
                completion_status = result["status"]
                completed = completion_status == "simulated_action_completed"
                verification_ms = None if scenario.response_ms is None else int(
                    scenario.response_ms * policy["latency_multiplier"])
            except ValueError:
                refusal_reason = "confirmation_failed"
    return {"state": risk["state"], "completed": completed,
            "completion_status": completion_status, "verification_ms": verification_ms,
            "refusal_reason": refusal_reason}


def _system_rows() -> list[dict]:
    rows = []
    for scenario in SCENARIOS:
        rows.append({"system": "deny_all", "scenario_id": scenario.scenario_id,
                     "authorized": scenario.authorized, "completed": False,
                     "verification_ms": None, "state": None,
                     "refusal_reason": "always_denied"})
        rows.append({"system": "unguarded_checkout", "scenario_id": scenario.scenario_id,
                     "authorized": scenario.authorized, "completed": True,
                     "verification_ms": 0, "state": None,
                     "refusal_reason": None})
        rows.append({"system": "otp_step_up", "scenario_id": scenario.scenario_id,
                     "authorized": scenario.authorized, "completed": True,
                     "verification_ms": 12000, "state": None,
                     "refusal_reason": None if scenario.authorized else "victim_relayed_otp"})
        for name, policy in CALLGATE_POLICIES.items():
            rows.append({"system": name, "scenario_id": scenario.scenario_id,
                         "authorized": scenario.authorized,
                         "contact_response_probability": policy["response_probability"],
                         "latency_multiplier": policy["latency_multiplier"],
                         **_workflow_result(scenario, policy)})
    return rows


def _summaries(rows: list[dict]) -> dict:
    systems = sorted({row["system"] for row in rows})
    out = {}
    for system in systems:
        subset = [row for row in rows if row["system"] == system]
        unauthorized = [row for row in subset if not row["authorized"]]
        legitimate = [row for row in subset if row["authorized"]]
        latencies = [row["verification_ms"] for row in legitimate
                     if row["completed"] and row["verification_ms"] is not None]
        out[system] = {
            "false_execute": _proportion(
                sum(row["completed"] for row in unauthorized), len(unauthorized)),
            "legitimate_completion": _proportion(
                sum(row["completed"] for row in legitimate), len(legitimate)),
            "verification_ms_median": None if not latencies else statistics.median(latencies),
            "verification_ms_p95": None if not latencies else sorted(latencies)[-1],
            "latency_note": "synthetic reviewer response parameter, not human timing",
        }
    return out


def run() -> dict:
    rows = _system_rows()
    return {
        "schema_version": "callgate-checkout-utility-v2",
        "title": "Checkout safety-utility sensitivity — simulated, author script, not human study",
        "disclosure": ("Synthetic author-provided checkout rehearsal. No real payments, "
                       "no independent labels, no population claim. Contact availability "
                       "and latency are scripted parameters."),
        "assumptions": [
            "Three author-written legitimate and three unauthorized scenarios are weighted equally.",
            "OTP relay is a seeded Bernoulli draw at each stated p_relay value.",
            "A legitimate CallGate action completes only when the contact is available.",
            "The scripted independent contact rejects every unauthorized CallGate request.",
            "Contact latency is sampled from the stated synthetic uniform distribution.",
            "Outputs are sensitivity results, not forecasts or measured human behavior.",
        ],
        "random_seed": RANDOM_SEED,
        "trials_per_scenario": TRIALS_PER_SCENARIO,
        "otp_relay_probabilities": list(OTP_RELAY_PROBABILITIES),
        "scenario_count": len(SCENARIOS),
        "systems": ["deny_all", "unguarded_checkout", "otp_step_up",
                    "callgate_p100_fast", "callgate_p67_observed", "callgate_p67_slow"],
        "rows": rows,
        "summary": _summaries(rows),
        "sensitivity": _sensitivity_results(),
        "model_parameters": {
            "otp_step_up": "coerced victim relays OTP in unauthorized pressure scenarios",
            "callgate_p100_fast": "all contacts respond with scripted fast latency",
            "callgate_p67_observed": "one legitimate contact is unavailable",
            "callgate_p67_slow": "same availability as observed; response latency multiplied by 4",
        },
    }


def render_markdown(report: dict) -> str:
    lines = [
        f"# {report['title']}",
        "",
        "## Assumptions",
        "",
        *[f"- {item}" for item in report["assumptions"]],
        "",
        report["disclosure"],
        "",
        "## Scripted scenario rehearsal",
        "",
        "| System | False execute | Legitimate completion | Median verify ms | P95 verify ms |",
        "|---|---:|---:|---:|---:|",
    ]
    for system in report["systems"]:
        item = report["summary"][system]
        false_execute = item["false_execute"]
        utility = item["legitimate_completion"]
        lines.append(
            f"| {system} | {false_execute['numerator']}/{false_execute['denominator']} "
            f"({false_execute['value']:.1%}) | {utility['numerator']}/{utility['denominator']} "
            f"({utility['value']:.1%}) | {item['verification_ms_median']} | "
            f"{item['verification_ms_p95']} |")
    lines += [
        "",
        "![Safety-utility chart](safety_utility.svg)",
        "",
        "Wilson intervals are included in the JSON for descriptive proportions only.",
        "Reviewer timing is a synthetic parameter, not measured human response time.",
        "Deny-all has no unauthorized execution in this rehearsal, but also no legitimate completion.",
        "OTP step-up is modeled as failing under live coercion because the victim relays the code.",
        "CallGate variants model contact availability and delay; lower availability creates conversion loss.",
        "",
        "## OTP relay sensitivity",
        "",
        "| p_relay | False execute | Wilson 95% | Legitimate completion | Median ms | P95 ms |",
        "|---:|---:|---:|---:|---:|---:|",
    ]
    for item in report["sensitivity"]["otp_step_up"].values():
        false_execute = item["false_execute"]
        utility = item["legitimate_completion"]
        interval = "–".join(f"{value:.1%}" for value in false_execute["wilson95"])
        lines.append(
            f"| {item['p_relay']:.2f} | {false_execute['numerator']}/{false_execute['denominator']} "
            f"({false_execute['value']:.1%}) | {interval} | {utility['numerator']}/{utility['denominator']} "
            f"({utility['value']:.1%}) | {item['verification_ms_median']} | {item['verification_ms_p95']} |")
    lines += [
        "",
        "## Contact availability and delay sensitivity",
        "",
        "| Policy | False execute | Legitimate completion | Wilson 95% | Median ms | P95 ms |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name, item in report["sensitivity"]["callgate"].items():
        false_execute = item["false_execute"]
        utility = item["legitimate_completion"]
        interval = "–".join(f"{value:.1%}" for value in utility["wilson95"])
        lines.append(
            f"| {name} | {false_execute['numerator']}/{false_execute['denominator']} "
            f"({false_execute['value']:.1%}) | {utility['numerator']}/{utility['denominator']} "
            f"({utility['value']:.1%}) | {interval} | {item['verification_ms_median']} | "
            f"{item['verification_ms_p95']} |")
    lines += [
        "",
        "![OTP relay sensitivity chart](sensitivity_scan.svg)",
        "",
        "Unfavorable results are retained: deny-all has no utility; unguarded checkout always executes; "
        "OTP becomes less safe as relay probability rises; contact unavailability lowers completion.",
    ]
    return "\n".join(lines) + "\n"


def render_sensitivity_svg(report: dict) -> str:
    width, height = 900, 500
    left, top, plot_w, plot_h = 90, 70, 700, 330
    points = []
    labels = []
    for item in report["sensitivity"]["otp_step_up"].values():
        x = left + item["p_relay"] * plot_w
        y = top + plot_h - item["false_execute"]["value"] * plot_h
        points.append(f"{x:.1f},{y:.1f}")
        labels.extend([
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="#7c3aed"/>',
            f'<text x="{x:.1f}" y="{y - 13:.1f}" text-anchor="middle" font-family="system-ui" font-size="13">{item["false_execute"]["numerator"]}/{item["false_execute"]["denominator"]}</text>',
            f'<text x="{x:.1f}" y="425" text-anchor="middle" font-family="system-ui" font-size="13">{item["p_relay"]:.2f}</text>',
        ])
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">OTP relay probability sensitivity</title>',
        '<desc id="desc">Seeded simulated false execution as OTP relay probability increases.</desc>',
        '<rect width="100%" height="100%" fill="#fff"/>',
        '<text x="90" y="35" font-family="system-ui" font-size="22" font-weight="700">OTP relay sensitivity — simulated</text>',
        f'<rect x="{left}" y="{top}" width="{plot_w}" height="{plot_h}" fill="#f8fafc" stroke="#cbd5e1"/>',
        f'<polyline points="{" ".join(points)}" fill="none" stroke="#7c3aed" stroke-width="3"/>',
        *labels,
        f'<text x="{left + plot_w / 2}" y="465" text-anchor="middle" font-family="system-ui" font-size="17">p_relay</text>',
        f'<text x="25" y="{top + plot_h / 2}" transform="rotate(-90 25 {top + plot_h / 2})" text-anchor="middle" font-family="system-ui" font-size="17">False execution</text>',
        '</svg>',
    ]
    return "\n".join(parts) + "\n"


def render_svg(report: dict) -> str:
    width, height = 900, 520
    left, top, plot = 110, 70, 340
    bottom = top + plot
    colors = {"deny_all": "#6b7280", "unguarded_checkout": "#b45309",
              "otp_step_up": "#dc2626", "callgate_p100_fast": "#166534",
              "callgate_p67_observed": "#15803d", "callgate_p67_slow": "#65a30d"}
    labels = {
        "deny_all": "deny-all",
        "unguarded_checkout": "unguarded",
        "otp_step_up": "OTP step-up",
        "callgate_p100_fast": "CallGate p=1.0",
        "callgate_p67_observed": "CallGate p=0.67",
        "callgate_p67_slow": "CallGate slow",
    }

    def x(value):
        return left + value * plot

    def y(value):
        return bottom - value * plot

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" '
        'aria-labelledby="title desc">',
        '<title id="title">Checkout safety and utility rehearsal</title>',
        '<desc id="desc">Synthetic comparison of legitimate completion and false execution.</desc>',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<rect x="{left}" y="{top}" width="{plot}" height="{plot}" fill="#f8fafc" '
        'stroke="#cbd5e1"/>',
        f'<line x1="{left}" y1="{bottom}" x2="{left + plot}" y2="{bottom}" stroke="#0f172a"/>',
        f'<line x1="{left}" y1="{bottom}" x2="{left}" y2="{top}" stroke="#0f172a"/>',
        f'<text x="{left + plot / 2}" y="{height - 38}" text-anchor="middle" '
        'font-family="system-ui, sans-serif" font-size="18">Legitimate checkout completion</text>',
        f'<text x="28" y="{top + plot / 2}" transform="rotate(-90 28 {top + plot / 2})" '
        'text-anchor="middle" font-family="system-ui, sans-serif" font-size="18">'
        'False execution</text>',
        f'<text x="{left}" y="{bottom + 28}" text-anchor="middle" '
        'font-family="system-ui, sans-serif" font-size="14">0%</text>',
        f'<text x="{left + plot}" y="{bottom + 28}" text-anchor="middle" '
        'font-family="system-ui, sans-serif" font-size="14">100%</text>',
        f'<text x="{left - 18}" y="{bottom + 5}" text-anchor="end" '
        'font-family="system-ui, sans-serif" font-size="14">0%</text>',
        f'<text x="{left - 18}" y="{top + 5}" text-anchor="end" '
        'font-family="system-ui, sans-serif" font-size="14">100%</text>',
        f'<text x="{left + plot + 38}" y="{top + 18}" font-family="system-ui, sans-serif" '
        'font-size="13" fill="#475569">unsafe</text>',
        f'<text x="{left + plot + 38}" y="{bottom}" font-family="system-ui, sans-serif" '
        'font-size="13" fill="#475569">useful and safer</text>',
    ]
    for system in report["systems"]:
        summary = report["summary"][system]
        false_execute = summary["false_execute"]
        utility = summary["legitimate_completion"]
        px = x(utility["value"])
        py = y(false_execute["value"])
        label = labels[system]
        color = colors[system]
        point = (f"{label}: false execute {false_execute['numerator']}/"
                 f"{false_execute['denominator']}; legitimate completion "
                 f"{utility['numerator']}/{utility['denominator']}")
        y_offset = 10 if system != "callgate_p67_slow" else 30
        parts += [
            f'<circle cx="{px:.1f}" cy="{py:.1f}" r="8" fill="{color}"/>',
            f'<text x="{px + 14:.1f}" y="{py - 10:.1f}" font-family="system-ui, sans-serif" '
            f'font-size="15" font-weight="700" fill="{color}">{escape(label)}</text>',
            f'<text x="{px + 14:.1f}" y="{py + y_offset:.1f}" font-family="system-ui, sans-serif" '
            f'font-size="13" fill="#334155">{escape(point)}</text>',
        ]
    parts += [
        '<text x="110" y="32" font-family="system-ui, sans-serif" font-size="22" '
        'font-weight="700" fill="#0f172a">Synthetic checkout safety-utility rehearsal</text>',
        '<text x="110" y="54" font-family="system-ui, sans-serif" font-size="14" '
        'fill="#475569">Author-written scenarios; no real payments or human timing.</text>',
        '</svg>',
    ]
    return "\n".join(parts) + "\n"


def main() -> int:
    report = run()
    ROOT.mkdir(exist_ok=True)
    (ROOT / "results.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    (ROOT / "REPORT.md").write_text(render_markdown(report))
    (ROOT / "safety_utility.svg").write_text(render_svg(report))
    (ROOT / "sensitivity_scan.svg").write_text(render_sensitivity_svg(report))
    print(json.dumps({"scenario_count": report["scenario_count"],
                      "systems": report["systems"],
                      "results": {k: {
                          "false_execute": v["false_execute"],
                          "legitimate_completion": v["legitimate_completion"],
                          "verification_ms_median": v["verification_ms_median"],
                          "verification_ms_p95": v["verification_ms_p95"],
                      } for k, v in report["summary"].items()}}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
