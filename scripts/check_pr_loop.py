#!/usr/bin/env python3
"""check_pr_loop.py — Universal Loop Contract gate (CI-enforced).

 stdin: JSON {"body": "<PR body markdown>", "files": ["changed/path", ...]}
 exit: 0 pass / 1 fail (reasons on stdout)

Rules (AGENTS.md "Universal Loop Contract"):
  1. The PR body must carry a `## Loop-Evidence` section that references
     a work order or finding (WO-… / R-FR-… / finding / M<digit>) and
     says what was tested — chat memory is not evidence.
  2. If production code changed, tests must change too (Iron Law #1 at
     PR level). Docs-only and test-only PRs are exempt from rule 2.

This is the vendor-neutral enforcement point: every agent lands in the
same CI, so the contract binds GLM, GPT, Claude, Codex and any future
operator equally.
"""
from __future__ import annotations

import json
import re
import sys

# Locale pipes (Thai-Windows cp874 etc.) crash printing ✅ status output;
# pin pipes to UTF-8 like scripts/hooks_runner.py does.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError, ValueError):
        pass

_EVIDENCE_HEADER = re.compile(r"^#{1,3}\s*Loop-Evidence\s*$", re.I | re.M)
_REFERENCE = re.compile(r"\b(WO-[A-Za-z0-9-]+|R-[A-Z]+-\d+|finding|M\d\b)", re.I)
_TESTED_HINT = re.compile(r"test|pytest|verify|e2e|eval", re.I)

_PROD_CODE = re.compile(
    r"\.(py|js|ts|tsx|sh|ps1|sql)$", re.I)
_PROD_PATH = re.compile(r"^(scripts|conductor|awiki_cli|\.github/workflows)/")
_EXEMPT_PATH = re.compile(r"^(tests/|docs/|wiki/|skills/.*SKILL\.md$)")


def _is_prod(path: str) -> bool:
    if _EXEMPT_PATH.match(path):
        return False
    return bool(_PROD_CODE.search(path) and _PROD_PATH.match(path))


def check_pr(body: str, files: list[str]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if not body or not body.strip():
        return False, ["PR body is empty — attach the Loop-Evidence section "
                       "(see .github/PULL_REQUEST_TEMPLATE.md)"]
    m = _EVIDENCE_HEADER.search(body)
    if not m:
        reasons.append("PR body missing a '## Loop-Evidence' section — the "
                       "loop trail (WO/finding + what was tested) must live "
                       "in the PR, not chat memory")
        section = ""
    else:
        section = body[m.end():]
        nxt = re.search(r"^#{1,3}\s+\S", section, re.M)
        if nxt:
            section = section[:nxt.start()]
    if m and not _REFERENCE.search(section):
        reasons.append("Loop-Evidence has no WO/finding reference "
                       "(WO-… / R-FR-… / finding / M<digit>)")
    if m and not _TESTED_HINT.search(section):
        reasons.append("Loop-Evidence does not say what was tested "
                       "(test/pytest/verify/e2e/eval)")
    prod = [f for f in files if _is_prod(f)]
    has_tests = any(f.startswith("tests/") for f in files)
    if prod and not has_tests:
        reasons.append(
            f"production code changed without tests: {prod[:3]} — Iron Law #1 "
            "(test-first) applies at PR level; add/extend a test in tests/")
    return (not reasons), reasons


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError as e:
        print(f"invalid JSON payload: {e}")
        return 1
    ok, reasons = check_pr(payload.get("body", ""),
                           payload.get("files", []))
    for r in reasons:
        print(f"❌ {r}")
    if ok:
        print("✅ Universal Loop Contract satisfied (evidence present, "
              "tests paired with production code)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
