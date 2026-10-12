# RC1 CI handoff

The workflow in `.github/workflows/amazon-rc1.yml` is prepared but has not run because no branch was pushed.

It runs the full Python and Node suites plus both dependency audits on Python 3.12 for Ubuntu and Windows. A separate Ubuntu job scans all reachable Git history with Gitleaks 8.30.1 and `--redact`; it must fail without printing secret values if a finding remains. Dependabot remains enabled for the root Python manifest, the MCP manifest, and GitHub Actions.

## After pushing RC1 to the private repository

1. Open the private repository on GitHub.
2. Select **Actions**.
3. Open **Amazon RC1 verification**.
4. Open the run for the pushed RC1 commit.
5. Confirm both matrix rows are present: **Python and Node (ubuntu-latest)** and **Python and Node (windows-latest)**.
6. Open each row and record the Python, Node, root audit, and MCP audit results.
7. Open **Full-history secret scan (redacted)**. If it fails, do not publish the repository; classify the finding locally without copying the matched value into an issue, log, or chat.

The workflow is evidence only after GitHub has actually run it. Its presence in the repository is not a passing result.

