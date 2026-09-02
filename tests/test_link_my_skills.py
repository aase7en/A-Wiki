from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "link-my-skills.sh"


def _bash_executable() -> str:
    if sys.platform == "win32" or os.name == "nt":
        git_exe = shutil.which("git")
        if git_exe:
            candidate = Path(git_exe).resolve().parent.parent / "bin" / "bash.exe"
            if candidate.is_file():
                return str(candidate)
    return "bash"


def test_link_my_skills_skips_existing_real_directory(tmp_path):
    codex_skills = tmp_path / ".codex" / "skills"
    existing_pdf = codex_skills / "pdf"
    existing_pdf.mkdir(parents=True)
    marker = existing_pdf / "KEEP"
    marker.write_text("do not delete", encoding="utf-8")

    # The bash script emits UTF-8 (✓/emoji status); text=True alone would
    # decode with the locale codec and crash the reader thread on cp874
    # Windows, silently turning stdout into None.
    result = subprocess.run(
        [_bash_executable(), str(SCRIPT), "--codex"],
        cwd=REPO_ROOT,
        env={"HOME": str(tmp_path), "PATH": "/usr/bin:/bin:/usr/sbin:/sbin"},
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    assert result.returncode == 0, result.stderr + result.stdout
    assert marker.read_text(encoding="utf-8") == "do not delete"
    assert "Skipping existing directory" in result.stdout
    assert (codex_skills / "model-cost-switching").is_symlink()
