from __future__ import annotations

import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "link-my-skills.sh"


def test_link_my_skills_skips_existing_real_directory(tmp_path):
    codex_skills = tmp_path / ".codex" / "skills"
    existing_pdf = codex_skills / "pdf"
    existing_pdf.mkdir(parents=True)
    marker = existing_pdf / "KEEP"
    marker.write_text("do not delete", encoding="utf-8")

    result = subprocess.run(
        ["bash", str(SCRIPT), "--codex"],
        cwd=REPO_ROOT,
        env={"HOME": str(tmp_path), "PATH": "/usr/bin:/bin:/usr/sbin:/sbin"},
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr + result.stdout
    assert marker.read_text(encoding="utf-8") == "do not delete"
    assert "Skipping existing directory" in result.stdout
    assert (codex_skills / "model-cost-switching").is_symlink()
