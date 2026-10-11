# Related work

CallGate does not claim to discover a new vulnerability category. It applies existing research concerns to a consumer shopping and simulated voice-assistant setting, then measures approval designs with an author-written benchmark.

## Lies in the Loop

Checkmarx Zero's Lies-in-the-Loop research studies how compromised context can manipulate human approval: `{{LINK_NEEDED: Checkmarx Zero primary research URL}}`.

The relevant OWASP entry is: `{{LINK_NEEDED: exact OWASP primary entry URL}}`.

CallGate's difference is scope, not priority. The scenario is a household shopper receiving phone pressure while an agent consumes poisoned merchant content. The proposed control is out-of-band review by a different simulated subject, displaying server-held parameters and issuing a scoped, one-use permission. ApprovalBench compares this design with other author-written approval patterns. `{{CLAIMS:APPROVALBENCH_RELATED_WORK_SUMMARY}}`

## MCP URL-mode elicitation

The [MCP 2025-11-25 URL-mode elicitation specification](https://modelcontextprotocol.io/specification/2025-11-25/client/elicitation) defines how a server can direct a user to an external interaction and later notify the client that it completed. CallGate uses that protocol boundary for simulated review. This does not imply support in every MCP client or in any production voice assistant.

## Tool poisoning and indirect prompt injection

Public research has shown that tool metadata and tool-returned content can carry instructions that influence an agent: `{{LINK_NEEDED: primary public tool-poisoning research URL}}`.

CallGate does not try to prove that the agent ignored poisoned content. Its deliberately vulnerable test double is expected to follow it. The measured question is narrower: can poisoned context obtain a protected action when authorization depends on a separate subject, the server's actual parameters, and one-use proof?

## What ApprovalBench measures

ApprovalBench is titled **“simulated, author-scripted, not human-subject research.”** It reports attack-success counts, legitimate completion, and verification delay from generated JSON. The reference implementations are ours, are intended to resemble their real design families rather than caricature them, and are explicitly open to correction. No result should be generalized to a deployed payment system or to human behavior.

