"""a_loop_skill.py — A-Loop Phase 4: propose skill from repeated failure.

Phase 3 (a_loop_distill.py) detects failure patterns and writes type=idea
entries. Phase 4 takes a confirmed pattern and proposes a NEW skill to
prevent that failure class — then, ONLY after user approval, registers it
via new-skill.py --apply (Iron Law #9: registry-first).

Design:
  - propose_skill_for_pattern() → returns a DRAFT dict (no side effects)
  - apply_proposal(proposal) → shells out to new-skill.py --apply
  - User/agent must explicitly call apply_proposal() — never automatic
  - Name generation: kebab-case from tag, prefix 'guard-' to signal origin
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
NEW_SKILL_SCRIPT = REPO_ROOT / "scripts" / "new-skill.py"


def _to_kebab(text: str) -> str:
    """Convert arbitrary text to kebab-case (lowercase, dash-separated)."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    return text or "unnamed"


def propose_skill_for_pattern(
    *,
    tag: str,
    failure_count: int,
    sample_summaries: list[str],
) -> dict[str, Any]:
    """Build a skill proposal draft from a repeated failure pattern.

    Returns a dict with: name, description, domain, phase, category,
    rationale, samples. NO side effects — caller decides whether to apply.
    """
    kebab_tag = _to_kebab(tag)
    # Prefix 'guard-' to signal this skill prevents a failure class
    name = f"guard-{kebab_tag}"
    description = (
        f"Guard skill auto-proposed by A-Loop: prevents the '{tag}' failure "
        f"class (seen {failure_count}x)."
    )
    samples_str = "; ".join(sample_summaries[:3])
    rationale = (
        f"Failure pattern '{tag}' occurred {failure_count} times. "
        f"Samples: {samples_str}. A guard skill can add a check/test/hook "
        f"to prevent this class of failure."
    )
    return {
        "name": name,
        "description": description,
        "domain": "engineering",
        "phase": "verify",  # guards run in verify phase
        "category": "guard",
        "rationale": rationale,
        "samples": sample_summaries[:5],
        "failure_count": failure_count,
        "source_tag": tag,
    }


def apply_proposal(
    proposal: dict[str, Any],
    *,
    repo_root: Path | str = REPO_ROOT,
) -> bool:
    """Register the proposed skill via new-skill.py --apply.

    Returns True on success (new-skill.py exit 0), False on failure.
    Iron Law #9: new-skill.py handles registry-first ordering that
    check_skill_registry.py enforces.
    """
    repo_root = Path(repo_root)
    cmd = [
        sys.executable,
        str(repo_root / "scripts" / "new-skill.py"),
        proposal["name"],
        "--domain", proposal.get("domain", "engineering"),
        "--phase", proposal.get("phase", "build"),
        "--category", proposal.get("category", "uncategorized"),
        "--description", proposal.get("description", ""),
        "--apply",
    ]
    try:
        result = subprocess.run(
            cmd, cwd=str(repo_root), capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=30,
        )
        if result.returncode != 0:
            sys.stderr.write(
                f"[a-loop-skill] new-skill.py failed: {result.stderr.strip()}\n"
            )
            return False
        return True
    except Exception as e:
        sys.stderr.write(f"[a-loop-skill] apply error: {e}\n")
        return False
