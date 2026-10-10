"""Generate a Git-derived pre-existing-work boundary report."""

import argparse
import datetime
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CUTOFF = "2026-08-31T10:15:00-07:00"


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, check=True, text=True,
                          capture_output=True).stdout.strip()


def default_output(cutoff):
    name = "PREEXISTING_WORK_LA_HACKS.md" if cutoff.startswith("2026-10-17") \
        else "PREEXISTING_WORK.md"
    return ROOT / "docs" / "amazon" / name


def generate(cutoff, output):
    head = git("rev-parse", "HEAD")
    pre_head = git("rev-list", "-1", f"--before={cutoff}", "--all")
    warning = []
    if git("rev-parse", "--is-shallow-repository") == "true":
        warning.append("WARNING: shallow history; boundary report may be incomplete.")
    if git("replace", "-l"):
        warning.append("WARNING: git replace refs detected; history may be rewritten locally.")
    modules = {}
    if pre_head:
        for path in git("ls-tree", "-r", "--name-only", pre_head).splitlines():
            module = path.split("/", 1)[0]
            if module not in modules:
                first = git("log", "--all", "--reverse", "--format=%H", "--", module)
                modules[module] = first.splitlines()[0] if first else "UNKNOWN"
    changed = {}
    current_commit = None
    log = git("log", "--all", f"--since={cutoff}", "--reverse",
              "--format=commit:%H", "--name-only")
    for line in log.splitlines():
        if line.startswith("commit:"):
            current_commit = line.removeprefix("commit:")
        elif line and current_commit and line not in changed:
            changed[line] = current_commit
    generated = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    lines = ["# Pre-existing work boundary", "", f"- Cutoff: `{cutoff}`",
             f"- Source HEAD: `{head}`", f"- Generated: `{generated}`", ""]
    lines.extend(f"> {item}" for item in warning)
    if warning:
        lines.append("")
    lines.extend(["## Present before cutoff", "",
                  "| Module/path | First commit |", "|---|---|"])
    lines.extend(f"| `{path}` | `{sha}` |" for path, sha in sorted(modules.items()))
    lines.extend(["", "## Added or modified after cutoff", "",
                  "| File | First post-cutoff commit |", "|---|---|"])
    lines.extend(f"| `{path}` | `{sha}` |" for path, sha in sorted(changed.items()))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--cutoff", default=DEFAULT_CUTOFF)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    generate(args.cutoff, args.output or default_output(args.cutoff))
