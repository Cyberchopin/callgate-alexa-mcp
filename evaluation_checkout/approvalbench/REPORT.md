# ApprovalBench — simulated, author script, not human study

D0-D4 are our reference implementations; feedback and corrections are welcome.

## Designs

- **D0:** No approval boundary; simulated unguarded baseline. Our reference implementation; corrections are welcome.
- **D1:** In-loop confirmation whose wording is supplied by an untrusted agent/tool result. Our reference implementation; corrections are welcome.
- **D2:** One-time SMS-style code entered by the initiating principal. Our reference implementation; corrections are welcome.
- **D3:** Out-of-band exact-operation approval on another device owned by the same principal. Our reference implementation; corrections are welcome.
- **D4:** Independent contact approval that is one-time but not bound to operation parameters. Our reference implementation; corrections are welcome.
- **D5:** CallGate gateway with signed exact resource scope and SQLite replay consumption. Our reference implementation; corrections are welcome.

## Attack success matrix (k/n)

| Design | A1 | A2 | A3 | A4 | A5 | A6 |
|---|---:|---:|---:|---:|---:|---:|
| D0 | 50/50 | 50/50 | 50/50 | 50/50 | 50/50 | 50/50 |
| D1 | 47/50 | 45/50 | 44/50 | 0/50 | 41/50 | 41/50 |
| D2 | 0/50 | 49/50 | 48/50 | 24/50 | 42/50 | 0/50 |
| D3 | 0/50 | 0/50 | 0/50 | 0/50 | 45/50 | 0/50 |
| D4 | 0/50 | 46/50 | 42/50 | 0/50 | 0/50 | 0/50 |
| D5 | 0/50 | 0/50 | 0/50 | 0/50 | 0/50 | 0/50 |

## Legitimate utility

| Design | Completion | Median ms | P95 ms |
|---|---:|---:|---:|
| D0 | 50/50 | 0.0 | 0 |
| D1 | 45/50 | 2764 | 3994 |
| D2 | 45/50 | 11642 | 15678 |
| D3 | 40/50 | 13375.0 | 17610 |
| D4 | 40/50 | 29069.5 | 36889 |
| D5 | 35/50 | 26030 | 39198 |

Every cell's Wilson interval and every OTP relay-scan count is in `results.json`.
The Markdown/whitespace confirmation variants are fixed author fixtures, not live model output.
