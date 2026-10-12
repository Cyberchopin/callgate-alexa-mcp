"""Fail-closed local submission readiness checklist."""

import argparse
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
    tests = command([sys.executable, "-m", "pytest", "-q"])
    checks.append(("Python tests pass", tests.returncode == 0))
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
