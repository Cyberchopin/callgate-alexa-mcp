"""Validate the public PayPal hackathon submission pack without network access.

During preparation, the Devpost copy intentionally contains one YouTube URL
placeholder. Pass --allow-video-placeholder until the owner uploads the final
public video. The final pre-submit run must omit that flag.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAYPAL_DOCS = ROOT / "docs" / "paypal"
REQUIRED = (
    ROOT / "README.md",
    PAYPAL_DOCS / "SUBMISSION_PACK_ZH.md",
    PAYPAL_DOCS / "DEMO_SCRIPT.md",
    PAYPAL_DOCS / "DEVPOST.md",
    PAYPAL_DOCS / "YOUTUBE_COPY_EN.md",
    PAYPAL_DOCS / "FINAL_SUBMISSION_CHECKLIST_ZH.md",
    PAYPAL_DOCS / "sandbox-run.json",
    PAYPAL_DOCS / "media" / "thumbnail.png",
)
VIDEO_PLACEHOLDER = "[[YouTube link — public, under 3 minutes]]"
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
SPOKEN_LINE = re.compile(r"\*\*“([^”]+)”\*\*")
WORD = re.compile(r"[A-Za-z0-9]+(?:[’'-][A-Za-z0-9]+)*")


def markdown_files() -> list[Path]:
    return [ROOT / "README.md", *sorted(PAYPAL_DOCS.glob("*.md"))]


def local_link_errors(files: list[Path]) -> list[str]:
    errors: list[str] = []
    for source in files:
        text = source.read_text(encoding="utf-8")
        for raw in MARKDOWN_LINK.findall(text):
            target = raw.strip().split()[0].strip("<>")
            if target.startswith(("http://", "https://", "#", "mailto:")):
                continue
            relative = target.split("#", 1)[0]
            if relative and not (source.parent / relative).resolve().exists():
                errors.append(f"{source.relative_to(ROOT)} -> {target}")
    return errors


def find_keys(value: object) -> set[str]:
    if isinstance(value, dict):
        out = set(value)
        for child in value.values():
            out.update(find_keys(child))
        return out
    if isinstance(value, list):
        out: set[str] = set()
        for child in value:
            out.update(find_keys(child))
        return out
    return set()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--allow-video-placeholder", action="store_true")
    args = parser.parse_args()
    errors: list[str] = []

    for path in REQUIRED:
        if not path.is_file():
            errors.append(f"missing required file: {path.relative_to(ROOT)}")

    files = [path for path in markdown_files() if path.is_file()]
    errors.extend(f"missing local Markdown link: {item}" for item in local_link_errors(files))

    devpost_path = PAYPAL_DOCS / "DEVPOST.md"
    if devpost_path.is_file():
        devpost = devpost_path.read_text(encoding="utf-8")
        placeholder_count = devpost.count(VIDEO_PLACEHOLDER)
        other_placeholder_count = devpost.count("[[") - placeholder_count
        if other_placeholder_count:
            errors.append(f"Devpost copy contains {other_placeholder_count} unexpected placeholder(s)")
        if placeholder_count:
            if placeholder_count != 1:
                errors.append(f"Devpost copy contains {placeholder_count} video placeholders; expected one")
            elif not args.allow_video_placeholder:
                errors.append("replace the YouTube placeholder before the final submission")
        elif "youtube.com/" not in devpost and "youtu.be/" not in devpost:
            errors.append("Devpost copy has neither the expected placeholder nor a YouTube URL")

    combined = "\n".join(path.read_text(encoding="utf-8") for path in files)
    for stale in ("claude-sonnet-5-5", "396 across the repository", "92 passed"):
        if stale in combined:
            errors.append(f"stale submission claim found: {stale}")

    sandbox_path = PAYPAL_DOCS / "sandbox-run.json"
    if sandbox_path.is_file():
        sandbox = json.loads(sandbox_path.read_text(encoding="utf-8"))
        keys = find_keys(sandbox)
        forbidden = keys & {"name", "email", "address_line_1", "address_line_2", "postal_code", "city"}
        if forbidden:
            errors.append("sandbox evidence contains private address fields: " + ", ".join(sorted(forbidden)))
        if sandbox.get("base_url") != "https://api-m.sandbox.paypal.com":
            errors.append("sandbox evidence base_url is not the PayPal sandbox")

    script_path = PAYPAL_DOCS / "DEMO_SCRIPT.md"
    spoken_words = 0
    if script_path.is_file():
        script = script_path.read_text(encoding="utf-8")
        spoken_words = len(WORD.findall(" ".join(SPOKEN_LINE.findall(script))))
        if not 250 <= spoken_words <= 390:
            errors.append(f"spoken script has {spoken_words} words; expected 250-390 for an under-3-minute demo")

    print(f"required_files={len(REQUIRED)}")
    print(f"markdown_files={len(files)}")
    print(f"spoken_words={spoken_words}")
    print(f"video_placeholder_allowed={args.allow_video_placeholder}")
    if errors:
        print(f"submission_pack=FAIL ({len(errors)} issue(s))")
        for error in errors:
            print(f"- {error}")
        return 1
    print("submission_pack=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
