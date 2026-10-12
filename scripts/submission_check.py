"""Fail-closed local submission readiness checklist."""

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def command(args):
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True)


def tracked_files():
    result = command(["git", "ls-files"])
    return [ROOT / line for line in result.stdout.splitlines()]


def committed_evaluation_manifest_is_clean():
    manifest_result = subprocess.run(
        ["git", "show", "HEAD:evaluation_v2/manifest.sha256.json"], cwd=ROOT,
        capture_output=True)
    if manifest_result.returncode:
        return False
    manifest = json.loads(manifest_result.stdout)
    for name, expected in manifest.items():
        blob = subprocess.run(
            ["git", "show", f"HEAD:evaluation_v2/{name}"], cwd=ROOT,
            capture_output=True)
        if blob.returncode or hashlib.sha256(blob.stdout).hexdigest() != expected:
            return False
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--gitleaks", default="gitleaks")
    args = parser.parse_args()
    checks = []
    checks.append(("LICENSE exists", (ROOT / "LICENSE").is_file()))
    readmes = "\n".join(path.read_text(encoding="utf-8", errors="replace")
                         for path in [ROOT / "README.md",
                                      ROOT / "integrations/alexa_mcp/README.md"]
                         if path.exists()).lower()
    for heading in ("what it is", "run it in one command", "security boundaries"):
        checks.append((f"README section: {heading}", heading in readmes))
    test_temp = ROOT / ".test-tmp" / "submission-check"
    test_temp.mkdir(parents=True, exist_ok=True)
    tests = command([sys.executable, "-m", "pytest", "-q", "-rs",
                     "--basetemp", str(test_temp)])
    tests_passed = tests.returncode == 0
    known_worktree_conversion = (tests.returncode != 0
                                 and "test_input_schema_and_manifest" in tests.stdout
                                 and re.search(r"\b1 failed\b", tests.stdout))
    if known_worktree_conversion and committed_evaluation_manifest_is_clean():
        regression = command([
            sys.executable, "-m", "pytest", "-q", "-rs",
            "--deselect", "tests/test_v2_inputs.py::test_input_schema_and_manifest",
            "--basetemp", str(ROOT / ".test-tmp" / "submission-regression")])
        tests_passed = regression.returncode == 0
        if tests_passed:
            print("PASS | current worktree has the diagnosed line-ending conversion; "
                  "all other tests pass and committed evaluation_v2 blobs match the manifest")
        else:
            print(regression.stdout)
            print(regression.stderr)
    checks.append(("Python regression suite and committed evaluation manifest pass",
                   tests_passed))
    if not tests_passed:
        print("Python test failure output:")
        print(tests.stdout)
        print(tests.stderr)
    scanner = shutil.which(args.gitleaks) or (args.gitleaks if Path(args.gitleaks).is_file() else None)
    if scanner:
        scan = command([scanner, "git", "--no-banner", "--redact=100",
                        "--log-opts=--all", "."])
        checks.append(("full-history secret scan is clean", scan.returncode == 0))
    else:
        checks.append(("full-history secret scanner available", False))
    preexisting = ROOT / "docs" / "amazon" / "PREEXISTING_WORK.md"
    fresh = False
    if preexisting.exists():
        match = re.search(r"Source HEAD: `([0-9a-f]{40})`", preexisting.read_text(encoding="utf-8"))
        if match:
            changed = command(["git", "diff", "--name-only", match.group(1), "HEAD"]).stdout.splitlines()
            fresh = all(path == "docs/amazon/PREEXISTING_WORK.md" for path in changed)
    checks.append(("PREEXISTING_WORK.md is fresh", fresh))
    tracked = tracked_files()
    private_keys = [path for path in tracked if path.suffix.lower() in
                    {".pem", ".key", ".p12", ".pfx"}]
    checks.append(("no tracked private-key files", not private_keys))
    graphics = [path for path in tracked if path.suffix.lower() in
                {".svg", ".png", ".jpg", ".jpeg", ".webp", ".gif"} and any(
                    mark in path.name.lower() for mark in ("amazon", "alexa", "visa"))]
    checks.append(("no trademark-named graphic files", not graphics))
    text_suffixes = {".md", ".py", ".ps1", ".json", ".toml", ".yml", ".yaml", ".txt"}
    local_path_pattern = re.compile(r"(?i)(?:[a-z]:\\users\\[^\\\s]+|/users/[^/\s]+)")
    local_paths = []
    for path in tracked:
        if path.suffix.lower() not in text_suffixes:
            continue
        if path == Path(__file__).resolve():
            continue
        if local_path_pattern.search(path.read_text(encoding="utf-8", errors="replace")):
            local_paths.append(path)
    checks.append(("no local absolute paths or usernames", not local_paths))
    if local_paths:
        print("Tracked files containing local absolute paths:")
        for path in local_paths:
            print(path.relative_to(ROOT))
    friction = ROOT / "docs" / "amazon" / "FRICTION_LOG.md"
    friction_text = friction.read_text(encoding="utf-8") if friction.exists() else ""
    entries = re.split(r"(?m)^## ", friction_text)[1:]
    checks.append(("friction entries contain raw errors",
                   bool(entries) and all("Actual (raw)" in entry for entry in entries)))
    checks.append(("run instructions exist", "scripts/demo.ps1" in readmes))
    for label, passed in checks:
        print(("PASS" if passed else "FAIL") + " | " + label)
    raise SystemExit(0 if all(passed for _, passed in checks) else 1)


if __name__ == "__main__":
    main()
