#!/usr/bin/env python3
"""
Hook: Rabies Report Invariant Validator (V13 anti-hallucination)
----------------------------------------------------------------
Validates the structure + arithmetic invariants of `classify_rabies.py` JSON
output BEFORE the file lands on disk. The engine's in-run assertions (V1-V12)
catch most bugs, but AI agents editing the JSON directly — or bugs in
JSON serialization — can still produce malformed output.

Fires on: Write/Edit/MultiEdit to **/rabiesvac*.json OR **/rabies_review*.json
(both naming patterns used by classify_rabies.py `--json` output).

Invariants checked:
  (a) Required top-level keys present: report, cases
  (b) `len(cases) > 0` — empty report (silent date bug) blocked
  (c) Sum-of-cells: complete_IM + complete_ID + sub5_IM + sub5_ID +
      incomplete_IM + incomplete_ID + review == len(cases)
  (d) ERIG/HRIG counts ≤ len(cases)
  (e) Every case has valid cat ∈ {complete, sub5, incomplete, REVIEW}
      and route ∈ {IM, ID, MIXED, NONE}

Block (exit 2) on any violation. Override: HOOK_SKIP=check_rabies_report

Why this hook exists (audit 2026-08-12):
  Engine assertions only fire when `classify_rabies.py` is invoked. If an AI
  agent hand-writes a JSON file (e.g., to "fix a typo" or "regenerate the
  report"), no engine code runs and invariants can silently fail. This hook
  guards the OUTPUT FILE regardless of how it was produced.

Reference: skills/awiki/a-rabies-report/SKILL.md v1.4.0 anti-hallucination layer.
"""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path


HOOK_NAME = "check_rabies_report"
REQUIRED_REPORT_KEYS = {
    "complete_IM", "complete_ID",
    "sub5_IM", "sub5_ID",
    "incomplete_IM", "incomplete_ID",
    "erig", "hrig", "review",
}
VALID_CATS = {"complete", "sub5", "incomplete", "REVIEW"}
VALID_ROUTES = {"IM", "ID", "MIXED", "NONE"}


def _is_target_surface(file_path: str) -> bool:
    """Match rabies JSON output paths only. Returns True if path looks like:
       - **/rabiesvac*.json
       - **/rabies_review*.json
       - **/rabiesvac_review*.json
    """
    if not file_path:
        return False
    p = Path(file_path).name.lower()
    if not p.endswith(".json"):
        return False
    return ("rabiesvac" in p) or ("rabies_review" in p) or ("rabies-breakdown" in p)


def _final_write_content(tool_name: str, tool_input: dict, file_path: str) -> str | None:
    """Reconstruct the post-edit file content for Write/Edit/MultiEdit.
    Returns None if content cannot be reconstructed (skip — don't block)."""
    if tool_name == "Write":
        return tool_input.get("content", "")
    if tool_name in ("Edit", "MultiEdit"):
        # Read current file and apply edits (mirror check_skill_registry pattern)
        try:
            current = Path(file_path).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return None
        if tool_name == "Edit":
            old = tool_input.get("old_string", "")
            new = tool_input.get("new_string", "")
            if old and old in current:
                return current.replace(old, new, 1)
            return None
        # MultiEdit
        edits = tool_input.get("edits", [])
        for e in edits:
            old, new = e.get("old_string", ""), e.get("new_string", "")
            if old and old in current:
                current = current.replace(old, new, 1)
        return current
    return None


def _evaluate(content: str) -> str | None:
    """Return None if content passes all invariants, else return reason string."""
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        return f"file is not valid JSON ({e.msg} at line {e.lineno} col {e.colno})"

    if not isinstance(data, dict):
        return f"top-level JSON must be an object, got {type(data).__name__}"

    # (a) required keys
    report = data.get("report")
    cases = data.get("cases")
    if report is None:
        return "missing required key 'report' (engine output must include 9-cell dict)"
    if cases is None:
        return "missing required key 'cases' (engine output must include case list)"
    if not isinstance(report, dict):
        return f"'report' must be a dict, got {type(report).__name__}"
    if not isinstance(cases, list):
        return f"'cases' must be a list, got {type(cases).__name__}"

    missing = REQUIRED_REPORT_KEYS - set(report.keys())
    if missing:
        return f"'report' missing keys: {sorted(missing)}"

    # (b) non-empty
    if len(cases) == 0:
        return ("'cases' is empty — engine produced 0 cases. Likely causes: "
                "date format wrong (use YYYY-MM-DD CE not BE 2569), period "
                "start > end, or wrong file passed as `quarter` arg.")

    # (c) sum-of-cells invariant
    cells_sum = sum(report[k] for k in (
        "complete_IM", "complete_ID",
        "sub5_IM", "sub5_ID",
        "incomplete_IM", "incomplete_ID",
        "review",
    ))
    # (e) every case has valid cat + route — check FIRST so a dead-code
    # regression (e.g. 'ig_only' cat) is reported clearly, not masked by
    # sum-mismatch.
    bad_cases = []
    for i, c in enumerate(cases):
        if not isinstance(c, dict):
            bad_cases.append(f"case[{i}] not a dict")
            continue
        cat = c.get("cat")
        route = c.get("route")
        if cat not in VALID_CATS:
            bad_cases.append(f"case[{i}] cat={cat!r} not in {sorted(VALID_CATS)}")
        if route not in VALID_ROUTES:
            bad_cases.append(f"case[{i}] route={route!r} not in {sorted(VALID_ROUTES)}")
        if len(bad_cases) >= 3:
            bad_cases.append("...(more)")
            break
    if bad_cases:
        return "invalid case entries: " + "; ".join(bad_cases)

    if cells_sum != len(cases):
        return (f"sum-of-cells invariant violated: "
                f"complete+sub5+incomplete+review = {cells_sum}, "
                f"but len(cases) = {len(cases)}. Cases were silently dropped.")

    # (d) ERIG/HRIG sanity
    for ig_key in ("erig", "hrig"):
        if report[ig_key] > len(cases):
            return (f"{ig_key.upper()} count ({report[ig_key]}) > total cases "
                    f"({len(cases)}) — immunoglobulin was double-counted.")

    return None


def main() -> int:
    try:
        input_data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        # Not a hook event — could be a manual pipe test
        return 0

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if tool_name not in ("Edit", "Write", "MultiEdit"):
        return 0
    if not _is_target_surface(file_path):
        return 0

    content = _final_write_content(tool_name, tool_input, file_path)
    if content is None:
        # Can't reconstruct — don't block (fail-open like other hooks)
        return 0

    reason = _evaluate(content)
    if reason is None:
        return 0

    sys.stderr.write(
        f"🚫 [{HOOK_NAME}] Blocked {tool_name} to {file_path}\n"
        f"   reason: {reason}\n"
        f"   fix:   re-run `python scripts/hospital/classify_rabies.py ... --json <path>` "
        f"to regenerate valid output. Do NOT hand-edit the JSON.\n"
        f"   override (emergency): HOOK_SKIP={HOOK_NAME}\n"
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
