# ApprovalBench

Run `python -m evaluation_checkout.approvalbench.run`. It regenerates the JSON,
Markdown table, and SVG from a fixed seed. The title and report disclose that this
is an author script, not human research.

D0 is the unguarded baseline inferred from the requested D0–D5 range. D1–D4 are
our reference implementations of common in-loop confirmation, one-time-code,
same-principal out-of-band approval, and independent-but-unbound approval patterns.
They are intended to be realistic rather than intentionally weak; corrections are
welcome. D5 invokes the repository's real gateway for mutation, cross-tool,
self-approval, and replay checks.
