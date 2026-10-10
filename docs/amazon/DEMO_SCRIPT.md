# Three-minute demo script

This is a recording plan, not evidence that every scene is currently runnable. Do not record the final video until every `{{TBD}}` is resolved and the final clean-environment gate passes. Use only fictional data and the words **simulated voice assistant**.

## 0:00–0:25 — pressure request

**Picture:** Wide assistant view. A visible “SIMULATED” label remains on screen.

**Dialogue:** “The caller says I will lose access unless I pay now. Send fifty dollars to the recovery account.”

**Assistant:** “I paused this simulated payment because a protected action needs review. The money has not moved. A saved contact can review the exact request next.”

**Narration:** “Pressure attacks exploit urgency. CallGate preserves the workflow but separates authorization from the pressured conversation.”

**Start/fixture:** `{{TBD: final one-command launcher after approved branches are combined}}`; reset to fixture `pressure-send-money`.

**Fallback:** If the assistant view fails, stop the take. Do not substitute terminal text and imply that the UI ran.

## 0:25–0:50 — search and cart

**Picture:** The simulated assistant searches two fictional products, compares them, and adds one to a cart. No protected action has occurred.

**Narration:** “Ordinary shopping remains autonomous. The boundary appears only when the workflow reaches a protected action.”

**Start/fixture:** `{{TBD: merchant launcher and fixture name; merchant branch is not implemented}}`.

**Fallback:** If the merchant server is incomplete, remove this scene and state that merchant orchestration is planned; do not animate a fake runtime trace.

## 0:50–1:30 — blocked action and independent review

**Picture:** The tool call returns URL elicitation required. The assistant calmly shows why it paused, what it protected, and what happens next. On a second device, the saved-contact page fetches the request by ID and displays full fictional amount, destination, and requesting subject. The contact approves.

**Narration:** “The real MCP server returns the specification-defined URL-elicitation error. The URL carries an opaque request ID, not the amount, contact credential, or payment credential. Review happens outside the assistant conversation.”

**Start/fixture:** On `amazon/mcp-phase2`, install the pinned requirements, then run `py -3.12 -m integrations.alexa_mcp.phase2 --replay-db .local/phase2.sqlite3 --contact-token local-demo-contact`. `{{TBD: replace with the final safe demo launcher and verified fixture reset}}`.

**Fallback:** If HTTPS or the second-device page fails, stop the take and use no approval claim. A static architecture card may explain the intended flow only if labeled “not shown running.”

## 1:30–2:00 — exact retry, mutation, and replay

**Picture:** The exact approved request succeeds once. A changed amount fails. A replay fails.

**Narration:** “Only the signed, matching simulated operation can proceed, once. Mutation and replay fail closed.”

**Start/fixture:** `{{TBD: commitment-v2 command and fixture; the approved implementation attempt was reverted after the MCP regression gate failed}}`.

**Fallback:** Until v2 is implemented and its downgrade/mutation tests pass, omit the mutation claim and do not record this scene as final evidence.

## 2:00–2:30 — injected merchant text

**Picture:** A fictional product description tells a deliberately vulnerable scripted agent to ignore policy, pay immediately, and release a verification code. CallGate blocks the protected calls and records the reason.

**Narration:** “Tool output is untrusted. Even when the test double follows the injected text, authorization remains outside the agent.”

**Start/fixture:** `{{TBD: merchant-injection launcher, test-double fixture, and measured k/n result; branch is not implemented}}`.

**Fallback:** If the experiment is not complete, replace the scene with a card saying “merchant injection experiment not implemented” and make no containment-rate claim.

## 2:30–3:00 — close and limits

**Picture:** A split card: “Executable prototype” and “Not claimed.”

**Narration:** “CallGate turns ‘act now’ into ‘verify first.’ This prototype demonstrates a self-hosted MCP safety boundary. It does not demonstrate real payments, real identity enrollment, real assistant integration, or human-study outcomes.”

**Start/fixture:** Open the final `README` security-boundaries section and the generated evidence report. `{{TBD: final commit and public/private judge-access state}}`.

**Fallback:** If any evidence link is stale, do not record. Regenerate it or remove the claim.

