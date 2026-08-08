#!/usr/bin/env python3
"""fixes_backfill.py — one-shot converter: wiki/concepts/it-support/*.md → fixes.json entries.

KEEP-MARKER: manual-authoring-tool — this file is intentionally NOT imported by
any other module. It is run on demand by a human (see usage below) to backfill
fixes.json from wiki pages. Do NOT delete as a "dead script" in audits — its
lack of importers is by design, not a sign of abandonment. Related to the
dashboard Fixes module (fixes.html / fixes.json / /api/fixes).

Scans it-support concept pages (the canonical "fix knowledge" format), extracts
YAML frontmatter + the Thai section schema (## อาการ / ## สาเหตุ / ## วิธีแก้ไข /
## วินิจฉัยเบื้องต้น), and emits a draft fixes.json the user can review and merge.

This is NOT wired into the server — it is a manual authoring aid, run on demand:

    python scripts/live-dashboard/fixes_backfill.py            # prints draft entries
    python scripts/live-dashboard/fixes_backfill.py --merge     # merges into fixes.json

Design notes
------------
- Idempotent: re-running on the same source does not duplicate entries (keyed by id).
- Preserves existing hand-authored entries in fixes.json.
- Best-effort parsing: it-support pages are human-authored Markdown with a soft
  schema. Pages missing a section are still imported (with empty arrays), so the
  human reviewer can fill the gaps.
- Privacy: emits a warning if a page contains anything that looks like a real
  hostname, IP, or path (use <PRINTER_IP> / <WORK_DIR> placeholders).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
IT_SUPPORT_DIR = REPO_ROOT / "wiki" / "concepts" / "it-support"
FIXES_JSON = Path(__file__).resolve().parent / "fixes.json"

# Regex patterns (DOTALL so multi-line sections match).
_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_SECTION_RE_TEMPLATE = r"^##\s+{heading}\s*\n(.*?)(?=^##\s+|\Z)"
_CODE_BLOCK_RE = re.compile(r"```(\w+)?\s*\n(.*?)```", re.DOTALL)

# Thai section headings used in it-support concept pages.
SECTIONS = {
    "symptoms": "อาการ",
    "root_cause": "สาเหตุ",
    "fix_steps": r"วิธีแก้ไข(?:\s*\(.*?\))?",
    "diagnostics": "วินิจฉัยเบื้องต้น",
}

# Privacy heuristics — placeholder policy from AGENTS.md Iron Law #6.
_PRIVACY_HINTS = [
    (re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"), "IP address (use <PRINTER_IP>)"),
    (re.compile(r"[A-Z]:\\Users\\", re.IGNORECASE), "Windows user path (use <WORK_DIR>)"),
    (re.compile(r"รพ\.[A-Za-z]", re.IGNORECASE), "real hospital name (use <HOSPITAL>)"),
]


def parse_frontmatter(text: str) -> dict:
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}
    fm_text = m.group(1)
    out: dict = {}
    for line in fm_text.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            value = value.strip()
            # crude YAML list parsing: [a, b, c]
            if value.startswith("[") and value.endswith("]"):
                value = [v.strip().strip("'\"") for v in value[1:-1].split(",") if v.strip()]
            out[key.strip()] = value
    return out


def extract_section(text: str, heading_pattern: str) -> str:
    pat = re.compile(_SECTION_RE_TEMPLATE.format(heading=heading_pattern), re.MULTILINE | re.DOTALL)
    m = pat.search(text)
    return m.group(1).strip() if m else ""


def parse_bullets(section_text: str) -> list[str]:
    """Extract `- item` or `* item` bullet points."""
    bullets = []
    for line in section_text.splitlines():
        line = line.strip()
        if line.startswith(("- ", "* ")):
            bullets.append(line[2:].strip())
        elif line and not line.startswith("#") and not line.startswith("```"):
            # Non-bullet line — treat as a standalone symptom line if non-empty.
            bullets.append(line)
    return [b for b in bullets if b]


def parse_numbered_steps(section_text: str) -> list[str]:
    """Extract `1. step` numbered steps."""
    steps = []
    for line in section_text.splitlines():
        m = re.match(r"^\s*(?:\d+[\.\)]|\*|-)\s+(.+)$", line)
        if m:
            steps.append(m.group(1).strip())
    return steps


def extract_scripts(text: str) -> list[dict]:
    """Extract fenced code blocks as script entries."""
    scripts = []
    for m in _CODE_BLOCK_RE.finditer(text):
        lang = (m.group(1) or "").lower()
        code = m.group(2).rstrip()
        if not code.strip():
            continue
        language = "powershell" if lang in ("ps", "ps1", "powershell") else \
                   "python" if lang in ("py", "python") else \
                   "bash" if lang in ("sh", "bash", "shell") else \
                   lang or "text"
        scripts.append({
            "label": f"{language} snippet",
            "language": language,
            "requires_admin": "admin" in code.lower() or "pnputil" in code.lower(),
            "os": ["windows"] if language == "powershell" else [],
            "code": code,
        })
    return scripts


def slug_from_path(path: Path) -> str:
    """brother-hl-l3270cdw-wsd-error.md → brother-hl-l3270cdw-wsd-error"""
    return path.stem


def detect_category(tags: list[str], title: str) -> str:
    text = " ".join(tags + [title]).lower()
    if any(k in text for k in ("printer", "brother", "hp ", "canon", "epson")):
        return "printer"
    if any(k in text for k in ("usb", "hardware", "device", "driver")):
        return "hardware"
    if any(k in text for k in ("network", "wifi", "dns", "ip", "firewall")):
        return "network"
    if any(k in text for k in ("security", "antivirus", "firewall", "password")):
        return "security"
    return "system"


def privacy_scan(text: str, source: str) -> list[str]:
    """Return list of privacy warnings for human review."""
    warnings = []
    for pat, label in _PRIVACY_HINTS:
        if pat.search(text):
            warnings.append(f"{label} found in {source}")
    return warnings


def convert_page(path: Path) -> tuple[dict | None, list[str]]:
    """Convert one it-support concept page to a fixes.json entry.

    Returns (entry_or_None, warnings). Returns None if the page is a CLAUDE.md
    or index file (not a fix page).
    """
    if path.name in ("CLAUDE.md", "index.md", "README.md") or path.name.startswith("index-"):
        return None, []

    text = path.read_text(encoding="utf-8")
    fm = parse_frontmatter(text)
    title_line = ""
    for line in text.splitlines():
        if line.startswith("# "):
            title_line = line[2:].strip()
            break

    warnings = privacy_scan(text, str(path.relative_to(REPO_ROOT)))

    tags = fm.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]

    symptoms_raw = extract_section(text, SECTIONS["symptoms"])
    root_cause_raw = extract_section(text, SECTIONS["root_cause"])
    fix_steps_raw = extract_section(text, SECTIONS["fix_steps"])
    diagnostics_raw = extract_section(text, SECTIONS["diagnostics"])

    # Use the fix + diagnostics sections for script extraction (not symptoms).
    scripts = extract_scripts(fix_steps_raw) + extract_scripts(diagnostics_raw)

    entry = {
        "id": slug_from_path(path),
        "title": title_line or path.stem.replace("-", " ").title(),
        "title_th": title_line,
        "device": "",
        "category": detect_category(tags, title_line),
        "os": ["windows"] if any("windows" in t for t in tags) else [],
        "tags": tags,
        "severity": "medium",
        "symptoms": parse_bullets(symptoms_raw),
        "root_cause": root_cause_raw.split("\n\n")[0].strip() if root_cause_raw else "",
        "steps": parse_numbered_steps(fix_steps_raw),
        "scripts": scripts,
        "source_doc": str(path.relative_to(REPO_ROOT)).replace("\\", "/"),
        "created": fm.get("created", str(date.today())),
        "updated": fm.get("updated", str(date.today())),
        "verified": fm.get("verified", ""),
        "related": [],
    }
    return entry, warnings


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--merge", action="store_true",
                    help="merge draft entries into fixes.json (default: dry-run print)")
    ap.add_argument("--source", type=Path, default=IT_SUPPORT_DIR,
                    help=f"source dir (default: {IT_SUPPORT_DIR})")
    args = ap.parse_args(argv)

    if not args.source.is_dir():
        print(f"ERROR: source dir not found: {args.source}", file=sys.stderr)
        return 1

    pages = sorted(args.source.glob("*.md"))
    pages = [p for p in pages if p.name not in ("CLAUDE.md",)]
    print(f"Scanning {len(pages)} page(s) in {args.source}...", file=sys.stderr)

    new_entries: list[dict] = []
    all_warnings: list[str] = []
    for page in pages:
        entry, warns = convert_page(page)
        if entry is None:
            continue
        new_entries.append(entry)
        all_warnings.extend(warns)

    if all_warnings:
        print("\n⚠️  Privacy warnings (review before merge):", file=sys.stderr)
        for w in all_warnings:
            print(f"   - {w}", file=sys.stderr)
        print(file=sys.stderr)

    # Load existing fixes.json if merging.
    existing_by_id: dict[str, dict] = {}
    schema_version = 1
    if FIXES_JSON.is_file():
        try:
            data = json.loads(FIXES_JSON.read_text(encoding="utf-8"))
            schema_version = data.get("schema_version", 1)
            for e in data.get("fixes", []):
                existing_by_id[e["id"]] = e
        except (json.JSONDecodeError, KeyError) as e:
            print(f"WARN: existing fixes.json unreadable ({e}); starting fresh", file=sys.stderr)

    # Merge: new entries replace existing ones with the same id (idempotent),
    # but preserve hand-authored entries whose id is not in the source pages.
    merged_ids = {e["id"] for e in new_entries}
    preserved = [v for k, v in existing_by_id.items() if k not in merged_ids]
    final_fixes = new_entries + preserved

    output = {
        "schema_version": schema_version,
        "generated_at": str(date.today()),
        "description": "A-Wiki Known Fixes — see fixes_backfill.py for regeneration.",
        "fixes": final_fixes,
    }

    if args.merge:
        FIXES_JSON.write_text(
            json.dumps(output, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8"
        )
        print(f"\n✅ Merged {len(new_entries)} new + {len(preserved)} preserved "
              f"= {len(final_fixes)} total → {FIXES_JSON}", file=sys.stderr)
    else:
        print(json.dumps(output, ensure_ascii=False, indent=2))
        print(f"\n(dry-run: {len(new_entries)} new, {len(preserved)} preserved. "
              f"Use --merge to write.)", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
