"""
test_check_output_format.py — Tests for the Output Format Guard hook.

Covers:
  (a) BLOCK .html into source-of-truth dirs/files  → exit 2
  (b) BLOCK .html outside allowed zones             → exit 2
  (c) WARN  .md with >=12 rows + report keywords    → exit 0, advisory in stderr
  (d) Allow .html in exports/html/ and templates/   → exit 0
  (e) Various edge cases: MultiEdit, non-write, parse fail
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK_PATH = REPO_ROOT / "scripts" / "hooks" / "check_output_format.py"


def _run(payload: dict) -> subprocess.CompletedProcess:
    """Run the hook with the given payload dict, return CompletedProcess."""
    return subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )


def _write(file_path: str, content: str = "<html>") -> dict:
    return {"tool_name": "Write", "tool_input": {"file_path": file_path, "content": content}}


def _edit(file_path: str, new_string: str = "<html>") -> dict:
    return {"tool_name": "Edit", "tool_input": {"file_path": file_path, "new_string": new_string}}


def _multiedit(file_path: str, edits: list[dict]) -> dict:
    return {"tool_name": "MultiEdit", "tool_input": {"file_path": file_path, "edits": edits}}


# ── (a) BLOCK: .html into source-of-truth ────────────────────────────────

class TestBlockHtmlIntoSourceOfTruth:

    def test_block_html_in_wiki(self):
        r = _run(_write("wiki/entities/iot/test.html"))
        assert r.returncode == 2
        assert "BLOCKED" in r.stderr

    def test_block_html_in_docs(self):
        r = _run(_write("docs/protocols/test.html"))
        assert r.returncode == 2

    def test_block_html_in_raw(self):
        r = _run(_write("raw/test.html"))
        assert r.returncode == 2

    def test_block_html_as_claude_md(self):
        r = _run(_write("CLAUDE.md.html"))
        # file_path contains CLAUDE.md but not a source-of-truth file itself
        # so this only hits rule (b) if not in exports/ — still blocks
        assert r.returncode == 2

    def test_block_write_to_agents_md_html(self):
        # AGENTS.md.html — outside source-of-truth files but outside exports too → block (b)
        r = _run(_write("AGENTS.html"))
        assert r.returncode == 2

    def test_block_edit_html_in_wiki(self):
        r = _run(_edit("wiki/concepts/test.html", "<h1>oops</h1>"))
        assert r.returncode == 2

    def test_block_html_in_wiki_deep_path(self):
        r = _run(_write("wiki/synthesis/cross-domain/output.html"))
        assert r.returncode == 2


# ── (b) BLOCK: .html outside allowed zones ───────────────────────────────

class TestBlockHtmlOutsideAllowedZones:

    def test_block_html_in_repo_root(self):
        r = _run(_write("report.html"))
        assert r.returncode == 2
        assert "BLOCKED" in r.stderr

    def test_block_html_in_scripts(self):
        r = _run(_write("scripts/output.html"))
        assert r.returncode == 2

    def test_block_html_in_skills_non_template(self):
        r = _run(_write("skills/render-html/output.html"))
        assert r.returncode == 2

    def test_block_multiedit_html_in_wiki(self):
        payload = _multiedit("wiki/test.html", [{"new_string": "<p>bad</p>"}])
        r = _run(payload)
        assert r.returncode == 2


# ── (d) ALLOW: .html in exports/html/ and templates/ ─────────────────────

class TestAllowHtmlInAllowedZones:

    def test_allow_html_in_exports_html(self):
        r = _run(_write("exports/html/report-20260605.html", "<html><body></body></html>"))
        assert r.returncode == 0

    def test_allow_html_in_exports_html_subpath(self):
        r = _run(_write("exports/html/plan-20260601-102203.html"))
        assert r.returncode == 0

    def test_allow_html_in_templates(self):
        r = _run(_write("skills/render-html/templates/custom.html"))
        assert r.returncode == 0

    def test_allow_edit_html_in_templates(self):
        r = _run(_edit("skills/render-html/templates/report.html", "<div>{{data}}</div>"))
        assert r.returncode == 0


# ── (c) WARN: .md with >=12 rows + report keywords → advisory, exit 0 ───

REPORT_TABLE_14_ROWS = """## Code Review Findings

