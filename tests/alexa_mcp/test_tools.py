import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


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
