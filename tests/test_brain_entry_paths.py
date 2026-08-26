"""BRAIN-ENTRY common paths — G5b: a fresh agent reaches the right tool
in <=3 hops by READING (no memory), and every referenced file exists."""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ENTRY = (REPO_ROOT / "BRAIN-ENTRY.md").read_text(encoding="utf-8")


def test_common_paths_table_exists_with_all_expected_scenarios():
    for scenario in ("resume", "fuzzy", "implement", "bug", "release",
                     "defect"):
        assert scenario in ENTRY, f"missing common path scenario: {scenario}"


def test_every_referenced_repo_file_exists():
    """Dead links already bit this repo once (48 hard errors) — the entry
    must never point at a file that does not exist."""
    refs = set(re.findall(r"`([\w./-]+\.(?:md|yaml|json))`", ENTRY))
    assert refs, "entry should reference concrete files"
    # machine-local exemptions (never present on CI, by design):
    # drive/* (private junction layer) and session-memory.md (per-machine
    # private memory; BRAIN-ENTRY itself notes it may be absent)
    EXEMPT_PREFIX = ("drive/",)
    EXEMPT_FILES = {"wiki/context/session-memory.md"}
    missing = [r for r in refs
               if not any(r.startswith(pfx) for pfx in EXEMPT_PREFIX)
               and r not in EXEMPT_FILES
               and not (REPO_ROOT / r).is_file()]
    assert not missing, f"BRAIN-ENTRY references missing files: {missing}"


def test_bug_path_reaches_debug_mantra_within_three_hops():
    """Fresh-agent simulation: follow ONLY what the entry tells us to read.
    bug path -> protocols/defect-memory.md (or skills via registry) must
    surface debug-mantra within 3 file-reads from BRAIN-ENTRY."""
    hop_files = [REPO_ROOT / "BRAIN-ENTRY.md"]
    seen_text = ENTRY
    for _ in range(3):  # up to 3 additional hops
        if "debug-mantra" in seen_text:
            break
        next_refs = [REPO_ROOT / r for r in
                     re.findall(r"`([\w./-]+\.md)`", seen_text)
                     if (REPO_ROOT / r).is_file()]
        hop_files.extend(next_refs)
        seen_text = "\n".join(p.read_text(encoding="utf-8", errors="replace")
                              for p in next_refs)
    assert "debug-mantra" in seen_text, (
        "debug-mantra not reachable within 3 hops from BRAIN-ENTRY "
        f"(hops read: {[p.name for p in hop_files]})")
