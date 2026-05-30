from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DIGEST_SCRIPT = REPO_ROOT / "scripts" / "wiki-health-digest.py"

spec = importlib.util.spec_from_file_location("wiki_health_digest", DIGEST_SCRIPT)
assert spec and spec.loader
wiki_health_digest = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = wiki_health_digest
spec.loader.exec_module(wiki_health_digest)


def test_version_has_matching_changelog_entry():
    version = (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    changelog = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

    assert version
    assert f"## {version}" in changelog
    assert "P4" in changelog
    assert "P5" in changelog


def test_upstream_refresh_runbook_names_refresh_commands():
    text = (REPO_ROOT / "docs" / "runbooks" / "upstream-refresh.md").read_text(encoding="utf-8")

    assert "scripts/refresh-ecosystem.sh" in text
    assert "scripts/refresh-9arm.sh" in text
    assert "scripts/refresh-skillopt.sh" in text
    assert "scripts/update-model-roster.sh" in text
    assert "VERSION" in text
    assert "CHANGELOG.md" in text


def test_wiki_health_digest_renders_markdown_summary():
    payload = {
        "generated_at": "2026-05-30T00:00:00Z",
        "version": "1.2.0",
        "summary": {"ok": 1, "warn": 0, "fail": 0},
        "stats": {"wiki_markdown": 10},
        "checks": [{"level": "OK", "name": "version tracking", "detail": "1.2.0"}],
    }

    markdown = wiki_health_digest.render_markdown(payload)

    assert "# A-Wiki Weekly Health Digest" in markdown
    assert "| `wiki_markdown` | 10 |" in markdown
    assert "must not auto-commit" in markdown


def test_wiki_health_digest_workflow_is_report_only():
    workflow = REPO_ROOT / ".github" / "workflows" / "wiki-health-digest.yml"
    text = workflow.read_text(encoding="utf-8")

    assert "schedule:" in text
    assert "scripts/wiki-health-digest.py" in text
    assert "actions/upload-artifact@v4" in text
    assert "setup-cloud-link.sh --provider local --force" in text
    assert "git commit" not in text
    assert "git push" not in text
