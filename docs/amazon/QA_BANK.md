# Judge Q&A bank

Each answer is designed to fit within roughly fifteen seconds when spoken naturally.

1. **Who installs this?**  A household or care organization would operate the gateway and enroll its own trusted reviewers. This prototype simulates enrollment; it does not verify real people.

2. **Why not use OTP or 3-D Secure?**  Those controls help, but a pressured victim may relay a code or approve a prompt. CallGate tests a separate reviewer who sees the exact operation outside that conversation; it complements rather than replaces payment controls.

3. **Why is default denial an accomplishment?**  By itself, it is not. We report legitimate completion and delay alongside false execution so a deny-all system is visibly useless.

4. **What if the saved contact is compromised?**  That is an explicit boundary. One compromised reviewer can approve requests assigned to them; production would need stronger enrollment, recovery, and possibly multiple reviewers.

5. **Why is `subject` simulated?**  The prototype has no production identity provider. It tests binding behavior with a stable fictional subject identifier, not proof of a human identity.

6. **Is this integrated with a real Alexa+ runtime?**  No. It is a real self-hosted MCP server plus a simulated voice-assistant experience. We do not claim real Alexa+ client support.

7. **Where does private data go?**  In the prototype, pending request data stays in the local server database. The review URL uses an opaque ID. We do not send payment data to an LLM for authorization.

8. **Does the model decide whether money moves?**  No. The model may request a tool, but deterministic gateway policy, signed proof checks, contact routing, and replay consumption decide whether the simulated action is allowed.

9. **Can approval be reused for another tool?**  That is the commitment-v2 goal. The first implementation attempt was reverted after its MCP regression gate failed, so we will not make this final claim until the replacement passes.

10. **Why use URL elicitation?**  It is the MCP-native way to direct sensitive interaction outside the ordinary model/client exchange, while letting the server notify the initiating session when review completes.

11. **What is real in the demo?**  The MCP protocol exchange, tool discovery, gateway call, elicitation error, local review flow, completion notification, and SQLite replay store are executable on isolated branches. Money and identities are fictional.

12. **What stops prompt injection?**  The intended defense is architectural: tool output cannot mint policy proof. The merchant-injection experiment is still pending, so we do not yet claim an experimental containment result.

13. **What happens when the contact is unavailable?**  The action remains paused or expires. Our seeded simulation deliberately reports the resulting loss in legitimate completion instead of hiding it.

14. **How do you know the result is not cherry-picked?**  Generated figures come from committed JSON with fixed assumptions and seed, and the claims checker binds README parameters to that JSON. It is still an author simulation, not independent validation.

15. **What would production require next?**  Real identity enrollment, secure contact recovery, audited payment integrations, deployment hardening, privacy review, independent user research, and support validation in the target assistant client.

