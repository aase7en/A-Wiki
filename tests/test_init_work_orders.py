from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "init-work-orders.sh"
POINTER = "prompt-placement-protocol.md"


def test_bootstrap_adds_prompt_placement_pointer_once(tmp_path: Path) -> None:
    for name in ("AGENTS.md", "CLAUDE.md", "GEMINI.md"):
        (tmp_path / name).write_text(f"# {name}\n", encoding="utf-8")

    first = subprocess.run(
        ["bash", str(SCRIPT), str(tmp_path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    second = subprocess.run(
        ["bash", str(SCRIPT), str(tmp_path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    assert (tmp_path / "COLLAB.md").is_file()
    assert (tmp_path / "docs/work-orders/README.md").is_file()
    assert (tmp_path / "docs/work-orders/WO-TEMPLATE.md").is_file()
    assert "prompt-placement pointer in AGENTS.md" in first.stdout
    assert "already bootstrapped" in second.stdout

    for name in ("AGENTS.md", "CLAUDE.md", "GEMINI.md"):
        text = (tmp_path / name).read_text(encoding="utf-8")
        assert text.count(POINTER) == 1
