from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "todo-health.py"
spec = importlib.util.spec_from_file_location("todo_health", SCRIPT)
assert spec and spec.loader
todo_health = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = todo_health
spec.loader.exec_module(todo_health)


def test_extract_active_block_stops_at_next_heading():
    text = """# Session Memory

## 🔥 Active TODOs (cross-session)

- [ ] **[wiki-brain]** Keep this

## Recent

- [ ] **[old]** Ignore this
"""

    block = todo_health.extract_active_block(text)

    assert "- [ ] **[wiki-brain]** Keep this" in block
    assert all("[old]" not in line for line in block)


def test_analyze_fails_when_active_todo_cap_is_exceeded(tmp_path):
    session = tmp_path / "session-memory.md"
    backlog = tmp_path / "project-backlog.md"
    backlog.write_text("# Backlog\n", encoding="utf-8")
    session.write_text(
        "## 🔥 Active TODOs (cross-session)\n\n"
        "- [ ] **[a]** one\n"
        "- [ ] **[b]** two\n"
        "- [ ] **[c]** three\n"
        "\n## Sticky\n",
        encoding="utf-8",
    )

    findings, summary = todo_health.analyze(session, backlog, max_active=2)

    assert summary["active_open"] == 3
    assert any(f.level == "FAIL" and "exceeds cap" in f.message for f in findings)


def test_analyze_warns_on_checked_items_in_active_block(tmp_path):
    session = tmp_path / "session-memory.md"
    backlog = tmp_path / "project-backlog.md"
    backlog.write_text("# Backlog\n", encoding="utf-8")
    session.write_text(
        "## 🔥 Active TODOs (cross-session)\n\n"
        "- [x] **[done]** should roll off\n"
        "- [ ] **[open]** should stay\n"
        "\n## Sticky\n",
        encoding="utf-8",
    )

    findings, summary = todo_health.analyze(session, backlog)

    assert summary["active_checked"] == 1
    assert any(f.level == "WARN" and "checked" in f.message for f in findings)
