"""
quality_gate.py — Validate one IngestResult before writing wiki/sources/.

Checks the model output matches the contract enforced by
scripts/hooks/check_source_original_file.py + the YAML frontmatter
template in wiki/CLAUDE.md.

Returns (is_valid, reason). Reasons help the router decide whether to
escalate to the next tier or hand the file back to the user.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_KEYS = ("type", "title", "slug", "date_ingested", "original_file", "tags", "routed_via")


def _parse_frontmatter(content: str) -> tuple[bool, dict[str, str]]:
    """Return (has_frontmatter, {key: raw_value})."""
    if not content.startswith("---"):
        return False, {}
    end = content.find("\n---", 3)
    if end < 0:
        return False, {}
    body = content[3:end].strip()
    out: dict[str, str] = {}
    for line in body.splitlines():
        line = line.rstrip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", line)
        if m:
            out[m.group(1)] = m.group(2).strip()
    return True, out


def validate(content: str, *, expected_slug: str, expected_raw_path: str) -> tuple[bool, str]:
    if not content or not content.strip():
        return False, "empty output"

    has_fm, fm = _parse_frontmatter(content)
    if not has_fm:
        return False, "missing YAML frontmatter (does not start with ---)"

    missing = [k for k in REQUIRED_KEYS if k not in fm]
    if missing:
        return False, f"frontmatter missing keys: {', '.join(missing)}"

    if fm.get("type", "").strip().strip('"').strip("'") != "source":
        return False, f"type must be 'source', got {fm.get('type')!r}"

    routed = fm.get("routed_via", "").strip().strip('"').strip("'")
    if not re.match(r"^harness@v\d+$", routed):
        return False, f"routed_via must match 'harness@v\\d+', got {routed!r}"

    of = fm.get("original_file", "").strip().strip('"').strip("'")
    if of.startswith("./"):
        of = of[2:]
    if not of.startswith("raw/"):
        return False, f"original_file must start with raw/, got {of!r}"

    abs_p = (REPO_ROOT / of).resolve()
    try:
        if not abs_p.is_file():
            return False, f"original_file points to missing file: {of}"
    except OSError as e:
        return False, f"original_file resolve error: {e}"

    if of != expected_raw_path:
        return False, f"original_file mismatch: got {of!r}, expected {expected_raw_path!r}"

    slug = fm.get("slug", "").strip().strip('"').strip("'")
    if slug != expected_slug:
        return False, f"slug mismatch: got {slug!r}, expected {expected_slug!r}"

    return True, "ok"


def should_escalate(results: list, threshold_pct: int) -> tuple[bool, list[str]]:
    """If too many results failed validation, return (True, [failed_slugs])."""
    if not results:
        return False, []
    failed = [r for r in results if not r.success or not r.metadata.get("validated")]
    pct = len(failed) * 100 // len(results)
    return pct >= threshold_pct, [r.slug for r in failed]
