#!/usr/bin/env python3
"""parse_plan.py — Convert an A-Wiki plan .md file to the JSON schema expected by the plan HTML adapter.

Schema:
  {
    "title":          str,           # H1 title or first H2
    "generated_from": str,           # absolute path of the source .md file
    "sections":       [{             # one per H2 section
      "heading": str,
      "body":    str                 # raw markdown text (no leading heading line)
    }],
    "phases": [{                     # extracted from the "Phase" / "Rollout" section
      "id":     int,
      "name":   str,
      "detail": str,
      "status": "pending"
    }],
    "verify_cmds": [str]             # bash lines from the Verification code block
  }

Usage:
    python3 skills/render-html/scripts/parse_plan.py /path/to/plan.md   # stdout JSON
    python3 skills/render-html/scripts/parse_plan.py /path/to/plan.md | \
        python3 skills/render-html/scripts/render.py plan --in -
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


def parse(path: str) -> dict:
    text = Path(path).read_text(encoding="utf-8")

    # ── Title (H1 or first H2) ─────────────────────────────────────────────
    title_m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    title = title_m.group(1).strip() if title_m else Path(path).stem

    # ── Split into H2 sections ─────────────────────────────────────────────
    # Find all "## heading" positions (not ### or deeper)
    h2_iter = list(re.finditer(r"^##\s+(.+)$", text, re.MULTILINE))
    sections: list[dict] = []
    for i, m in enumerate(h2_iter):
        heading = m.group(1).strip()
        start = m.end()
        end = h2_iter[i + 1].start() if i + 1 < len(h2_iter) else len(text)
        body = text[start:end].strip()
        sections.append({"heading": heading, "body": body})

    # ── Phases (from section whose heading contains "Phase" or "Rollout") ──
    phases: list[dict] = []
    phase_body = ""
    for sec in sections:
        h = sec["heading"].lower()
        if "phase" in h or "rollout" in h:
            phase_body = sec["body"]
            break

    if phase_body:
        # Line-by-line: match "- **Phase X…**: detail" or "- **Phase X**  detail"
        for line in phase_body.splitlines():
            line = line.strip()
            if not line.startswith("-") and not line.startswith("*"):
                continue
            # Strip leading bullet
            line = re.sub(r"^[-*]\s+", "", line)
            # Try: **Phase X (tag):** detail  OR  **Phase X**: detail
            ph_m = re.match(r"\*{1,2}(Phase\s+\w+[^*]*?)\*{1,2}[:\s]*(.*)", line)
            if not ph_m:
                continue
            raw_name = ph_m.group(1).strip().rstrip(":").rstrip()
            rest = ph_m.group(2).strip()
            # If rest starts with a parenthetical tag like "(foundation):" pull it into name
            tag_m = re.match(r"(\([^)]+\))\s*[:\-]?\s*(.*)", rest, re.DOTALL)
            if tag_m:
                raw_name = raw_name + " " + tag_m.group(1)
                rest = tag_m.group(2)
            raw_detail = re.sub(r"\s+", " ", rest.strip())
            # Derive numeric id: digits first (Phase 0), then letters (Phase A → 0)
            id_m = re.search(r"(\d+)", raw_name)
            if id_m:
                phase_id = int(id_m.group(1))
            else:
                id_m = re.search(r"Phase\s+([A-Z])", raw_name)
                phase_id = ord(id_m.group(1)) - ord("A") if id_m else len(phases)
            phases.append({
                "id": phase_id,
                "name": raw_name,
                "detail": raw_detail or "(see plan for details)",
                "status": "pending",
            })

    # ── Verification commands (first bash/shell code block in Verification section) ──
    verify_cmds: list[str] = []
    verify_body = ""
    for sec in sections:
        h = sec["heading"].lower()
        if "verif" in h or "verify" in h:
            verify_body = sec["body"]
            break

    if verify_body:
        cb_m = re.search(r"```(?:bash|sh|shell)?\s*\n([\s\S]*?)```", verify_body)
        if cb_m:
            verify_cmds = [
                ln.strip()
                for ln in cb_m.group(1).splitlines()
                if ln.strip() and not ln.strip().startswith("#")
            ]

    return {
        "title": title,
        "generated_from": str(Path(path).resolve()),
        "sections": sections,
        "phases": phases,
        "verify_cmds": verify_cmds,
    }


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print("Usage: parse_plan.py <plan.md>", file=sys.stderr)
        return 1
    data = parse(args[0])
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
