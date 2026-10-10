import importlib.util
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_generator():
    spec = importlib.util.spec_from_file_location(
        "gen_preexisting", ROOT / "scripts" / "gen_preexisting.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_friction_add_writes_required_fields(tmp_path):
    log = tmp_path / "friction.md"
    result = subprocess.run([sys.executable, "scripts/friction.py", "add",
        "--task", "T", "--step", "S", "--expected", "E", "--actual", "RAW",
        "--severity", "low", "--workaround", "W", "--suggestion", "A",
        "--log", str(log)], cwd=ROOT)
    assert result.returncode == 0
    text = log.read_text(encoding="utf-8")
    assert all(value in text for value in ("T", "S", "E", "RAW", "low", "W", "A"))


def test_preexisting_generators_keep_outputs_separate(tmp_path):
    amazon = tmp_path / "amazon.md"
    la = tmp_path / "la.md"
    for cutoff, output in (("2026-08-31T10:15:00-07:00", amazon),
                           ("2026-10-17", la)):
        result = subprocess.run([sys.executable, "scripts/gen_preexisting.py",
            "--cutoff", cutoff, "--output", str(output)], cwd=ROOT)
        assert result.returncode == 0
    assert "2026-08-31" in amazon.read_text(encoding="utf-8")
    assert "2026-10-17" in la.read_text(encoding="utf-8")


def test_preexisting_boundary_uses_author_not_committer_date(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.invalid"],
                   cwd=repo, check=True)
    (repo / "before.txt").write_text("before", encoding="utf-8")
    subprocess.run(["git", "add", "before.txt"], cwd=repo, check=True)
    env = os.environ | {
        "GIT_AUTHOR_DATE": "2026-08-30T12:00:00-07:00",
        "GIT_COMMITTER_DATE": "2026-09-02T12:00:00-07:00",
    }
    subprocess.run(["git", "commit", "-qm", "authored before cutoff"], cwd=repo,
                   env=env, check=True)

    output = tmp_path / "report.md"
    load_generator().generate("2026-08-31T10:15:00-07:00", output, root=repo)
    report = output.read_text(encoding="utf-8")
    assert "Date basis: Git author date" in report
    assert "`before.txt`" in report
    assert "## Added or modified after cutoff\n\n| File | First post-cutoff commit |\n|---|---|\n" in report
