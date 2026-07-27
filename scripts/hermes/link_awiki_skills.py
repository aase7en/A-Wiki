#!/usr/bin/env python3
"""
link_awiki_skills.py — expose ``skills/awiki/*`` to Hermes on the Pi5.
=====================================================================

This is the **first real consumer** of ``hermes.skills.json``.  Chunk A shipped
that manifest and Chunk C3' copied it onto the device, but a repo-wide grep
found nothing that ever read it — ``awiki-init-pi5.sh`` hard-coded three skill
directories (``engineering-lifecycle``, ``engineering``, ``mattpocock``) and
never touched ``skills/awiki/``, which is where the whole A-Suite lives.  The
net effect: every A-* skill was invisible to Hermes.

Why linking is enough
---------------------
The Pi5 gateway uses **Skills-as-Commands** — every directory under
``/opt/data/skills/`` is auto-exposed as ``/<dirname>`` on Telegram (see
docs/architecture/hermes-cross-agent-handoff.md §"Skills-as-Commands", and
chunk hermes-e which proved it with ``/wiki /search /review /spec /plan /build
/ship``).  A-Suite skills are prompt dispatchers, not script-backed commands,
so unlike those seven they need **no** ``telegram-commands.json`` entry: the
SKILL.md body is the payload the model reads.  Linking the directory is the
whole integration.

Scope
-----
Only manifest entries whose ``path`` starts with ``skills/awiki/`` are linked
here.  Lifecycle / native / mattpocock skills already have their own steps in
``awiki-init-pi5.sh``; re-linking them would create duplicate command names.

Design (mirrors scripts/hermes/persona-orchestrator.py and pi5-brain-sync.py)
-----------------------------------------------------------------------------
- **Map, do not execute by default** — ``--apply`` is required to touch the
  filesystem; the default prints the plan as JSON and is CI-safe.
- **Pure planner** — ``build_link_plan`` does no I/O beyond an ``is_dir`` check,
  so tests drive it directly.
- **Never create a broken link** — an entry whose source directory is missing is
  skipped.  The device has carried broken symlinks before (the
  ``lifecycle/idea-refine`` orphan found during C3'); don't add more.
- **Idempotent** — re-running replaces an existing link in place, so the init
  script is safe to re-run after every sync.

Usage
-----
::

    # Dry-run (default): print the plan, touch nothing.
    python3 scripts/hermes/link_awiki_skills.py

    # Link for real, into the Hermes skill root.
    python3 scripts/hermes/link_awiki_skills.py --apply \
        --skills-root ~/.hermes/skills

    # On the container, where Hermes actually scans:
    python3 scripts/hermes/link_awiki_skills.py --apply \
        --skills-root /opt/data/skills

Exit codes
----------
- 0 = success (plan printed, or links applied)
- 1 = manifest missing/unreadable

See: scripts/skills_registry/generators/gen_hermes.py (produces the manifest)
     docs/architecture/hermes-cross-agent-handoff.md
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Sequence

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = REPO_ROOT / "scripts" / "skills_registry" / "generated" / "hermes.skills.json"
DEFAULT_SKILLS_ROOT = Path.home() / ".hermes" / "skills"

# Manifest entries under this prefix become Telegram commands.
AWIKI_PREFIX = "skills/awiki/"

# Namespace inside the Hermes skill root.  Matches the layout chunk hermes-e
# proved on the device (/opt/data/skills/awiki/<name>), so there is one
# convention rather than two.
LINK_NAMESPACE = "awiki"


def _utf8_streams() -> None:
    """Force UTF-8 on stdout/stderr.

    Skill names are ASCII but the plan is printed next to Thai log lines on a
    cp874 console; every CLI in this repo reconfigures its streams for the same
    reason (see scripts/hooks/check_compaction_suggest.py).
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):  # pragma: no cover - exotic stream
            pass


