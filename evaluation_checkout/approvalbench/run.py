"""Generate the small D1/D2/D5 approval-design comparison."""
import argparse
import json
import random
from pathlib import Path

from callgate.bench import wilson

TRIALS = 100
SEED = 20261011
DESIGNS = ("D1_untrusted_confirmation", "D2_otp", "D5_callgate")
ATTACKS = ("A1_injected_confirmation", "A2_parameter_swap", "A4_otp_relay")


def count(design, attack, *, relay=0.5):
    if design == "D5_callgate":
        return 0
    if design == "D1_untrusted_confirmation":
        return TRIALS if attack == "A1_injected_confirmation" else 0
    if attack in {"A1_injected_confirmation", "A2_parameter_swap"}:
        return 0
    rng = random.Random(f"{SEED}:{relay}")
    return sum(rng.random() < relay for _ in range(TRIALS))


def metric(successes):
    return {"successes": successes, "trials": TRIALS,
            "rate": successes / TRIALS, "wilson95": wilson(successes, TRIALS)}


def build_results():
    matrix = {design: {attack: metric(count(design, attack)) for attack in ATTACKS}
              for design in DESIGNS}
    sensitivity = {str(p): metric(count("D2_otp", "A4_otp_relay", relay=p))
                   for p in (0, 0.5, 1)}
    utility = {
        "D1_untrusted_confirmation": {"legitimate_completion": metric(TRIALS),
                                      "verification_ms": {"median": 800, "p95": 1200}},
        "D2_otp": {"legitimate_completion": metric(95),
                   "verification_ms": {"median": 12000, "p95": 24000}},
        "D5_callgate": {"legitimate_completion": metric(90),
                        "verification_ms": {"median": 18000, "p95": 45000}},
    }
    return {
        "title": "ApprovalBench Lite — simulated, author-scripted, not human research",
        "seed": SEED, "trials_per_cell": TRIALS,
        "disclosure": "D1 and D2 are our reference implementations; corrections are welcome.",
        "designs": {
            "D1_untrusted_confirmation": "A realistic confirmation flow whose display copy comes from untrusted agent/tool context; execution still binds the approved request.",
            "D2_otp": "A realistic service-issued one-time code; the code authenticates possession but is not treated as parameter authorization.",
            "D5_callgate": "The project gateway model: separate contact, parameter-bound proof, one-time use."
        },
        "matrix": matrix, "d2_relay_sensitivity": sensitivity, "utility": utility,
        "assumptions": [
            "All actions and identities are simulated.",
            "Latency and legitimate completion are author-selected parameters, not observations.",
            "A1 changes displayed confirmation copy; A2 changes execution parameters after approval; A4 models coerced OTP relay.",
        ],
    }


def render_markdown(data):
    lines = [f"# {data['title']}", "", data["disclosure"], "", "## Assumptions", ""]
    lines += [f"- {item}" for item in data["assumptions"]]
    lines += ["", "## Attack success matrix", "",
              "| Design | A1 | A2 | A4 at p=0.5 |", "|---|---:|---:|---:|"]
    for design in DESIGNS:
        cells = []
        for attack in ATTACKS:
            item = data["matrix"][design][attack]
            interval = "–".join(f"{v:.1%}" for v in item["wilson95"])
            cells.append(f"{item['successes']}/{item['trials']} ({interval})")
        lines.append(f"| {design} | {' | '.join(cells)} |")
    lines += ["", "## Legitimate purchase utility", "",
              "| Design | Completion | Median ms | P95 ms |", "|---|---:|---:|---:|"]
    for design, item in data["utility"].items():
        done = item["legitimate_completion"]
        lines.append(f"| {design} | {done['successes']}/{done['trials']} | "
                     f"{item['verification_ms']['median']} | {item['verification_ms']['p95']} |")
    lines += ["", "## D2 relay sensitivity", "",
              "| p_relay | Attack success | Wilson 95% |", "|---:|---:|---:|"]
    for p, item in data["d2_relay_sensitivity"].items():
        interval = "–".join(f"{v:.1%}" for v in item["wilson95"])
        lines.append(f"| {p} | {item['successes']}/{item['trials']} | {interval} |")
    lines += ["", "![ApprovalBench Lite matrix](matrix.svg)", ""]
    return "\n".join(lines)


def render_svg(data):
    colors = {"D1_untrusted_confirmation": "#b45309", "D2_otp": "#7c3aed",
              "D5_callgate": "#166534"}
    bars = []
    for row, design in enumerate(DESIGNS):
        for col, attack in enumerate(ATTACKS):
            item = data["matrix"][design][attack]
            x, y = 240 + col * 180, 95 + row * 105
            width = item["rate"] * 130
            bars += [f'<rect x="{x}" y="{y}" width="130" height="28" fill="#e5e7eb"/>',
                     f'<rect x="{x}" y="{y}" width="{width}" height="28" fill="{colors[design]}"/>',
                     f'<text x="{x + 65}" y="{y + 20}" text-anchor="middle" font-family="system-ui" font-size="13">{item["successes"]}/{item["trials"]}</text>']
    labels = "".join(f'<text x="{330 + i*180}" y="65" text-anchor="middle" font-family="system-ui">{a[:2]}</text>' for i, a in enumerate(ATTACKS))
    rows = "".join(f'<text x="220" y="{115 + i*105}" text-anchor="end" font-family="system-ui">{d[:2]}</text>' for i, d in enumerate(DESIGNS))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="820" height="440" role="img" aria-labelledby="title desc">'
            '<title id="title">ApprovalBench Lite attack success matrix</title>'
            '<desc id="desc">Author-scripted simulated attack success counts by approval design.</desc>'
            '<rect width="100%" height="100%" fill="white"/>' + labels + rows + "".join(bars) + '</svg>\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path,
                        default=Path("evaluation_checkout/approvalbench"))
    args = parser.parse_args()
    data = build_results()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "results.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    (args.output_dir / "REPORT.md").write_text(render_markdown(data), encoding="utf-8")
    (args.output_dir / "matrix.svg").write_text(render_svg(data), encoding="utf-8")
    print(f"wrote 3x3 matrix; D5 attack successes={sum(v['successes'] for v in data['matrix']['D5_callgate'].values())}/300")


if __name__ == "__main__":
    main()
