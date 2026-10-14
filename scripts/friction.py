"""Append a contemporaneous competition-tool friction entry."""

import argparse
import datetime
from pathlib import Path


DEFAULT_LOG = Path(__file__).resolve().parents[1] / "docs" / "amazon" / "FRICTION_LOG.md"


def add(args):
    timestamp = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    entry = f"""

## {timestamp} — {args.task}

- Step: {args.step}
- Expected: {args.expected}
- Actual (raw):

```text
{args.actual}
```

- Severity: {args.severity}
- Workaround: {args.workaround}
- Actionable suggestion: {args.suggestion}
"""
    args.log.parent.mkdir(parents=True, exist_ok=True)
    with args.log.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(entry)


def parser():
    root = argparse.ArgumentParser()
    commands = root.add_subparsers(dest="command", required=True)
    command = commands.add_parser("add")
    command.add_argument("--task", required=True)
    command.add_argument("--step", required=True)
    command.add_argument("--expected", required=True)
    command.add_argument("--actual", required=True)
    command.add_argument("--severity", required=True,
                         choices=("low", "medium", "high", "critical"))
    command.add_argument("--workaround", required=True)
    command.add_argument("--suggestion", required=True)
    command.add_argument("--log", type=Path, default=DEFAULT_LOG)
    command.set_defaults(run=add)
    return root


if __name__ == "__main__":
    arguments = parser().parse_args()
    arguments.run(arguments)
