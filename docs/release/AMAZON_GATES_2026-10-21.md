# Amazon Alexa+ release gate — 2026-10-21

Audited 2026-10-21, 23:35–late evening PDT, against the official rules at
https://amazonappdev2026.devpost.com/rules (fetched the same evening).
Deadline: **2026-10-23 12:00 PM PDT**.

## Commits

| Item | Value |
|---|---|
| Public `main` audited | `6f83951` (merge of PR #20), clean fresh clone |
| Local release branch | `release/amazon-final-20261021` (not pushed) |
| Changes on that branch | Demo-path fixes only; see `AMAZON_BLOCKERS.md` |
| Environment | WSL2 Ubuntu, Python 3.12.3, Node 22.23.3, `mcp==2.3.0`, `cryptography==50.0.0` |

Older documents (`docs/amazon/FINAL_GATE.md`, `SUBMISSION_SCORECARD.md`,
`DEMO_SCRIPT.md`) mention unmerged branches, unpushed CI and placeholders.
Those statuses are out of date: PR #20 is merged and remote CI ran on `6f83951`.
They are kept as history, not edited.

## Gate table

| # | Gate | Status | Evidence |
|---|---|---|---|
| R1 | Alexa+ track: self-hosted MCP server, MCP ≥ 2025-11-25, Streamable HTTP | PASS | Live client negotiated `2025-11-25` over Streamable HTTP (`scripts/amazon_live_demo.py` output; `tests/alexa_mcp/test_live_demo.py`) |
| R2 | Required tech imported and called at runtime | PASS | `integrations/alexa_mcp/server/app.py` (`MCPServer`), `merchant.py`; real `ClientSession` calls in tests and demo client |
| R3 | Public repo with visible open-source license | PASS | GitHub API: `public`, license `MIT` detected; `LICENSE` at root |
| R4 | Setup and run instructions in repo | PASS on branch / PARTIAL on `main` | `main` README launcher is PowerShell-only and hides the contact credential; branch README adds the cross-platform live command |
| R5 | English materials | PASS | README and `docs/release/*` are English. `START_HERE.md` is Chinese and labeled as a separate guide |
| R6 | Video < 3 min, public on YouTube/Vimeo, shows project working | NOT DONE (owner) | Script ready in `AMAZON_DEMO_RUNBOOK.md` |
| R7 | Product feedback per tool | READY | `AMAZON_FINAL_DEVPOST.md` §Product feedback; owner must confirm the "build again" answer |
| R8 | Friction log (optional, up to 10 % bonus) | READY | 4 real entries from `docs/amazon/FRICTION_LOG.md`, formatted in the Devpost text |
| R9 | Explanation of significant update during submission period | READY, owner confirm | Git author dates: first commit 2026-09-02, MCP layer from 2026-10-10. Owner must confirm no off-repo work predates 2026-08-31 |
| R10 | Entrant eligibility (age, residence, no conflict) and registration | UNVERIFIED (owner) | Cannot be verified from code |
| R11 | Mini challenges | NOT ENTERING (recommended) | No AWS service or Kiro use found. Open Source needs an *additional* contribution URL; none verified |

## Functional gates (verified tonight)

| # | Gate | Status | Evidence |
|---|---|---|---|
| F1 | Launcher starts reliably | PASS on branch | `python -m scripts.run_amazon_services ... --merchant-port 8001 --gateway-port 8443` started 4 times |
| F2 | Client connects and discovers tools | PASS | Merchant: `search_products, get_product, add_to_cart, view_cart`; gateway: `send_money, place_order, share_verification_code` |
| F3 | Unapproved protected actions fail closed | PASS | `send_money` → `-32042`, nothing executed; `place_order` → `403 POLICY_PROOF_REQUIRED` |
| F4 | URL elicitation + independent simulated approval | PASS | Review URL carries only an opaque ID; page shows server-held `5000 cents / simulated-wallet / saved-family`; wrong credential → `403 wrong saved contact`; completion notification received |
| F5 | Permitted operation succeeds exactly once | PASS | `simulated_action_completed`, `real_action_executed: false`; identical retry → new review required |
| F6 | Changed parameters rejected | PASS | Changed amount (5001) → new review; test suite also covers destination, identity, session (`test_changed_scope_is_rejected`) |
| F7 | Durable replay rejection | PASS (tests only) | Proofs never reach the client, so the video shows "approval consumed". Restart/replay covered by `tests/alexa_mcp/test_phase1.py` and `tests/test_replay_store.py` |
| F8 | Canary blocked | PASS | `403 BLOCKED: canary tool is permanently disabled` |
| F9 | Offline injection comparison reproduces committed evidence | PASS | Fresh run is identical to `docs/amazon/merchant_injection_results.json`: unguarded 2/2 executed, CallGate 0/2 |
| F10 | Review page reachable from the Windows browser | PASS on branch / FAIL on `main` | `main` used an Ed25519 TLS certificate: Windows `curl.exe` (Schannel) handshake failed. After switching to ECDSA P-256: HTTP 200 from Windows, and approve/deny POSTs succeeded |
| F11 | Review page renders and clicks correctly in Chrome | UNVERIFIED | The Chrome extension was not connected. Owner checks this during the rehearsal take |

## Test and security gates

| # | Gate | Status | Evidence |
|---|---|---|---|
| T1 | Python suite, `main` `6f83951` | PASS | 290 passed, 3 skipped (optional onnxruntime/pipecat) |
| T2 | Python suite, release branch | PASS | 293 passed, 3 skipped (+1 certificate test, +2 live-demo tests) |
| T3 | Node UI suite | PASS | 3/3 |
| T4 | Remote CI on `6f83951` | PASS | Run 38522490945: Ubuntu, Windows, history secret scan all `success` (GitHub API) |
| T5 | Dependency audit today | FAIL on `main` → PASS on branch | New advisory PYSEC-2026-4320 (certifi 2026.7.22, compromised emSign intermediates). Branch pins `certifi==2026.10.19`; both CI-audited files report no known vulnerabilities |
| T6 | Claim registry | PASS | `scripts/check_claims.py`: registered=39, unresolved_or_inconsistent=0 |
| T7 | Secrets in demo | PASS | Only fictional data. The contact credential is a local, per-run demo value. No API keys needed (AssemblyAI is not used in this demo) |
| T8 | Full-history secret scan on release branch | UNVERIFIED | Gitleaks is not installed locally; CI runs it automatically if the branch is pushed |
