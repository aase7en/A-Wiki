from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_stop_auto_commit_refuses_non_main_without_merge():
    for rel in (".claude/hooks/stop-auto-commit.sh", ".codex/hooks/stop-auto-commit.sh"):
        text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        assert "refusing auto-commit/push" in text
        assert 'git merge "$BRANCH"' not in text
        assert "git checkout main" not in text
