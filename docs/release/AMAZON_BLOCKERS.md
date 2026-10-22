# Amazon blockers — 2026-10-21

Scope: only items that can stop a valid, recordable, judge-reproducible
submission by **2026-10-23 12:00 PM PDT**. No features were added.

## Fixed tonight (local branch `release/amazon-final-20261021`, not pushed)

| ID | Blocker on `main` `6f83951` | Fix | Verification |
|---|---|---|---|
| X-1 | **The review page could not open in a Windows browser.** The development TLS certificate used Ed25519. Python/OpenSSL (tests) accepts it; Windows Schannel and Chrome do not. Windows `curl.exe`: `schannel: failed to receive handshake` | `integrations/alexa_mcp/phase2.py` now generates an ECDSA P-256 key signed with SHA-256. The issuer and reviewer Ed25519 signing keys are unchanged | New test `test_development_certificate_uses_browser_compatible_key` (RED, then GREEN). Windows `curl.exe` gets HTTP 200, and approve/deny POSTs work from Windows |
| X-2 | **The one-command launcher hid the contact credential.** `run_amazon_services.py` generated a random token and never printed it, so nobody could approve on the review page | Added `--contact-token` and print the simulated credential | `test_launcher_and_client_complete_the_recorded_demo` |
| X-3 | **No visible MCP client for the video.** The live chain existed only inside pytest. `/demo` is a static fixture page | New `scripts/amazon_live_demo.py`, a scripted MCP client with interactive (browser) and rehearsal modes, restricted to loopback URLs | Full chain passed in rehearsal mode and with decisions posted from Windows; new e2e test |
| X-4 | **The dependency audit fails today.** PYSEC-2026-4320, certifi 2026.7.22 (compromised emSign intermediates). The scheduled audit (Mondays 09:23 UTC) would turn `main` red on 2026-10-26, during judging | Pinned `certifi==2026.10.19` in `requirements-lock.txt` and `requirements-integrations-lock.txt` | `pip_audit` on both CI-audited files: no known vulnerabilities |

Also changed: the README gains a short cross-platform "watch the full chain"
section.

## Added 2026-10-22 to strengthen the entry (not blockers)

| ID | Change | Why | Verification |
|---|---|---|---|
| E-1 | Live simulated-assistant page (`integrations/alexa_mcp/assistant.py`, `ui/live.*`), started by the launcher on `--assistant-port` | Judging weighs Design ("complete, coherent product experience"). The old video was a terminal plus a static fixture | 4 e2e tests; driven from Windows; headless Edge screenshots |
| E-2 | Review page shows dollars and UTC times instead of raw cents and epoch seconds | The contact must understand the request at a glance | New UI test |
| E-3 | Devpost cites a primary-source statistic (FTC, Dec 1 2025) | Potential Impact criterion; the old draft had an unfilled `{{SOURCE_NEEDED}}` | Checked on ftc.gov |

Full suite on the branch: 298 passed, 3 skipped. Node: 3/3. Claim registry:
consistent. Both CI-audited dependency files: no known vulnerabilities. Gateway
authorization, policy, and replay code are unchanged.

## Remaining — owner action required

### B-1 (critical): Publish the fixes to `main` before recording

- **Why:** the rules require the repository to contain everything needed to make the project work. Judges cloning `main` today hit X-1 and X-2. The video and the Devpost "Try it" commands assume the branch.
- **Action:** approve one of these.
  - **(a) Recommended.** I push `release/amazon-final-20261021`, open a PR, wait for the Ubuntu, Windows, and secret-scan jobs, and you merge.
  - **(b)** You push and merge it yourself.
- **Deadline:** by 2026-10-22 evening, so there is time to fix a red CI run.
- **If not merged:** record from the local branch, and remove the "Try it" live-client commands from the Devpost text.

### B-2 (critical): Record and upload the video

- **Action:** follow `AMAZON_DEMO_RUNBOOK.md`. Do one rehearsal take first; it doubles as the interactive Chrome check. Rendering already passed in headless Edge (gate F11). Upload to YouTube or Vimeo as **Public**, under 3:00.
- **Why:** this is a required field. Judges may score only the text, images, and video.

### B-3 (critical): Complete owner-only fields and submit on Devpost

In `AMAZON_FINAL_DEVPOST.md`:

- Eligibility: age of majority and eligible residence, no sponsor/judge conflict, and registration on the hackathon page.
- Confirm no off-repo CallGate work predates 2026-08-31. Disclose any other hackathon that used this code.
- Answer "Would you build with it again?" for each tool.
- Decide on mini challenges. Recommended: none.
- Paste the video URL.
- Submit by **2026-10-22 internal target**. The hard deadline is 2026-10-23 12:00 PM PDT. After it, do not modify the submission.

## Not blocking (recorded, deliberately not fixed tonight)

- `requirements-integrations-lock.txt` pins `pillow 12.3.0` (CVE-2026-112396, fix in 13.0.0). This file is for optional Pipecat/Silero extras only; CI does not install or audit it, and the MCP demo does not use it. A major-version bump is not worth the risk before the deadline.
- `docs/amazon/FINAL_GATE.md`, `SUBMISSION_SCORECARD.md`, `DEMO_SCRIPT.md`, and `DEVPOST.md` contain stale statuses and `{{…}}` placeholders. They are historical; `docs/release/*` supersede them. Judges are unlikely to open them.
- The README ends with a note that canonical tool-parameter binding (commitment v2) is not implemented. That is accurate, and the release docs do not claim v2.
- `scripts/demo.ps1 -Offline` rewrites `docs/amazon/merchant_injection_results.json`. The content is deterministic and identical, but on Windows it may show as modified. The runbook writes to `.test-tmp/` instead.
- The Windows clone `C:\Users\wangs\callgate-alexa-mcp` is at `f18eda5` with many uncommitted changes. Do not use it. Nothing in it was touched.
- Gitleaks has not run locally on the branch. CI runs it automatically if the branch is pushed (B-1).
