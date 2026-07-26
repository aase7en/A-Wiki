"""a_loop_distill.py — A-Loop Phase 3: distill ideas from failure patterns.

Stop hook (or manual). Scans memory_ledger for repeated failure patterns
→ proposes type=idea entries → SessionStart surfaces them.

Design:
  - "Pattern" = failures sharing the same tag (or a keyword from summary)
  - min_count threshold (default 3) — isolated failures don't trigger
  - Idempotent: checks if an idea for this pattern already exists
  - Never blocks (exit 0). Override: HOOK_SKIP=a_loop_distill

This is the "Idea Distiller" half of A-Loop Phase 3. The other half
(Failure→Skill, Phase 4) is in references/phase-skill.md + future hook.
"""
from __future__ import annotations

import os
import sys
from collections import Counter
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
REPO_ROOT = HOOKS_DIR.parent.parent
LIB_DIR = REPO_ROOT / "scripts" / "lib"

sys.path.insert(0, str(LIB_DIR))
sys.path.insert(0, str(HOOKS_DIR))

import memory_ledger  # noqa: E402

DEFAULT_LEDGER_PATH = REPO_ROOT / ".tmp" / "memory-ledger.jsonl"
DEFAULT_MIN_COUNT = 3


def count_failure_patterns(
    ledger_path: Path | str = DEFAULT_LEDGER_PATH,
    *,
    min_count: int = DEFAULT_MIN_COUNT,
) -> list[dict]:
    """Find failure patterns that repeat >= min_count times.

    Groups by tag (first tag, or 'untagged' if none). Returns list of
    {tag, count, sample_summaries} sorted by count descending.
    """
    ledger = memory_ledger.MemoryLedger(ledger_path)
    entries = ledger._load_all()
    failures = [e for e in entries if e.get("type") == "failure"]
    if not failures:
        return []
    # Group by first tag (most specific)
    by_tag: dict[str, list[dict]] = {}
    for f in failures:
        tags = f.get("tags", [])
        key = tags[0] if tags else "untagged"
        by_tag.setdefault(key, []).append(f)
    patterns = []
    for tag, group in by_tag.items():
        if len(group) >= min_count:
            patterns.append({
                "tag": tag,
                "count": len(group),
                "sample_summaries": [g.get("summary", "")[:80] for g in group[:3]],
            })
    patterns.sort(key=lambda p: p["count"], reverse=True)
    return patterns


def propose_ideas(
    ledger_path: Path | str = DEFAULT_LEDGER_PATH,
    *,
    min_count: int = DEFAULT_MIN_COUNT,
) -> int:
    """Propose idea entries for repeated failure patterns.

    Idempotent: if an idea mentioning the pattern tag already exists, skip.
    Returns count of new ideas proposed.
    """
    patterns = count_failure_patterns(ledger_path, min_count=min_count)
    if not patterns:
        return 0
    ledger = memory_ledger.MemoryLedger(ledger_path)
    # Check existing ideas to avoid duplicates (idempotency)
    existing_ideas = [
        e for e in ledger._load_all()
        if e.get("type") == "idea"
    ]
    existing_idea_tags = set()
    for idea in existing_ideas:
        for t in idea.get("tags", []):
            existing_idea_tags.add(t.lower())
    # Also check summary text for the pattern tag word
    existing_idea_text = " ".join(
        e.get("summary", "").lower() for e in existing_ideas
    )

    proposed = 0
    for p in patterns:
        tag = p["tag"]
        # Idempotency check: skip if we already proposed an idea for this tag
        idea_tag_marker = f"distill:{tag.lower()}"
        if idea_tag_marker in existing_idea_tags:
            continue
        if tag.lower() in existing_idea_text and "distill" in existing_idea_text:
            continue
        # Propose
        summary = (
            f"Repeated failure pattern '{tag}' ({p['count']}x). "
            f"Consider: guard/prevent/test for this. Samples: {'; '.join(p['sample_summaries'][:2])}"
        )
        ledger.append(
            session_id="a-loop-distill",
            type="idea",
            summary=summary,
            tags=[idea_tag_marker, "a-loop", "distill"],
        )
        proposed += 1
    return proposed


def auto_propose_skill(
    ledger_path: Path | str = DEFAULT_LEDGER_PATH,
    *,
    min_count: int = DEFAULT_MIN_COUNT,
) -> int:
    """When a failure pattern repeats ≥ min_count, auto-draft a skill proposal.

    The draft is written as a ledger type=idea entry tagged 'skill-proposal'
    so SessionStart surfaces it. This does NOT register the skill — user must
    explicitly confirm via apply_proposal() (see scripts/lib/a_loop_skill.py).

    Idempotent: if a skill-proposal for this pattern already exists, skip.

    Returns count of new proposals drafted.
    """
    patterns = count_failure_patterns(ledger_path, min_count=min_count)
    if not patterns:
        return 0
    ledger = memory_ledger.MemoryLedger(ledger_path)
    # Check existing skill-proposal ideas for idempotency
    existing_entries = ledger._load_all()
    existing_proposal_tags = set()
    for e in existing_entries:
        if e.get("type") == "idea" and "skill-proposal" in e.get("tags", []):
            for t in e.get("tags", []):
                if t.startswith("proposal:"):
                    existing_proposal_tags.add(t.lower())

    drafted = 0
    for p in patterns:
        tag = p["tag"]
        proposal_marker = f"proposal:guard-{tag.lower().replace(' ', '-')}"
        if proposal_marker in existing_proposal_tags:
            continue
        # Use a_loop_skill.propose_skill_for_pattern to build the draft
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
            import a_loop_skill
            proposal = a_loop_skill.propose_skill_for_pattern(
                tag=tag,
                failure_count=p["count"],
                sample_summaries=p["sample_summaries"],
            )
        except Exception:
            # Fallback if a_loop_skill not importable
            proposal = {
                "name": f"guard-{tag.lower().replace(' ', '-')}",
                "description": f"Guard for {tag} failures ({p['count']}x)",
            }
        # Write as idea entry tagged skill-proposal
        summary = (
            f"SKILL PROPOSAL: {proposal['name']} — {proposal.get('description', '')[:80]} "
            f"(failure pattern '{tag}' seen {p['count']}x). "
            f"Confirm via /A-Loop Phase 4 or apply_proposal()."
        )
        ledger.append(
            session_id="a-loop-distill",
            type="idea",
            summary=summary,
            tags=[proposal_marker, "skill-proposal", "a-loop", tag.lower()],
        )
        drafted += 1
    return drafted


def main() -> int:
    """Hook entry point. Exits 0 always (never blocks).

    Runs both:
      1. propose_ideas — distill ideas from failure patterns
      2. auto_propose_skill — draft skill proposals for repeated patterns
    """
    if os.environ.get("HOOK_SKIP") == "a_loop_distill":
        return 0
    try:
        n_ideas = propose_ideas(DEFAULT_LEDGER_PATH)
        n_proposals = auto_propose_skill(DEFAULT_LEDGER_PATH)
        if n_ideas > 0 or n_proposals > 0:
            sys.stderr.write(
                f"[a-loop-distill] {n_ideas} idea(s) + {n_proposals} skill proposal(s) "
                f"from repeated failure patterns\n"
            )
    except Exception as e:
        sys.stderr.write(f"[a-loop-distill] error: {e}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
