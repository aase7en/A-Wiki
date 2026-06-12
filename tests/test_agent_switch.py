from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=False)


def test_agent_switch_bootstraps_missing_local_handoff(tmp_path: Path):
    repo = tmp_path / "repo"
    (repo / "scripts" / "swarm").mkdir(parents=True)
    (repo / "scripts" / "lib").mkdir(parents=True)
    (repo / "wiki" / "context").mkdir(parents=True)

    shutil.copy2(REPO_ROOT / "scripts" / "swarm" / "agent-switch.sh", repo / "scripts" / "swarm" / "agent-switch.sh")
    shutil.copy2(REPO_ROOT / "scripts" / "lib" / "personal_paths.sh", repo / "scripts" / "lib" / "personal_paths.sh")
    shutil.copy2(REPO_ROOT / "handoff.md.example", repo / "handoff.md.example")
    (repo / "log.md.example").write_text("## [2026-06-05] bootstrap test\n", encoding="utf-8")
    (repo / "wiki" / "context" / "session-memory.md.example").write_text(
        "## \U0001f525 Active TODOs\n\n- [ ] continue test task\n\n## \U0001f5d3\ufe0f Recent\n\n### [2026-06-05] test\n\n- Done: seed\n",
        encoding="utf-8",
    )

    assert run(["git", "init", "-b", "main"], repo).returncode == 0
    assert not (repo / "handoff.md").exists()

    result = run(["bash", "scripts/swarm/agent-switch.sh", "quick"], repo)

    assert result.returncode == 0, result.stderr
    handoff = (repo / "handoff.md").read_text(encoding="utf-8")
    assert "HANDOFF-AUTO-START" in handoff
    assert "continue test task" in handoff
    assert "Cross-Agent Handoff" in handoff


def test_agent_switch_adds_cost_snapshot_and_suggested_skills(tmp_path: Path):
    repo = tmp_path / "repo"
    (repo / "scripts" / "swarm").mkdir(parents=True)
    (repo / "scripts" / "lib").mkdir(parents=True)
    (repo / "scripts").mkdir(exist_ok=True)
    (repo / "wiki" / "context").mkdir(parents=True)
    (repo / ".tmp").mkdir()

    shutil.copy2(REPO_ROOT / "scripts" / "swarm" / "agent-switch.sh", repo / "scripts" / "swarm" / "agent-switch.sh")
    shutil.copy2(REPO_ROOT / "scripts" / "lib" / "personal_paths.sh", repo / "scripts" / "lib" / "personal_paths.sh")
    shutil.copy2(REPO_ROOT / "scripts" / "check-handoff.py", repo / "scripts" / "check-handoff.py")
    shutil.copy2(REPO_ROOT / "handoff.md.example", repo / "handoff.md.example")
    (repo / ".tmp" / "cost-tier-2026-06-13.txt").write_text("L2|handoff|test route", encoding="utf-8")
    (repo / ".tmp" / "model-scout-current.json").write_text("{}", encoding="utf-8")
    (repo / "log.md.example").write_text("## [2026-06-05] bootstrap test\n", encoding="utf-8")
    (repo / "wiki" / "context" / "session-memory.md.example").write_text(
        "## \U0001f525 Active TODOs\n\n- [ ] continue script fix\n\n## \U0001f5d3\ufe0f Recent\n\n### [2026-06-05] test\n\n- Done: seed\n",
        encoding="utf-8",
    )

    assert run(["git", "init", "-b", "main"], repo).returncode == 0

    result = run(["bash", "scripts/swarm/agent-switch.sh", "quick"], repo)

    assert result.returncode == 0, result.stderr
    handoff = (repo / "handoff.md").read_text(encoding="utf-8")
    assert "### Cost Tier Snapshot" in handoff
    assert "L2|handoff|test route" in handoff
    assert "### Suggested Skills" in handoff
    assert "model-cost-switching" in handoff
    assert run(["python3", "scripts/check-handoff.py", "--path", "handoff.md"], repo).returncode == 0
