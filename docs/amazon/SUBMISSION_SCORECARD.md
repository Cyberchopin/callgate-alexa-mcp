# Amazon submission scorecard

Last verified against the [official rules](https://amazonappdev2026.devpost.com/rules): 2026-10-10.

## Stage 1 — pass/fail gates

| Gate | Status | Evidence/action |
|---|---|---|
| Eligible entrant | `{{OWNER CONFIRM}}` | Confirm age of majority, eligible residence, and no Sponsor/Administrator/judge conflict. |
| Registered on Devpost | `{{OWNER CONFIRM}}` | Join the hackathon before submission. |
| Alexa+ track fit | READY ON ISOLATED BRANCH | Self-hosted MCP server on `amazon/mcp-phase2`; simulated assistant is described honestly. |
| MCP minimum version | READY ON ISOLATED BRANCH | 2025-11-25 URL elicitation behavior; pinned `mcp==2.3.0`; Streamable HTTP. |
| Required tech called at runtime | VERIFIED | Real MCP client connects, lists tools, and calls the server; 10 combined MCP tests pass. |
| Working repository and instructions | PARTIAL | One-command instructions exist; final combined branch/repository remains blocked by the historical scan finding and owner approval. |
| Public OSS license or private judge access | `{{OWNER DECISION}}` | Public requires a visible license; private requires the Devpost/Amazon collaborators listed in the rules. |
| English submission materials | PARTIAL | English README draft exists; final submission text/video captions remain. |
| Public demo video under 3 minutes | TODO | YouTube or Vimeo; show the running project. Do not use third-party logos or copyrighted music without permission. |
| Project available through judging | TODO | Keep repository and any test instructions usable through 2026-11-20 12:00 PT. |
| Significant-update explanation | READY ON ISOLATED BRANCH | Git-author-date reports on `amazon/tools`; regenerate after final combination. |

Do not publish or migrate while the three historical `generic-api-key` findings remain unclassified.

## Stage 2 — equally weighted criteria

### 1. Tech Implementation — target evidence

- Show Streamable HTTP MCP negotiation and the three returned tools on screen.
- Show `send_money` returning `-32042` URL elicitation with no proof.
- Show approval, completion notification, one successful retry, and replay rejection.
- Show SQLite replay rejection after process restart.
- Show `share_verification_code` blocked even with a valid proof.
- Do not record the final claim until commitment v2 is approved, implemented, and its downgrade test passes.

### 2. Design — target evidence

- Use one coherent story: a caller pressures the participant to pay immediately through a simulated voice assistant.
- Keep the participant experience calm: explain that a saved contact must review the exact request.
- On the independent review page, show amount, destination, requesting identity, approve/deny, and waiting state.
- End with a clear result rather than terminal output alone.

### 3. Potential Impact — target evidence

- Name one audience: households supporting an older or otherwise scam-vulnerable family member who uses voice purchasing.
- Cite one current primary/public-authority statistic; do not invent a number.
- Explain the deployment path and limits: simulated payments today, reusable authorization boundary for real integrations later.
- State what is not solved: identity enrollment, real payment integration, and real Alexa+ client support are not implemented.

### 4. Quality of the Idea — target evidence

- Lead with specification-native URL elicitation, not “another MCP wrapper.”
- Contrast ordinary agent autonomy with a non-bypassable capability gateway.
- Demonstrate cross-session/restart replay protection and the permanently blocked canary.
- After commitment v2 approval, demonstrate that changing tool, merchant/cart, subject, or signed parameters invalidates approval.

## Bonus and optional categories

- Friction log: include only real MCP SDK/specification/Alexa+/Devpost issues. Official rules allow up to a 10% judging bonus.
- Product feedback: answer all required questions for each used tool/SDK, including onboarding, what worked, what needs work, workaround, and whether you would use it again.
- Open Source mini challenge: `{{OWNER DECISION}}`; only enter with a meaningful public contribution URL and required explanation.
- AWS Builder: do not enter unless an AWS service or qualifying Kiro Crew use is real and documented.

## Final submission lock

- Deadline: **2026-10-23 12:00 PM Pacific Time**. Submit no later than 2026-10-22 internally.
- Judges may evaluate only the description, images, and video, so those three artifacts must independently communicate the problem, running proof, differentiation, and limitations.
- After the deadline the substantive submission cannot be changed.
