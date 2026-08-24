"""Tests for scripts/health/wiki_health.py — truthful wiki health (P2.2).

Iron Law #1: failing tests written FIRST.

Replaces fail-open health behavior (retired daily-maintenance's
`--check 2>/dev/null || echo OK`) with real validation. Contract:
  HARD errors (exit 1): broken wikilinks, invalid frontmatter,
                        stale generated context, skill-surface drift
  ADVISORIES (exit 0): orphan pages, duplicate aliases, dangling graph edges
  Integration-registry check: reported as skipped until the registry
  exists (Phase 3).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "health"))

import wiki_health as wh  # noqa: E402 -- module under test


def _write(p: Path, text: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


# ---------------------------------------------------------------------------
# wikilinks
# ---------------------------------------------------------------------------
def test_broken_wikilink_is_hard_error(tmp_path):
    wiki = tmp_path / "wiki"
    _write(wiki / "concepts" / "a.md", "See [[missing-target]] for details.\n")
    result = wh.check_wikilinks(wiki)
    assert result.severity == "hard"
    assert any("missing-target" in e for e in result.errors)


def test_valid_wikilink_and_alias_form_pass(tmp_path):
    wiki = tmp_path / "wiki"
    _write(wiki / "concepts" / "target.md", "# Target\n")
    _write(wiki / "concepts" / "a.md", "See [[target]] and [[target|display]].\n")
    result = wh.check_wikilinks(wiki)
    assert result.severity == "ok", result.errors


def test_wikilink_resolves_across_subdirs(tmp_path):
    wiki = tmp_path / "wiki"
    _write(wiki / "entities" / "iot" / "deep-entity.md", "# X\n")
    _write(wiki / "concepts" / "a.md", "See [[deep-entity]].\n")
    assert wh.check_wikilinks(wiki).severity == "ok"


# ---------------------------------------------------------------------------
# frontmatter
# ---------------------------------------------------------------------------
def test_unparseable_frontmatter_is_hard_error(tmp_path):
    wiki = tmp_path / "wiki"
    _write(wiki / "sources" / "bad.md", "---\ntitle: [unclosed\n---\nbody\n")
    result = wh.check_frontmatter(wiki)
    assert result.severity == "hard"
    assert any("bad.md" in e for e in result.errors)


def test_duplicate_aliases_are_advisory(tmp_path):
    wiki = tmp_path / "wiki"
    _write(wiki / "a.md", "---\naliases: [x1, dup]\n---\n")
    _write(wiki / "b.md", "---\naliases:\n  - dup\n---\n")
    result = wh.check_duplicate_aliases(wiki)
    assert result.severity == "advisory"
    assert any("dup" in a for a in result.advisories)


# ---------------------------------------------------------------------------
# graph + orphans
# ---------------------------------------------------------------------------
def test_dangling_graph_edges_are_advisory(tmp_path):
    wiki = tmp_path / "wiki"
    _write(wiki / "concepts" / "live.md", "# live\n")
    graph = tmp_path / ".wiki-graph.json"  # real schema: path/from/to/broken
    graph.write_text(json.dumps({
        "nodes": [
            {"path": "wiki/concepts/live.md"},
            {"path": "wiki/concepts/gone.md"},  # ghost node — no file on disk
        ],
        "edges": [{"from": "wiki/concepts/live.md", "to": "wiki/concepts/gone.md",
                   "type": "wikilink", "broken": False}],
    }), encoding="utf-8")
    result = wh.check_graph_edges(wiki, graph)
    assert result.severity == "advisory"
    assert any("gone" in a for a in result.advisories)


def test_orphan_pages_are_advisory(tmp_path):
    wiki = tmp_path / "wiki"
    _write(wiki / "concepts" / "linked.md", "# A\n")
    _write(wiki / "concepts" / "b.md", "See [[linked]].\n")
    _write(wiki / "concepts" / "lonely.md", "# no inbound links\n")
    result = wh.check_orphans(wiki)
    assert result.severity == "advisory"
    assert any("lonely" in a for a in result.advisories)
    assert not any("linked" in a for a in result.advisories)


# ---------------------------------------------------------------------------
# aggregate + report
# ---------------------------------------------------------------------------
def test_hard_errors_fail_advisories_pass(tmp_path):
    wiki = tmp_path / "wiki"
    _write(wiki / "concepts" / "a.md", "See [[nowhere]].\n")
    _write(wiki / "concepts" / "lonely.md", "# orphan\n")
    report = wh.run_all(tmp_path, slow_checks=False)
    assert report.hard_errors, "broken wikilink must be a hard error"
    assert report.advisories, "orphan must be an advisory"
    assert report.exit_code() == 1


def test_clean_tiny_wiki_passes(tmp_path):
    wiki = tmp_path / "wiki"
    _write(wiki / "concepts" / "a.md", "---\naliases: [aa]\n---\nSelf link [[a]].\n")
    report = wh.run_all(tmp_path, slow_checks=False)
    assert report.exit_code() == 0, report.hard_errors


def test_report_json_written(tmp_path):
    wiki = tmp_path / "wiki"
    _write(wiki / "concepts" / "a.md", "See [[nowhere]].\n")
    out = tmp_path / "report.json"
    report = wh.run_all(tmp_path, slow_checks=False, json_path=out)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["hard_errors"]
    assert report.exit_code() == 1


def test_integration_check_reports_skipped_until_registry_exists(tmp_path):
    _write(tmp_path / "wiki" / "concepts" / "a.md", "x\n")
    report = wh.run_all(tmp_path, slow_checks=False)
    assert any("integration registry" in a.lower() for a in report.skipped)


def test_baseline_ratchet_suppresses_known_debt_but_not_new(tmp_path):
    wiki = tmp_path / "wiki"
    _write(wiki / "concepts" / "a.md", "See [[legacy-missing]].\n")
    report = wh.run_all(tmp_path, slow_checks=False)
    assert report.exit_code() == 1
    assert len(report.hard_errors) == 1

    baseline = tmp_path / "baseline.txt"
    baseline.write_text(
        wh._hard_key(report.hard_errors[0]) + "\n", encoding="utf-8"
    )
    ratcheted = wh.run_all(tmp_path, slow_checks=False, baseline_path=baseline)
    assert ratcheted.exit_code() == 0, "baselined debt must not fail"
    assert len(ratcheted.baselined_hard) == 1
    assert ratcheted.hard_errors == []


# ---------------------------------------------------------------------------
# R-P2-004 — baseline identities must be platform-independent
# ---------------------------------------------------------------------------
def test_hard_keys_never_contain_backslashes(tmp_path):
    """Windows renders relative_to() with backslashes; baseline keys must not."""
    _write(tmp_path / "wiki" / "concepts" / "a.md", "See [[nowhere]].\n")
    report = wh.run_all(tmp_path, slow_checks=False)
    assert report.hard_errors
    for e in report.hard_errors + report.baselined_hard + report.advisories:
        assert "\\" not in e, f"platform-native separator leaked into identity: {e}"


def test_hard_key_normalizes_separator_variants():
    """Equivalent Windows/Linux renderings collapse to ONE baseline key."""
    bs = chr(92)  # backslash, built via chr() so no escape-sequence ambiguity
    win = "[wikilinks] concepts" + bs + "ai-tools" + bs + "tradeoffs.md: broken wikilink [[X]]"
    lin = "[wikilinks] concepts/ai-tools/tradeoffs.md: broken wikilink [[X]]"
    assert wh._hard_key(win) == wh._hard_key(lin)


def test_frontmatter_skip_is_visible_without_pyyaml(monkeypatch, tmp_path):
    """R-P2-005: missing PyYAML must be REPORTED, never silently green."""
    import importlib
    import sys

    _write(tmp_path / "wiki" / "concepts" / "a.md", "no frontmatter\n")
    monkeypatch.setitem(sys.modules, "yaml", None)
    importlib.reload(wh)
    try:
        report = wh.run_all(tmp_path, slow_checks=False)
        assert any("PyYAML" in s for s in report.skipped), report.skipped
    finally:
        importlib.reload(wh)  # restore real yaml state


class TestWikilinkResolutionExtensions:
    """2026-08-24: skills and repo files are real link targets."""

    def _idx(self):
        import importlib.util as ilu, sys as _sys
        spec = ilu.spec_from_file_location(
            "wh_real", REPO_ROOT / "scripts" / "health" / "wiki_health.py")
        wh = ilu.module_from_spec(spec)
        _sys.modules["wh_real"] = wh  # dataclasses need a registered module
        spec.loader.exec_module(wh)
        # the REAL repo: skill/registry resolution is repo-wide by design
        return wh, REPO_ROOT / "wiki"

    def test_skill_names_resolve(self, tmp_path):
        wh, wiki = self._idx()
        index, paths = wh._resolution_indexes(wiki)
        assert "monte-carlo-quant-analysis" in index, "skill name must resolve"
        assert "a-router" in index and "theme-factory" in index

    def test_repo_md_file_with_extension_resolves(self, tmp_path):
        wh, wiki = self._idx()
        index, paths = wh._resolution_indexes(wiki)
        assert wh._resolves("CLAUDE.md", index, paths), "root CLAUDE.md must resolve"
        assert wh._resolves("profile.md", index, paths)
