"""
Regression test for scripts/wiki/export-to-notebooklm.sh.

Root cause (2026-07-11): the script was moved from scripts/ into
scripts/wiki/ but its REPO_ROOT still resolved to "${SCRIPT_DIR}/.."
(= scripts/, one level short). It then bundled from a nonexistent
scripts/wiki/entities tree — producing 11-line empty bundles — and wrote
them to a stray scripts/exports/ directory instead of exports/notebooklm/.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "wiki" / "export-to-notebooklm.sh"


def test_export_writes_real_bundles_at_repo_root() -> None:
    result = subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=REPO_ROOT,
        timeout=300,
    )
    assert result.returncode == 0, result.stderr[-400:]

    out = REPO_ROOT / "exports" / "notebooklm" / "iot.md"
    assert out.exists(), (
        "bundle must land at <repo>/exports/notebooklm/, "
        f"stdout tail: {result.stdout[-300:]!r}"
    )
    # A real IoT bundle carries dozens of wiki pages — an empty-header
    # bundle (the bug) is ~500 bytes.
    assert out.stat().st_size > 10_000, (
        f"iot.md is only {out.stat().st_size} bytes — bundling from a "
        "nonexistent tree again?"
    )
    # The buggy path must not come back.
    assert not (REPO_ROOT / "scripts" / "exports").exists(), (
        "script wrote into scripts/exports/ — REPO_ROOT resolution is "
        "one level short again"
    )
