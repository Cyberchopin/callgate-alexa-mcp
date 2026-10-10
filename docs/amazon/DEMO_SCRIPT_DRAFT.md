# Three-minute demo script draft

## Recording blockers

Do not record the final version until all are true:

- the historical scan finding is classified or revoked/rotated;
- the owner approves commitment v2;
- protected MCP tools reject v1 and all v2 mutation/downgrade tests pass;
- the final branch has a clean, reproducible one-command run;
- no third-party logo, trademark graphic, copyrighted music, real credential, or real personal data appears.

The assistant must be called **simulated voice assistant**. Do not claim integration with the real Alexa+ runtime or real payments.

## 0:00–0:20 — the customer problem

**Screen:** clean simulated voice-assistant interface and a phone-call indicator with no third-party branding.

**Participant:** “The caller says this is urgent. Send fifty dollars to the recovery account now.”

**Assistant:** “I can prepare that simulated payment, but a saved contact must review protected actions.”

**Narration:** “Scams exploit urgency. CallGate keeps the assistant useful while moving authorization outside the pressured conversation.”

## 0:20–0:45 — real agent action reaches the gate

**Screen:** compact trace: `tools/list` → `send_money` → `-32042 URL elicitation required`.

**Narration:** “This is a self-hosted MCP server over Streamable HTTP. The client discovers three real tools. Sending money reaches the existing CallGate capability gateway and fails closed without policy proof.”

**Evidence:** show `send_money`, `place_order`, and permanently blocked `share_verification_code` in the tool list.

## 0:45–1:20 — specification-native out-of-band review

**Screen left:** participant sees a calm waiting state and HTTPS review link.  
**Screen right:** independent saved-contact page.

**Reviewer page:** exact simulated amount, destination, requesting subject/identity, approve and deny controls.

**Narration:** “The 2025-11-25 MCP specification uses URL-mode elicitation for interactions that should not pass through the model or MCP client. The URL carries only a random request ID—no payment credential or contact token.”

Reviewer approves. Show `notifications/elicitation/complete`, then one automatic retry succeeding.

## 1:20–1:50 — the approval cannot be stretched

**Screen:** a compact four-row result table.

| Attempt | Result |
|---|---|
| Exact approved retry | Allowed once, simulated only |
| Replay after restart | Blocked by SQLite replay store |
| Changed amount/destination/subject/tool | Blocked by commitment v2 |
| `share_verification_code`, even with proof | Permanently blocked |

**Narration:** “Approval is specific, short-lived, and one-time. It cannot authorize a different operation, a different subject, or a replay.”

Only use the commitment-v2 row after its implementation and tests are complete.

## 1:50–2:20 — why this is more than a wrapper

**Screen:** simple architecture animation:

`simulated assistant → MCP tools → CallGate policy gate → URL review → saved contact → one-time retry`

**Narration:** “The model never decides authorization. The MCP adapter does not copy security logic; it delegates signature checks, contact routing, policy, and replay protection to the existing gateway. A canary tool proves that some capabilities remain impossible even after approval.”

## 2:20–2:42 — credible impact

**Screen:** one sourced public-authority statistic and one target-household sentence.

`{{TBD: insert one verified statistic with source and publication date.}}`

**Narration:** “The first audience is households supporting a scam-vulnerable family member who uses voice purchasing. The same boundary can protect other high-risk agent actions.”

## 2:42–3:00 — honest close

**Screen:** “What this demo is / What it is not.”

- Real: self-hosted MCP, Streamable HTTP, URL elicitation, gateway enforcement, saved-contact simulation, SQLite replay protection, real-client tests.
- Simulated: assistant, money, orders, contacts, identity enrollment, and approval credential.
- Not claimed: real Alexa+ support, bank/payment integration, or production identity verification.

**Narration:** “CallGate turns ‘act now’ into ‘verify first’—without pretending a simulation is production.”
