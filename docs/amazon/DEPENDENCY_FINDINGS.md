# Dependency upgrade findings

Date checked: 2026-10-11 (America/Los_Angeles).

## Decision

Upgrade `cryptography` from `46.0.5` to `50.0.0`.

PyPI lists `50.0.0` as released on 2026-07-31, so it is more than 14 days old at the time of this review. It is the first release that covers all six unique advisory IDs reported by the owner-run audit. The newer `50.0.2` release (2026-09-30) is less than 14 days old and is not needed to remediate these six findings. `50.0.1` was released on 2026-08-25. Release dates are from the [PyPI release history](https://pypi.org/project/cryptography/#history).

## Six unique advisories

| Advisory ID | Fixed version | Affected feature | Used by this repository? |
|---|---:|---|---|
| `PYSEC-2026-35` | `46.0.6` | X.509 verification of peer names against DNS name constraints ([upstream advisory](https://github.com/pyca/cryptography/security/advisories/GHSA-m959-cc7f-wv43)) | No. The repository generates a local development certificate but does not use `cryptography`'s X.509 path-verification API. |
| `PYSEC-2026-36` | `46.0.7` | Non-contiguous Python buffers passed to buffer-accepting APIs such as hash updates ([upstream advisory](https://github.com/pyca/cryptography/security/advisories/GHSA-p423-j2cm-9vmq)) | No affected call was found. CallGate passes ordinary byte strings to Ed25519 APIs. |
| `GHSA-537c-gmf6-5ccf` | `48.0.1` | Vulnerable OpenSSL bundled in PyPI wheels ([upstream advisory](https://github.com/pyca/cryptography/security/advisories/GHSA-537c-gmf6-5ccf)) | Potentially. This concerns the bundled runtime rather than one CallGate API. The dependency is used for Ed25519 and development-certificate generation. |
| `PYSEC-2026-3553` | `49.0.0` | Duplicate self-signed intermediates causing exponential X.509 path building ([upstream advisory](https://github.com/pyca/cryptography/security/advisories/GHSA-jwv3-5hgf-82ww)) | No. CallGate does not accept or build attacker-supplied certificate chains with the `cryptography` verifier. |
| `PYSEC-2026-3554` | `49.0.0` | Wildcard DNS SAN escaping a permitted-subtree constraint ([upstream advisory](https://github.com/pyca/cryptography/security/advisories/GHSA-m2h6-j472-rp4c)) | No. CallGate does not use `cryptography`'s X.509 path-verification API. |
| `PYSEC-2026-3552` | `50.0.0` | Distinguishable PKCS#7 enveloped-data decryption failures creating an oracle ([upstream advisory](https://github.com/pyca/cryptography/security/advisories/GHSA-g6cj-pr64-35w5)) | No. No PKCS#7 decrypt API is called. |

## Compatibility surface

The upgrade can affect two repository paths even though they do not exercise the vulnerable features:

1. Ed25519 key generation, signing, and verification in the existing confirmation, receipt, and verification flows.
2. Ed25519-backed self-signed certificate generation in the MCP HTTPS development path.

The upgrade therefore requires a committed Ed25519 verification vector generated under `46.0.5`, plus a certificate-generation and HTTPS-connection test under `50.0.0`. It does not authorize changes to signature payloads, contact selection, replay prevention, policy decisions, or the unapproved commitment-v2 work.

## Scanner scope

The owner-provided `pip-audit` output contained 11 rows because several records were aliases or repeated across inputs; this document tracks the six unique IDs above. Agent Scan remains postponed. Nothing in this branch should be described as an Agent Scan pass or as an external security certification.
