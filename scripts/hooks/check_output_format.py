#!/usr/bin/env python3
"""
Hook: Output Format Guard
-------------------------
Enforces the 3-layer output-format protocol on file writes.

Layer 1 (Durable):   Markdown only — wiki/, docs/, CLAUDE.md, AGENTS.md
Layer 2 (Machine):   Most compact — CSV/JSONL/JSON (never HTML)
Layer 3 (Human):     JSON → render.py → leaf HTML in exports/html/ (gitignored)

Rules:
  (a) BLOCK (exit 2): .html written into source-of-truth dirs/files
  (b) BLOCK (exit 2): .html written outside allowed zones
  (c) WARN  (exit 0): .md with >=12 data-table rows + report keywords
                      → advisory "render-don't-dump" (never blocks, gated to
                        reduce false-positives on legitimate long wiki tables)

Allowed .html zones: exports/html/  |  skills/render-html/templates/
Silenceable:         HOOK_SKIP=check_output_format

See: docs/protocols/md-vs-html-output.md
"""
from __future__ import annotations

import json
import os
import re
import sys

REPO_ROOT = os.path.realpath(os.path.join(os.path.dirname(__file__), "../.."))

# Pattern: markdown table data row (has | on both sides, not a separator)
_TABLE_ROW = re.compile(r"^\s*\|.*\|\s*$")
# Pattern: separator row |---|:--:|  — exclude from data-row count
_SEP_ROW = re.compile(r"^\s*\|?[\s:-]+\|[\s:|-]*$")

# Keywords that signal a "report-style" document (i.e. should use render-html)
_REPORT_KW = re.compile(
    r"severity|critical|warning|finding|post-?mortem|code[ -]?review"
    r"|\bdiff\b|comparison|audit|dashboard|digest|reconcil",
    re.IGNORECASE,
)

ROW_THRESHOLD = 12  # data rows before advisory fires (above Decision Threshold table)


# ── helpers ─────────────────────────────────────────────────────────────

def _abs(path: str) -> str:
    """Resolve to absolute realpath (resolves symlinks like drive/raw/ -> raw/)."""
    if os.path.isabs(path):
        return os.path.realpath(path)
    return os.path.realpath(os.path.join(REPO_ROOT, path))


def _under(child: str, parent: str) -> bool:
    """Return True if child is inside parent (or equal), using commonpath."""
    try:
        return os.path.commonpath([parent, child]) == parent
    except ValueError:
        return False  # different drives on Windows


def _content(tool: str, ti: dict) -> str:
    """Extract the text content being written from different tool input shapes."""
    if tool == "Write":
        return ti.get("content") or ""
    if tool == "Edit":
        return ti.get("new_string") or ""
    if tool == "MultiEdit":
        edits = ti.get("edits") or []
        return "\n".join(e.get("new_string") or "" for e in edits)
    return ""


def _count_data_rows(text: str) -> int:
    """Count Markdown table data rows (excludes separator rows)."""
    lines = text.splitlines()
    has_sep = any(_SEP_ROW.match(ln) for ln in lines)
    data_rows = [ln for ln in lines if _TABLE_ROW.match(ln) and not _SEP_ROW.match(ln)]
    # If there's a separator, the first row is a header — subtract it
    return max(0, len(data_rows) - (1 if has_sep else 0))


# ── zone definitions ─────────────────────────────────────────────────────

def _build_zones() -> tuple[list[str], set[str], list[str]]:
    """Return (source_dirs, source_files, allowed_html_dirs)."""
    src_dirs = [
        _abs("wiki"),
        _abs("raw"),
        _abs("docs"),
    ]
    src_files = {
        _abs("CLAUDE.md"),
        _abs("AGENTS.md"),
    }
    allowed_html = [
        _abs("exports/html"),
        _abs("skills/render-html/templates"),
        _abs("scripts/live-dashboard"),
    ]
    return src_dirs, src_files, allowed_html


# ── main ─────────────────────────────────────────────────────────────────

def main() -> int:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0  # fail-open on parse error

    tool = data.get("tool_name", "")
    ti = data.get("tool_input") or {}
    fp = ti.get("file_path", "")

    if tool not in ("Edit", "Write", "MultiEdit") or not fp:
        return 0

    abs_fp = _abs(fp)
    low_fp = abs_fp.lower()

    src_dirs, src_files, allowed_html = _build_zones()

    # ── Rule (a) + (b): .html file ──────────────────────────────────────
    if low_fp.endswith(".html"):
        # (a) block .html into source-of-truth
        if abs_fp in src_files or any(_under(abs_fp, d) for d in src_dirs):
            sys.stderr.write(
                "BLOCKED (output-format): .html ลงใน source-of-truth\n\n"
                f"ไฟล์: {fp}\n\n"
                "Source-of-truth ต้องเป็น Markdown เท่านั้น (Layer 1).\n"
                "HTML คือ terminal leaf — ต้องผ่าน render.py ไปที่ exports/html/\n\n"
                "  python3 skills/render-html/scripts/render.py <surface> --in data.json\n\n"
                "ดู: docs/protocols/md-vs-html-output.md\n"
            )
            return 2

        # (b) block .html outside allowed zones
        if not any(_under(abs_fp, d) for d in allowed_html):
            sys.stderr.write(
                "BLOCKED (output-format): .html นอก allowed zones\n\n"
                f"ไฟล์: {fp}\n\n"
                "Rendered HTML ต้องอยู่ใน exports/html/ (gitignored, ephemeral)\n"
                "หรือ skills/render-html/templates/ (template source)\n\n"
                "  python3 skills/render-html/scripts/render.py <surface> --in data.json\n"
                "  → output ไปที่ exports/html/<surface>-<timestamp>.html\n\n"
                "ดู: docs/protocols/md-vs-html-output.md\n"
            )
            return 2

        return 0

    # ── Rule (c): .md with large report-style table → advisory ──────────
    if low_fp.endswith(".md"):
        c = _content(tool, ti)
        if c:
            data_rows = _count_data_rows(c)
            if data_rows >= ROW_THRESHOLD and _REPORT_KW.search(c):
                sys.stderr.write(
                    f"ADVISORY (render-don't-dump): .md มีตาราง ~{data_rows} data rows "
                    "+ report keywords\n\n"
                    "พิจารณาใช้ render-html แทน:\n"
                    "  1. สร้าง data.json\n"
                    "  2. python3 skills/render-html/scripts/render.py audit --in data.json\n"
                    "  3. ตอบแค่ path + สรุป 1-3 บรรทัด\n\n"
                    "ถ้าตารางนี้ถูกต้องใน wiki/docs ให้ตั้ง HOOK_SKIP=check_output_format\n"
                    "ดู: docs/protocols/md-vs-html-output.md\n"
                )
                # advisory only — exit 0, never block

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
