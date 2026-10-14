# PR #20 conflict plan — 2026-10-13 UTC

## Authorization update — 2026-10-13

The owner explicitly approved the local-only merge described below. The three
document conflicts were resolved using the proposed preservation approach;
verification and the resulting merge are recorded in BUILD_LOG and HANDOFF.
The earlier "not applied" wording below records the plan before authorization.
No push, GitHub PR merge, or main update is authorized or performed.


Read-only analysis of local repair commit `5f4cfe2` against remote main
`1d1069169e4fd10b5ac887bdcdc827b77b195b92`. No merge has been started.

## Evidence

Fetched main into this isolated clone's FETCH_HEAD without changing any branch.
The first network attempt failed with `getaddrinfo() thread failed to start`;
approved host execution succeeded on the second attempt.

`git merge-tree --write-tree HEAD FETCH_HEAD` computes an uncommitted trial tree
without changing HEAD, the index, or working files. Its conflict diagnostics:

```text
CONFLICT (content): Merge conflict in docs/REUSE_PLAN.md
CONFLICT (add/add): Merge conflict in docs/amazon/BUILD_LOG.md
CONFLICT (add/add): Merge conflict in docs/amazon/HANDOFF.md
```

All changes unique to remote main since the common ancestor are documents.
There are no core-code or frozen-evaluation conflicts. This does not certify
the combined documentation as accurate; several incoming status statements
describe an older stage of the project.

## Proposed minimal resolution (not applied)

| File | Resolution |
|---|---|
| docs/REUSE_PLAN.md | Keep the current repository-relative virtual-environment example and portable short-directory guidance. Both sides describe the same installation; neither needs a machine-specific path. |
| docs/amazon/BUILD_LOG.md | Keep current results at the top. Preserve incoming BUILD-001 through BUILD-011 as dated historical observations, with their source commit; do not overwrite newer measured results. |
| docs/amazon/HANDOFF.md | Keep the current handoff as authoritative. Preserve the incoming handoff under an explicitly historical section or linked archive; distinguish former scan blocks and unimplemented-feature statuses from the owner's later decisions and measured results. Do not silently discard unresolved security limitations. |

Review the automatically merged documents too: DEVPOST, DEMO_SCRIPT,
QA_BANK, RELATED_WORK, the v2 proposal, and submission drafts. Importing a
proposal document is not approval or implementation of v2. Do not convert
historical test counts into current pass claims.

## Authorization boundary

Earlier instructions restrict merges to specifically authorized release
branches. Eliminating this PR conflict by merging current main into the local
repair branch is outside that enumerated permission. This document is a plan,
not a merge approval. Required owner decision:

> Allow a local-only, no-fast-forward merge of main at the inspected commit into
> amazon/ci-repair, resolve only the three documentation conflicts above, run
> full regression, and stop before any push or PR merge.

If approved, first verify main and the PR head have not moved. No branch deletion,
force push, history rewrite, core-security edit, or frozen-data edit is needed.
Stop if additional conflicts or logical changes are required. The subsequent
publication method remains a separate decision; this plan does not authorize it.
