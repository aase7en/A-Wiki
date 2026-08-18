#!/usr/bin/env python3
"""awiki attach <project-root> — create the thin A-Wiki project adapter.

Phase 4 kernel contract (§control-plane-vs-project): projects ATTACH to
A-Wiki; A-Wiki is never copied/symlinked/submoduled into the project.

Behavior (idempotent + non-destructive + project-contained):
  - REFUSES to run if any adapter path (AGENTS.md, .awiki, project.yaml,
    context.md, state) is a symlink — never follows a link outside the
    project, never touches its target (R-P4-002)
  - creates .awiki/project.yaml ONLY if absent (existing policy untouched),
    generated via yaml.safe_dump from a mapping (never string interpolation,
    R-P4-004) including the required privacy/trust/memory policy (R-P4-003)
  - creates .awiki/context.md stub ONLY if absent
  - creates .awiki/state/ (+ .gitkeep) ONLY if absent
  - AGENTS.md: creates a minimal adapter file if absent; if present, appends
    ONE clearly-marked adapter section (marker below) preserving every
    existing byte — never rewrites, never appends twice
  - self-validates the result with the offline validator and FAILS (exit 1)
    if the generated adapter is invalid (R-P4-004)
No Git operations, no symlinks, no A-Wiki content copies. Cross-platform.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate as pv  # noqa: E402 -- self-validation after attach

AGENTS_MARKER = "awiki-project-adapter"
ADAPTER_SECTION = f"""

<!-- {AGENTS_MARKER} v1 — appended by `awiki attach`; safe to move, safe to keep, do not edit inside the markers -->
## A-Wiki Project Adapter

This project is attached to an A-Wiki brain (control plane). Adapter state
lives in `.awiki/` (project.yaml policy + context.md + state/). A-Wiki is
NOT copied into this repo — see `.awiki/project.yaml` and the A-Wiki kernel
contract for boundaries. Removing this section detaches cleanly.
<!-- /{AGENTS_MARKER} -->
"""

ADAPTER_PATHS = ["AGENTS.md", ".awiki", ".awiki/project.yaml",
                 ".awiki/context.md", ".awiki/state"]


def _slug(name: str) -> str:
    slug = re.sub(r"[^a-z0-9-]+", "-", name.lower()).strip("-")
    return (slug or "project")[:64]


def _check_no_unsafe_symlinks(project_root: Path) -> list[str]:
    """R-P4-002: refuse adapter paths that are symlinks (targets may live
    outside the project — following them writes through the boundary)."""
    problems = []
    for rel in ADAPTER_PATHS:
        p = project_root / rel
        if p.is_symlink():
            problems.append(f"refusing: {rel} is a symlink (adapter paths must be project-contained)")
    return problems


def _project_yaml_mapping(project_id: str, domains: list[str]) -> dict:
    """Stable policy mapping (R-P4-003/004) — serialized with safe_dump."""
    return {
        "schema": "awiki-project/v1",
        "id": project_id,
        "domains": sorted(dict.fromkeys(domains)) or ["general"],
        "skills": {"auto": ["a-router"]},
        "integrations": {"allowed": []},
        "memory": {"scopes": {"global": True, "project": True,
                              "session": True, "private": False}},
        "privacy": {"project_private": True},
        "trust": {"deep_enrichment": "project-policy", "private_context": False},
        "code_context": {"enabled": False, "preferred": [],
                         "cache_policy": "local-regenerable",
                         "global_memory_promotion": False},
        "resources": [],
    }


CONTEXT_MD_TEMPLATE = """\
# Project Context — {id}

Project-owned context for the A-Wiki adapter. Durable project decisions,
pointers, and constraints live here (NOT implementation detail — that stays
in the project repo). See .awiki/project.yaml for policy.
"""


def attach(project_root: Path, project_id: str, domains: list[str]) -> dict:
    report = {"created": [], "preserved": [], "appended_agents_section": False}
    aw = project_root / ".awiki"

    # ── R-P4-002: symlink refusal BEFORE any write ──
    unsafe = _check_no_unsafe_symlinks(project_root)
    if unsafe:
        report["refused"] = unsafe
        return report

    # ── .awiki/project.yaml (never overwrite; safe_dump, R-P4-004) ──
    yml = aw / "project.yaml"
    if yml.is_file():
        report["preserved"].append(".awiki/project.yaml")
    else:
        aw.mkdir(parents=True, exist_ok=True)
        mapping = _project_yaml_mapping(project_id, domains)
        yml.write_text(
            yaml.safe_dump(mapping, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        report["created"].append(".awiki/project.yaml")

    # ── .awiki/context.md (never overwrite) ──
    ctx = aw / "context.md"
    if ctx.is_file():
        report["preserved"].append(".awiki/context.md")
    else:
        aw.mkdir(parents=True, exist_ok=True)
        ctx.write_text(CONTEXT_MD_TEMPLATE.format(id=project_id), encoding="utf-8")
        report["created"].append(".awiki/context.md")

    # ── .awiki/state/ (runtime dir, minimal) ──
    state = aw / "state"
    if state.is_dir():
        report["preserved"].append(".awiki/state/")
    else:
        state.mkdir(parents=True, exist_ok=True)
        (state / ".gitkeep").write_text("", encoding="utf-8")
        report["created"].append(".awiki/state/")

    # ── AGENTS.md (create or marker-append; never rewrite) ──
    agents = project_root / "AGENTS.md"
    if agents.is_file():
        text = agents.read_text(encoding="utf-8")
        if AGENTS_MARKER in text:
            report["preserved"].append("AGENTS.md (adapter section already present)")
        else:
            if not text.endswith("\n"):
                text += "\n"
            agents.write_text(text + ADAPTER_SECTION, encoding="utf-8")
            report["appended_agents_section"] = True
    else:
        agents.write_text(f"# {project_id}\n" + ADAPTER_SECTION.lstrip("\n"), encoding="utf-8")
        report["created"].append("AGENTS.md")

    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Attach a project to A-Wiki (thin adapter)")
    parser.add_argument("project_root", nargs="?", type=Path, default=Path("."))
    parser.add_argument("--id", default=None, help="project id (default: dir-name slug)")
    parser.add_argument("--domain", action="append", default=[], help="project domain (repeatable)")
    args = parser.parse_args(argv)

    root = args.project_root.resolve()
    if not root.is_dir():
        print(f"attach: project root is not a directory: {root}", file=sys.stderr)
        return 2

    project_id = _slug(args.id or root.name)
    report = attach(root, project_id, args.domain)

    if "refused" in report:
        for problem in report["refused"]:
            print(f"attach: {problem}", file=sys.stderr)
        return 2

    for item in report["created"]:
        print(f"created  : {item}")
    for item in report["preserved"]:
        print(f"preserved: {item}")
    if report["appended_agents_section"]:
        print(f"appended : AGENTS.md adapter section (marker: {AGENTS_MARKER})")

    # ── R-P4-004: never report success on an invalid generated adapter ──
    result = pv.validate(root)
    if result.exit_code() != 0:
        for e in result.errors:
            print(f"attach: generated adapter is INVALID — {e}", file=sys.stderr)
        return 1

    print(f"attached : {project_id} (idempotent — rerun anytime)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
