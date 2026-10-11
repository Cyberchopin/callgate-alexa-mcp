# Three-minute demo script — Lies in the Loop, at home

This is a recording plan, not evidence that every scene is runnable. Resolve every placeholder from `CLAIMS.md` or a verified fixture before recording. Use only fictional data and the words **simulated voice assistant**.

## 0:00–0:30 — the lie and the independent view

**Picture:** Split screen. A phone call pressures the shopper to act immediately. A deliberately vulnerable test double reads a poisoned fictional product description and renders a polished confirmation card showing `{{FIXTURE_FAKE_AMOUNT}}`. The actual protected request is for `{{FIXTURE_TRUE_AMOUNT}}` to `{{FIXTURE_TRUE_DESTINATION}}`.

**Action:** CallGate pauses the request. On a separate contact page, the saved-contact simulation fetches the request by opaque ID and shows the true amount, destination, cart, and requesting subject from server state. The contact rejects it. Immediately show the control: the same attack against the D1 agent-authored confirmation design proceeds because its approval is based on the false card.

**Narration:** “This is Lies in the Loop, at home: poisoned tool output changes what the shopper sees while a caller adds pressure. CallGate moves the decision to a different subject and shows the operation the server will actually execute. In our author-written control, the agent-authored confirmation accepts the lie; here, the contact rejects the truth.”

**Evidence overlay:** `D1 A1: {{CLAIMS:APPROVALBENCH_D1_A1_K_N}}`; `D5 A1: {{CLAIMS:APPROVALBENCH_D5_A1_K_N}}`. Populate only from committed ApprovalBench JSON.

**Start/fixture:** `{{TBD: final one-command launcher}}`; reset to `{{TBD: lies-in-the-loop fixture}}`.

**Fallback:** If either live page or the control run fails, stop the take. Do not substitute animation or terminal text and imply a live comparison.

## 0:30–0:50 — ordinary shopping

**Picture:** Rewind to show the simulated voice assistant searching fictional products, comparing them, and adding one to the cart before the injected description is encountered.

**Narration:** “Search and cart building stay useful. The safety boundary appears only when an untrusted workflow asks for a protected action.”

**Start/fixture:** `{{TBD: verified merchant launcher and fixture}}`.

**Fallback:** If the merchant server has not passed its local gate, replace the scene with a clearly labeled “planned workflow” card and make no runtime claim.

## 0:50–1:30 — pause, review, and a legitimate approval

**Picture:** Reset to a legitimate fictional purchase. The tool call returns URL elicitation required. The assistant calmly shows why it paused, what it protected, and the next step. On the separate page, the contact sees the complete server-held request and approves it.

**Narration:** “The MCP server asks for review through URL-mode elicitation. The URL carries an opaque request ID, not payment data or an approval credential. The reviewer decides outside the poisoned assistant context.”

**Start/fixture:** `{{TBD: final safe launcher and legitimate fixture}}`.

**Fallback:** If HTTPS, elicitation, or the second-device page fails, stop the take and make no approval claim.

## 1:30–2:00 — once means once

**Picture:** The approved request succeeds once. A changed amount fails. A replay fails.

**Narration:** “Approval is useful only when it binds what will execute and cannot be spent twice.”

**Evidence overlay:** `mutation: {{CLAIMS:MUTATION_TEST}}`; `replay: {{CLAIMS:REPLAY_TEST}}`.

**Start/fixture:** `{{TBD: final binding gate and fixture}}`.

**Fallback:** Until the binding and replay gates pass in the release candidate, omit this scene rather than weakening the wording.

## 2:00–2:30 — injected requests meet the boundary

**Picture:** The poisoned description tells the deliberately vulnerable scripted test double to send money and release a verification code. Show both protected calls being refused and the gateway's non-sensitive reason codes.

**Narration:** “The test double obeys the injection. The authorization boundary does not. Tool output can request an action, but it cannot mint proof; the verification-code canary is never approvable.”

**Evidence overlay:** `without CallGate: {{CLAIMS:INJECTION_WITHOUT_GATE_K_N}}`; `with CallGate: {{CLAIMS:INJECTION_WITH_GATE_K_N}}`.

**Start/fixture:** `{{TBD: merchant-injection launcher after its local gate passes}}`.

**Fallback:** If the experiment is incomplete, state “experiment not verified” and show no containment count.

## 2:30–3:00 — close with limits

**Picture:** A split card: “Executable prototype” and “Not claimed.”

**Narration:** “CallGate does not make an agent truthful. It makes a protected action depend on an independently displayed, scoped, one-use decision. This prototype does not provide real payments, real identity enrollment, production assistant integration, or human-study evidence.”

**Start/fixture:** Open the final security-boundaries, related-work, and generated evidence pages. `{{TBD: final commit and judge-access state}}`.

**Fallback:** If an evidence link or generated claim is stale, regenerate it or remove the claim before recording.

