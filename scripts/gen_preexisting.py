"""Generate a Git-derived pre-existing-work boundary report."""

import argparse
import datetime
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CUTOFF = "2026-08-31T10:15:00-07:00"


def git(*args, root=ROOT):
    return subprocess.run(["git", *args], cwd=root, check=True, text=True,
                          capture_output=True).stdout.strip()


def parse_cutoff(value):
    cutoff = datetime.datetime.fromisoformat(value)
    pacific_daylight_time = datetime.timezone(datetime.timedelta(hours=-7))
    return cutoff.replace(tzinfo=cutoff.tzinfo or pacific_daylight_time)


def author_dated_commits(root):
    rows = git("log", "--all", "--format=%H%x09%aI", root=root).splitlines()
    return [(sha, datetime.datetime.fromisoformat(authored))
            for sha, authored in (row.split("\t", 1) for row in rows)]


def default_output(cutoff):
    name = "PREEXISTING_WORK_LA_HACKS.md" if cutoff.startswith("2026-10-17") \
        else "PREEXISTING_WORK.md"
    return ROOT / "docs" / "amazon" / name


def generate(cutoff, output, root=ROOT):
    cutoff_time = parse_cutoff(cutoff)
    commits = author_dated_commits(root)
    head = git("rev-parse", "HEAD", root=root)
    eligible = [(sha, authored) for sha, authored in commits if authored < cutoff_time]
    pre_head = max(eligible, key=lambda item: item[1])[0] if eligible else ""
    warning = []
    if git("rev-parse", "--is-shallow-repository", root=root) == "true":
        warning.append("WARNING: shallow history; boundary report may be incomplete.")
    if git("replace", "-l", root=root):
        warning.append("WARNING: git replace refs detected; history may be rewritten locally.")
    modules = {}
    if pre_head:
        for path in git("ls-tree", "-r", "--name-only", pre_head, root=root).splitlines():
            module = path.split("/", 1)[0]
            if module not in modules:
                first = git("log", "--all", "--reverse", "--format=%H", "--", module,
                            root=root)
                modules[module] = first.splitlines()[0] if first else "UNKNOWN"
    changed = {}
    for sha, authored in sorted(commits, key=lambda item: item[1]):
        if authored < cutoff_time:
            continue
        paths = git("diff-tree", "--root", "--no-commit-id", "--name-only", "-r", sha,
                    root=root)
        for path in paths.splitlines():
            changed.setdefault(path, sha)
    generated = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    lines = ["# Pre-existing work boundary", "", f"- Cutoff: `{cutoff}`",
             "- Date basis: Git author date (`%aI`)",
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
