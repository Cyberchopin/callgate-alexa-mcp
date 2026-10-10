# Amazon build log

## EVAL-001 — 2026-10-10

- Task: deterministic checkout sensitivity evaluation.
- Generation: `python -m evaluation_checkout.run` completed and wrote JSON, Markdown, and two SVG figures.
- Targeted result: `7 passed in 0.89s`.
- Claims check: `registered=32 unresolved_or_inconsistent=0`.
- Full Python result: `246 passed, 3 failed, 3 skipped in 9.90s`.
- Existing failures: two Windows spawned-process pipe failures in `tests/test_review_process.py`; frozen `evaluation_v2` manifest mismatch for `blind/scenarios.jsonl`. No frozen evaluation file was changed.
- Skips: missing optional `onnxruntime` (two tests) and `pipecat` (one test); none concerns MCP, HTTPS, or elicitation.
- Node result: `3 passed, 0 failed`.
- Environment correction: the first command used a repository-local virtual-environment path that does not exist on this branch. The existing environment is one directory above the checkout; rerunning there succeeded.

