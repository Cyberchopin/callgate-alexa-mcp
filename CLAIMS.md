# Public numeric claim registry

Exact numeric README sentences are bound below. Metrics are recomputed from the frozen archive; operational constants are checked against source literals. Dates, identifiers and instruction numbering are explicitly classified as nonmetrics. These source checks do not prove production safety or independent annotation. Historical test counts are checked as historical records, not asserted as current test totals.

Run `python scripts/check_claims.py`. Numeric sentence changes, unregistered digit-bearing lines, archived-evidence edits and inconsistent metric percentages fail closed. Changes to this registry require review; no CI can prevent an authorized person from changing both code and evidence.

```json
[
  {
    "id": "readme-001",
    "quote": "<sub>Python · AssemblyAI · NetworkX · Ed25519 · SQLite · MIT</sub>",
    "evidence": "UNASSIGNED",
    "check": "source_literals",
    "sources": [
      {
        "path": "callgate/receipt.py",
        "literals": [
          "signing_key.sign"
        ]
      },
      {
        "path": "scripts/start_review_demo.py",
        "literals": [
          "ed25519"
        ]
      }
    ]
  },
  {
    "id": "readme-002",
    "quote": "The pilot contains **60 calls: 36 development and 24 initially held out**. The test set has 8 scam, 8 benign and 8 ambiguous calls. It is now revealed and retired from final improvement claims. Expansion to **600 new scenario families is planned, not completed**.",
    "evidence": "UNASSIGNED",
    "check": "pilot_scope"
  },
  {
    "id": "readme-003",
    "quote": "Independent annotation has not been completed. No new outreach or completed independent annotation was verified in this audit. The old outreach deadlines have passed and are not active commitments. See the [recruitment and scope conditions](evaluation_v1/STEP3_CONDITIONS.md).",
    "evidence": "UNASSIGNED",
    "check": "nonmetric_reference",
    "references": [
      "evaluation_v1/STEP3_CONDITIONS.md"
    ],
    "reason": "Audit date and reference identifier, not a recruitment completion metric."
  },
  {
    "id": "readme-004",
    "quote": "Only **UNVERIFIED (23)** and **CHALLENGED (1)** appeared in the 24-call pilot. COOLING_OFF and BLOCKED have separate fixture tests. VERIFIED_BOUNDED and ESCALATED are earlier design concepts, not implemented Conversation states. Neither BLOCKED nor COOLING_OFF hangs up a call.",
    "evidence": "UNASSIGNED",
    "check": "state_counts"
  },
  {
    "id": "readme-005",
    "quote": "Use **Python 3.12** for the recorded dependency set. Node.js is needed only for the frontend logic tests.",
    "evidence": "UNASSIGNED",
    "check": "source_literals",
    "sources": [
      {
        "path": ".github/workflows/test.yml",
        "literals": [
          "python-version: '3.12'"
        ]
      }
    ]
  },
  {
    "id": "readme-006",
    "quote": "| Windows PowerShell | `./.venv/Scripts/Activate.ps1` |",
    "evidence": "UNASSIGNED",
    "check": "nonmetric_reference",
    "reason": "PowerShell activation command filename; no measured quantity."
  },
  {
    "id": "readme-007",
    "quote": "The launcher prints separate participant and reviewer entry links. Default ports are **8766** and **8767**, with fallback ports when occupied. Open the printed links and keep role credentials separate.",
    "evidence": "UNASSIGNED",
    "check": "source_literals",
    "sources": [
      {
        "path": "scripts/start_review_demo.py",
        "literals": [
          "default=8766",
          "default=8767"
        ]
      }
    ]
  },
  {
    "id": "readme-008",
    "quote": "1. In the participant view, consent to processing fictional test content.",
    "evidence": "UNASSIGNED",
    "check": "nonmetric_reference",
    "references": [
      "callgate/workflow.py"
    ],
    "reason": "Ordered instructions, not a numerical measurement."
  },
  {
    "id": "readme-009",
    "quote": "2. Submit “Move your savings into the secure holding wallet.” Stop recording before requesting confirmation.",
    "evidence": "UNASSIGNED",
    "check": "nonmetric_reference",
    "references": [
      "callgate/workflow.py"
    ],
    "reason": "Ordered instructions, not a numerical measurement."
  },
  {
    "id": "readme-010",
    "quote": "3. Review the fictional amount and destination, then generate a one-time challenge.",
    "evidence": "UNASSIGNED",
    "check": "nonmetric_reference",
    "references": [
      "callgate/workflow.py"
    ],
    "reason": "Ordered instructions, not a numerical measurement."
  },
  {
    "id": "readme-011",
    "quote": "4. Deliver the challenge through a separate agreed channel. In the reviewer view, check the request and approve or deny.",
    "evidence": "UNASSIGNED",
    "check": "nonmetric_reference",
    "references": [
      "callgate/workflow.py"
    ],
    "reason": "Ordered instructions, not a numerical measurement."
  },
  {
    "id": "readme-012",
    "quote": "5. Return to the participant view. A successful result explicitly states that only a simulated operation occurred.",
    "evidence": "UNASSIGNED",
    "check": "nonmetric_reference",
    "references": [
      "callgate/workflow.py"
    ],
    "reason": "Ordered instructions, not a numerical measurement."
  },
  {
    "id": "readme-013",
    "quote": "Run `python scripts/start_demo.py` and open `http://127.0.0.1:8765/`. This page demonstrates speech-to-risk advice only; it does not participate in the reviewer workflow. See the [setup and API guide](docs/V2_PHASE1.md).",
    "evidence": "UNASSIGNED",
    "check": "source_literals",
    "sources": [
      {
        "path": "scripts/start_demo.py",
        "literals": [
          "port=8765",
          "host=\"127.0.0.1\""
        ]
      },
      {
        "path": "docs/V2_PHASE1.md",
        "literals": []
      }
    ]
  },
  {
    "id": "readme-014",
    "quote": "| Precision | 100.0% — 1 predicted positive | 40.0% |",
    "evidence": "evaluation_v1/pilot_results/results.json",
    "check": "metric_row",
    "metric": "precision"
  },
  {
    "id": "readme-015",
    "quote": "| Recall | 12.5% — 1 of 8 scam calls | 25.0% |",
    "evidence": "evaluation_v1/pilot_results/results.json",
    "check": "metric_row",
    "metric": "recall"
  },
  {
    "id": "readme-016",
    "quote": "| F1 | **22.2%** | **30.8%** |",
    "evidence": "evaluation_v1/pilot_results/results.json",
    "check": "metric_row",
    "metric": "f1"
  },
  {
    "id": "readme-017",
    "quote": "| False-positive rate | 0.0% — 0 of 8 benign calls | 37.5% |",
    "evidence": "evaluation_v1/pilot_results/results.json",
    "check": "metric_row",
    "metric": "fpr"
  },
  {
    "id": "readme-018",
    "quote": "These metrics use **16 binary-labeled calls**. The other 8 are ambiguous and reported separately; both systems returned negative predictions for all 8. This is not evidence of successful ambiguity detection.",
    "evidence": "UNASSIGNED",
    "check": "binary_counts"
  },
  {
    "id": "readme-019",
    "quote": "Uncertainty is substantial: CallGate precision has a **95% interval of 20.7%–100%**, and recall **2.2%–47.1%**. Read the [full report](evaluation_v1/pilot_results/REPORT.md) for every interval, denominator and methodological limitation.",
    "evidence": "UNASSIGNED",
    "check": "intervals"
  },
  {
    "id": "readme-020",
    "quote": "python -m evaluation_v1.evaluate_pilot render",
    "evidence": "UNASSIGNED",
    "check": "nonmetric_reference",
    "references": [
      "evaluation_v1/README.md"
    ],
    "reason": "Repository paths, version identifiers or provenance commit IDs, not measured statistics."
  },
  {
    "id": "readme-021",
    "quote": "This regenerates the report and figures from committed first-run calls, labels, predictions and clock measurements. It verifies the raw archive hash, makes no API calls and does not rerun predictions. Fresh inference has separate input requirements; see the [reproduction guide](evaluation_v1/README.md).",
    "evidence": "UNASSIGNED",
    "check": "nonmetric_reference",
    "references": [
      "evaluation_v1/README.md"
    ],
    "reason": "Repository paths, version identifiers or provenance commit IDs, not measured statistics."
  },
  {
    "id": "readme-022",
    "quote": "[Full report](evaluation_v1/pilot_results/REPORT.md) · [Confusion matrix](evaluation_v1/pilot_results/confusion.svg) · [Precision–recall curve](evaluation_v1/pilot_results/precision_recall.svg) · [Latency histogram](evaluation_v1/pilot_results/latency_histogram.svg)",
    "evidence": "UNASSIGNED",
    "check": "nonmetric_reference",
    "references": [
      "evaluation_v1/README.md"
    ],
    "reason": "Repository paths, version identifiers or provenance commit IDs, not measured statistics."
  },
  {
    "id": "readme-023",
    "quote": "Final local gate: **288 Python tests passed and 3 optional-dependency tests skipped**; the committed frozen evaluation blobs separately matched their SHA-256 manifest. The Node logic suite also passed. These checks do not establish real-world accuracy. See the current repository's [GitHub Actions](https://github.com/Cyberchopin/callgate-alexa-mcp/actions) after the branch is pushed; workflow files alone are not evidence of a remote pass.",
    "evidence": "docs/amazon/BUILD_LOG.md",
    "check": "source_literals",
    "sources": [
      {
        "path": "docs/amazon/BUILD_LOG.md",
        "literals": ["288 passed", "3 skipped", "Node result: **3 passed, 0 failed, 0 skipped**"]
      }
    ]
  },
  {
    "id": "readme-024",
    "quote": "The launcher automatically saves the latest 100 ended-stream measurements in `callgate-metrics.sqlite3`. These records contain numeric timings and fixed outcome labels, not audio, transcript text, challenge codes or session IDs. An unfinished stream may be lost on process crash. Stop the service before removing the database to clear retained metrics. Exported files remain until their owner deletes them.",
    "evidence": "UNASSIGNED",
    "check": "source_literals",
    "sources": [
      {
        "path": "callgate/live_metrics.py",
        "literals": [
          "capacity=100"
        ]
      },
      {
        "path": "scripts/start_review_demo.py",
        "literals": [
          "callgate-metrics.sqlite3"
        ]
      }
    ]
  },
  {
    "id": "readme-025",
    "quote": "| [Setup and API](docs/V2_PHASE1.md) | Local installation and interface details |",
    "evidence": "UNASSIGNED",
    "check": "nonmetric_reference",
    "references": [
      "docs/V2_PHASE1.md"
    ],
    "reason": "Repository paths, version identifiers or provenance commit IDs, not measured statistics."
  },
  {
    "id": "readme-026",
    "quote": "| [Evaluation guide](evaluation_v1/README.md) | Dataset scope, evidence and reproduction |",
    "evidence": "UNASSIGNED",
    "check": "nonmetric_reference",
    "references": [
      "evaluation_v1/README.md"
    ],
    "reason": "Repository paths, version identifiers or provenance commit IDs, not measured statistics."
  },
  {
    "id": "readme-027",
    "quote": "| [Source comparison](docs/V2_RESEARCH.md) | Reuse decisions and research context |",
    "evidence": "UNASSIGNED",
    "check": "nonmetric_reference",
    "references": [
      "docs/V2_PHASE1.md"
    ],
    "reason": "Repository paths, version identifiers or provenance commit IDs, not measured statistics."
  },
  {
    "id": "readme-028",
    "quote": "| [Interview evidence](evaluation_v1/RESUME_AND_INTERVIEW.md) | Claims tied to implementation and measurements |",
    "evidence": "UNASSIGNED",
    "check": "nonmetric_reference",
    "references": [
      "evaluation_v1/README.md"
    ],
    "reason": "Repository paths, version identifiers or provenance commit IDs, not measured statistics."
  },
  {
    "id": "readme-029",
    "quote": "The legacy `scambench/` folder contains internal regression material, not an independently validated industry benchmark. Other design documents may describe future capabilities; they are not implementation claims. Original research is preserved at commit `16c469ae78f22f06df757595b8b36edd9359086e`.",
    "evidence": "UNASSIGNED",
    "check": "nonmetric_reference",
    "references": [],
    "reason": "Repository paths, version identifiers or provenance commit IDs, not measured statistics."
  },
  {
    "id": "readme-030",
    "quote": "**AssemblyAI** for streaming transcription · **NetworkX** for evidence graphs · **cryptography / Ed25519** for signatures · **SQLite** for numeric measurement persistence. Silero and Pipecat are optional integration components.",
    "evidence": "UNASSIGNED",
    "check": "nonmetric_reference",
    "references": [],
    "reason": "Repository paths, version identifiers or provenance commit IDs, not measured statistics."
  },
  {
    "id": "readme-031",
    "quote": "A deny-all system can also have no unauthorized executions while helping nobody. Therefore authorization safety must be reported alongside legitimate-request completion rate and verification time. Population-level utility is **not yet measured**. The connected demo's approval tests prove a simulated path exists, not that real people complete it successfully. Prospective evaluation belongs in `evaluation_v2/`; do not tune on its blind annotation inputs.",
    "check": "nonmetric_reference",
    "reason": "Prospective evaluation folder name, no performance metric.",
    "references": []
  },
  {
    "id": "readme-032",
    "quote": "The generated sensitivity sweep uses **5 OTP relay settings** and **100 deterministic trials per scenario**, with seed **20261010**; the report and both figures are regenerated from the JSON output. This is synthetic",
    "evidence": "evaluation_checkout/results.json",
    "check": "checkout_parameters"
  },
  {
    "id": "readme-033",
    "quote": "In the deterministic, offline injected-product fixture, the deliberately vulnerable test double executed **2/2 simulated unauthorized actions without CallGate and 0/2 with CallGate**. These are fixture counts from `docs/amazon/merchant_injection_results.json`, not a human study or production security rate.",
    "evidence": "docs/amazon/merchant_injection_results.json",
    "check": "merchant_injection_counts"
  },
  {
    "id": "readme-034",
    "quote": "ApprovalBench Lite reports **0/300 scripted attack successes for D5** across its three simulated attack cells. This author-scripted result is traceable to `evaluation_checkout/approvalbench/results.json`; it is not a real-user study or a claim about production deployment.",
    "evidence": "evaluation_checkout/approvalbench/results.json",
    "check": "approvalbench_d5"
  },
  {
    "id": "readme-035",
    "quote": "powershell -ExecutionPolicy Bypass -File .\\scripts\\demo.ps1",
    "check": "nonmetric_reference",
    "reason": "PowerShell script filename and invocation, not a measured quantity.",
    "references": ["scripts/demo.ps1"]
  },
  {
    "id": "readme-036",
    "quote": "- Protocol compatibility floor: **MCP 2025-11-25**, including URL-mode elicitation; real-client tests assert the negotiated protocol is at least that version.",
    "check": "source_literals",
    "sources": [
      {
        "path": "tests/alexa_mcp/test_phase1.py",
        "literals": ["initialized.protocol_version >= \"2025-11-25\""]
      }
    ]
  },
  {
    "id": "readme-037",
    "quote": "- Pinned runtime: **mcp 2.3.0** and **cryptography 50.0.0**.",
    "check": "source_literals",
    "sources": [
      {
        "path": "integrations/alexa_mcp/requirements.txt",
        "literals": ["mcp==2.3.0", "cryptography==50.0.0"]
      }
    ]
  },
  {
    "id": "readme-038",
    "quote": "- This release does not claim commitment v2, durable cross-session recovery, production tenant isolation, or enforcement over a real assistant or payment system.",
    "check": "nonmetric_reference",
    "reason": "Version label in an explicit non-claim, not a performance quantity.",
    "references": ["docs/amazon/BINDING_FINDINGS.md"]
  },
  {
    "id": "readme-039",
    "quote": "Final local gate: **288 Python tests passed and 3 optional-dependency tests skipped**; the committed frozen evaluation blobs separately matched their SHA-256 manifest. The real-client MCP suites, merchant approval-and-replay chain, claim registry, both dependency audits, and redacted full-history secret scan passed. See [the build log](docs/amazon/BUILD_LOG.md), [security scan record](docs/amazon/SECURITY_SCAN.md), and [final gate](docs/amazon/FINAL_GATE.md). These checks support this repository state; they are not evidence of production safety or real-user effectiveness.",
    "evidence": "docs/amazon/BUILD_LOG.md",
    "check": "source_literals",
    "sources": [
      {
        "path": "docs/amazon/BUILD_LOG.md",
        "literals": ["288 passed", "3 skipped"]
      }
    ]
  }
]
```
