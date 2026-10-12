# Final integration recommendation

No merge or push described here has been executed.

## Recommended order

Starting from the unchanged `main` commit `f18eda5`, create a review branch and
merge, in order, `release/amazon-rc2`, `amazon/merchant-injection`,
`amazon/approvalbench-lite`, and `amazon/final-gate`. Each later branch contains
the earlier branch, so review each merge for only its new commits. Do not publish
until the local verification, merchant gate, and redacted history scan all pass
on the exact final commit.

## Rollback

Before each merge, record the review branch SHA. If a merge gate fails, use
`git revert -m 1 <merge-sha>` to create an auditable rollback commit. Do not use
`reset --hard`, rewrite history, or alter the frozen evaluation directories.

## Known pending evidence

- Real-client error mapping and the complete merchant approval chain require the
  unrestricted owner-side run.
- GitHub Actions is configuration only until the private repository is pushed;
  no remote CI pass is claimed.
- ApprovalBench Lite is an author-scripted simulation, not human-subject research.