| File | Severity | Line | Issue |
|---|---|---|---|
| auth.py | HIGH | 42 | SQL injection |
| api.py | LOW | 88 | missing timeout |
| db.py | MED | 13 | no connection pool |
| ui.tsx | HIGH | 5 | XSS in render |
| cache.py | LOW | 201 | unbounded growth |
| worker.py | MED | 77 | error handler |
| config.py | HIGH | 10 | hardcoded secret |
| router.py | LOW | 44 | n+1 query |
| utils.py | MED | 99 | no validation |
| models.py | HIGH | 33 | SQL injection |
| views.py | LOW | 12 | missing auth |
| forms.py | MED | 67 | no csrf |
| tests.py | LOW | 5 | no assertions |
| admin.py | HIGH | 88 | open redirect |
"""


class TestRenderDontDumpAdvisory:

    def test_large_report_md_exits_zero_with_advisory(self):
        r = _run(_write("wiki/synthesis/review.md", REPORT_TABLE_14_ROWS))
        assert r.returncode == 0, "advisory must NOT block"
        assert "render-don't-dump" in r.stderr.lower() or "render" in r.stderr.lower()

    def test_small_table_no_advisory(self):
        small = "| A | B |\n|---|---|\n| 1 | 2 |\n| 3 | 4 |"
        r = _run(_write("wiki/test.md", small))
        assert r.returncode == 0
        assert "render" not in r.stderr.lower()

    def test_large_table_without_keywords_no_advisory(self):
        # 20 data rows but no report keywords
        rows = "\n".join(f"| item_{i} | val_{i} |" for i in range(20))
        content = "| Name | Value |\n|---|---|\n" + rows
        r = _run(_write("wiki/test.md", content))
        assert r.returncode == 0
        assert "render" not in r.stderr.lower()

    def test_report_keywords_but_small_table_no_advisory(self):
        # has "severity" keyword but only 3 data rows
        small = "| File | Severity |\n|---|---|\n| a.py | HIGH |\n| b.py | LOW |\n| c.py | MED |"
        r = _run(_write("wiki/test.md", small))
        assert r.returncode == 0
        assert "render" not in r.stderr.lower()

    def test_advisory_for_edit_tool(self):
        r = _run(_edit("wiki/analysis.md", REPORT_TABLE_14_ROWS))
        assert r.returncode == 0

    def test_advisory_for_multiedit_tool(self):
        payload = _multiedit("wiki/analysis.md", [{"new_string": REPORT_TABLE_14_ROWS}])
        r = _run(payload)
        assert r.returncode == 0


# ── (e) Edge cases ────────────────────────────────────────────────────────

class TestEdgeCases:

    def test_non_write_tool_passes(self):
        r = _run({"tool_name": "Bash", "tool_input": {"command": "ls"}})
        assert r.returncode == 0

    def test_no_file_path_passes(self):
        r = _run({"tool_name": "Write", "tool_input": {}})
        assert r.returncode == 0

    def test_parse_fail_passes(self):
        result = subprocess.run(
            [sys.executable, str(HOOK_PATH)],
            input="not json at all",
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0

    def test_md_file_with_no_content_passes(self):
        r = _run(_write("wiki/test.md", ""))
        assert r.returncode == 0

    def test_multiedit_aggregates_content(self):
        """MultiEdit with html in new_string of a .html path → blocked."""
        payload = _multiedit("wiki/out.html", [
            {"new_string": "<h1>part1</h1>"},
            {"new_string": "<p>part2</p>"},
        ])
        r = _run(payload)
        assert r.returncode == 2

    def test_hook_skip_env(self):
        """HOOK_SKIP silences the hook when called via auto-discover (no specific name)."""
        import subprocess as sp
        env = os.environ.copy()
        env["HOOK_SKIP"] = "check_output_format.py"
        # Call the hook DIRECTLY (not via hooks_runner) — HOOK_SKIP is a hooks_runner feature.
        # When the hook itself runs, HOOK_SKIP has no effect; it's purely hooks_runner-level.
        # Verify: hook still blocks even with HOOK_SKIP set (hook doesn't read that env var).
        r = sp.run(
            [sys.executable, str(HOOK_PATH)],
            input=json.dumps(_write("wiki/bad.html")),
            capture_output=True, text=True, cwd=str(REPO_ROOT), env=env,
        )
        # Hook itself always runs — HOOK_SKIP is hooks_runner's concern, not the hook's
        assert r.returncode == 2

    def test_absolute_path_in_wiki_still_blocked(self):
        abs_path = str(REPO_ROOT / "wiki" / "entities" / "test.html")
        r = _run(_write(abs_path))
        assert r.returncode == 2