def load_manifest(path: Path) -> dict[str, Any]:
    """Read hermes.skills.json.  Raises FileNotFoundError / JSONDecodeError."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_link_plan(
    manifest: dict[str, Any],
    repo_root: Path,
    skills_root: Path,
    prefix: str = AWIKI_PREFIX,
) -> list[dict[str, Any]]:
    """Return the ordered list of ``{name, source, link}`` entries to create.

    ``source`` is the skill DIRECTORY (the manifest stores the SKILL.md path).
    Entries outside *prefix*, and entries whose directory does not exist, are
    dropped.  Output is sorted by name so the printed plan is diffable.
    """
    plan: list[dict[str, Any]] = []
    for skill in manifest.get("skills", []):
        rel = skill.get("path") or ""
        if not rel.startswith(prefix):
            continue
        source = repo_root / Path(rel).parent
        if not source.is_dir():
            continue
        name = skill.get("name") or source.name
        plan.append({
            "name": name,
            "source": source,
            "link": skills_root / LINK_NAMESPACE / name,
        })
    plan.sort(key=lambda e: e["name"])
    return plan


def _make_link(source: Path, link: Path) -> None:
    """Point *link* at *source*, replacing whatever is there.

    Symlink first (what the Pi5 uses).  Windows refuses ``os.symlink`` without
    Developer Mode or admin, so fall back to a directory junction there — the
    linker is Pi5-only in practice, but the tests run on the maintainer's
    Windows box and a plan that cannot be exercised is a plan nobody trusts.
    """
    link.parent.mkdir(parents=True, exist_ok=True)
    if link.is_symlink() or link.exists():
        if link.is_dir() and not link.is_symlink():
            os.rmdir(link)  # junction or stray dir; refuses if non-empty by design
        else:
            link.unlink()
    try:
        os.symlink(source, link, target_is_directory=True)
    except (OSError, NotImplementedError):
        if os.name != "nt":
            raise
        import _winapi  # noqa: PLC0415 - Windows-only fallback
        _winapi.CreateJunction(str(source), str(link))


def apply_plan(plan: Sequence[dict[str, Any]]) -> int:
    """Create every link in *plan*.  Returns the count.  Idempotent."""
    for entry in plan:
        _make_link(entry["source"], entry["link"])
    return len(plan)


def main(argv: Sequence[str] | None = None) -> int:
    _utf8_streams()
    ap = argparse.ArgumentParser(
        description="Link skills/awiki/* into the Hermes skill root (Pi5).",
    )
    ap.add_argument("--manifest", default=str(DEFAULT_MANIFEST),
                    help="Path to hermes.skills.json.")
    ap.add_argument("--repo-root", default=str(REPO_ROOT),
                    help="A-Wiki checkout the links should point into.")
    ap.add_argument("--skills-root", default=str(DEFAULT_SKILLS_ROOT),
                    help="Hermes skill root (~/.hermes/skills, or /opt/data/skills).")
    ap.add_argument("--apply", action="store_true",
                    help="Create the links (default: dry-run, print the plan).")
    a = ap.parse_args(argv)

    manifest_path = Path(a.manifest)
    try:
        manifest = load_manifest(manifest_path)
    except FileNotFoundError:
        print(f"manifest not found: {manifest_path}", file=sys.stderr)
        print("run: python scripts/regen-skill-surfaces.py", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"manifest is not valid JSON ({manifest_path}): {exc}", file=sys.stderr)
        return 1

    plan = build_link_plan(manifest, Path(a.repo_root), Path(a.skills_root))

    if not a.apply:
        print(json.dumps(
            {"dry_run": True,
             "count": len(plan),
             "links": [{"name": e["name"],
                        "source": str(e["source"]),
                        "link": str(e["link"])} for e in plan]},
            indent=2, ensure_ascii=False))
        return 0

    n = apply_plan(plan)
    print(f"linked {n} skills/awiki skill(s) into {Path(a.skills_root) / LINK_NAMESPACE}")
    for entry in plan:
        print(f"  /{entry['name']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
