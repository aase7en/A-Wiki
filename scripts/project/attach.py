#!/usr/bin/env python3
"""awiki attach <project-root> — create the thin A-Wiki project adapter.

Phase 4 kernel contract (§control-plane-vs-project): projects ATTACH to
A-Wiki; A-Wiki is never copied/symlinked/submoduled into the project.

Behavior (idempotent + non-destructive):
  - creates .awiki/project.yaml ONLY if absent (existing policy untouched)
  - creates .awiki/context.md stub ONLY if absent
  - creates .awiki/state/ (+ .gitkeep) ONLY if absent
  - AGENTS.md: creates a minimal adapter file if absent; if present, appends
    ONE clearly-marked adapter section (marker below) preserving every
    existing byte — never rewrites, never appends twice.
No Git operations, no symlinks, no A-Wiki content copies. Cross-platform.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

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

PROJECT_YAML_TEMPLATE = """\
schema: awiki-project/v1
id: {id}
# repository: {{url: https://github.com/example/{id}}}   # stable identity — fill in
domains: [{domains}]
skills:
  auto: [a-router]
integrations:
  allowed: []          # ids from A-Wiki config/integrations.yaml
memory:
  scopes: {{global: true, project: true, session: true, private: false}}
privacy:
  project_private: true
code_context:
  enabled: false       # ProjectCodeContextProvider policy only (no runtime)
  preferred: []
  cache_policy: local-regenerable
  global_memory_promotion: false
resources: []          # project-relative adapter files (validated to exist)
"""

CONTEXT_MD_TEMPLATE = """\
# Project Context — {id}

Project-owned context for the A-Wiki adapter. Durable project decisions,
pointers, and constraints live here (NOT implementation detail — that stays
in the project repo). See .awiki/project.yaml for policy.
"""


def _slug(name: str) -> str:
    slug = re.sub(r"[^a-z0-9-]+", "-", name.lower()).strip("-")
    return (slug or "project")[:64]


def attach(project_root: Path, project_id: str, domains: list[str]) -> dict:
    report = {"created": [], "preserved": [], "appended_agents_section": False}
    aw = project_root / ".awiki"

    # ── .awiki/project.yaml (never overwrite) ──
    yml = aw / "project.yaml"
    if yml.is_file():
        report["preserved"].append(".awiki/project.yaml")
    else:
        aw.mkdir(parents=True, exist_ok=True)
        yml.write_text(
            PROJECT_YAML_TEMPLATE.format(
                id=project_id,
                domains=", ".join(sorted(dict.fromkeys(domains))) or "general",
            ),
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
    for item in report["created"]:
        print(f"created  : {item}")
    for item in report["preserved"]:
        print(f"preserved: {item}")
    if report["appended_agents_section"]:
        print(f"appended : AGENTS.md adapter section (marker: {AGENTS_MARKER})")
    print(f"attached : {project_id} (idempotent — rerun anytime)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
