#!/usr/bin/env python3
"""Build a lightweight map of A-Wiki's reusable capabilities."""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]

OWNED_SKILL_ROOTS = [
    "skills/claude-code",
    "skills/claude-thai",
    "skills/domain",
    "skills/delegation",
    "agent-skills/engineering",
    "agent-skills/productivity",
]
SKIP_PARTS = {"_upstream", "ecosystem", "__pycache__"}

SCRIPT_CAPABILITIES = [
    {
        "capability": "Local Search",
        "path": "scripts/wiki/search-wiki.py",
        "surface": "CLI",
        "command": 'python3 scripts/wiki/search-wiki.py "query"',
        "use_when": "Find existing wiki knowledge before spending model tokens.",
    },
    {
        "capability": "Knowledge Graph Query",
        "path": "scripts/wiki/query-graph.py",
        "surface": "CLI",
        "command": "python3 scripts/wiki/query-graph.py --hubs",
        "use_when": "Inspect hubs, neighbors, and cross-page relationships.",
    },
    {
        "capability": "Wiki Index Regeneration",
        "path": "scripts/gen-index.py",
        "surface": "CLI",
        "command": "python3 scripts/gen-index.py --check",
        "use_when": "Validate wiki structure and generated context after edits.",
    },
    {
        "capability": "Agent Preflight",
        "path": "scripts/agent-preflight.py",
        "surface": "CLI",
        "command": "python3 scripts/agent-preflight.py",
        "use_when": "Check branch, sync, drive/raw links, hooks, and platform drift.",
    },
    {
        "capability": "Skill Quality Reporting",
        "path": "scripts/skill-quality-report.py",
        "surface": "CLI/HTML",
        "command": "python3 scripts/skill-quality-report.py --fail-on-warn",
        "use_when": "Audit owned skills for frontmatter, eval coverage, length, and safety issues.",
    },
    {
        "capability": "Owned Skill Eval",
        "path": "scripts/skillopt/awiki_eval.py",
        "surface": "CLI",
        "command": "python3 scripts/skillopt/awiki_eval.py --suite evals/awiki/owned-skill-coverage.json --threshold 1.0",
        "use_when": "Confirm owned skill smoke coverage still recognizes required phrases.",
    },
    {
        "capability": "Model Roster Refresh",
        "path": "scripts/update-model-roster.sh",
        "surface": "CLI",
        "command": "bash scripts/update-model-roster.sh",
        "use_when": "Refresh free/cheap model availability for delegation decisions.",
    },
    {
        "capability": "Swarm Delegation",
        "path": "scripts/swarm/delegate.sh",
        "surface": "CLI",
        "command": 'bash scripts/swarm/delegate.sh architect "question"',
        "use_when": "Send lower-risk planning/search work to free or cheap models.",
    },
    {
        "capability": "NotebookLM Export",
        "path": "scripts/export-to-notebooklm.sh",
        "surface": "CLI",
        "command": "bash scripts/export-to-notebooklm.sh",
        "use_when": "Prepare notebook bundles from curated wiki content.",
    },
    {
        "capability": "Pharmacy Lookup",
        "path": "scripts/pharmacy_lookup.py",
        "surface": "CLI/HTML",
        "command": 'python3 scripts/pharmacy_lookup.py "drug name"',
        "use_when": "Search local pharmacy DB and verify order text.",
    },
    {
        "capability": "Delivery Reconciliation",
        "path": "scripts/compare_delivery.py",
        "surface": "CLI/HTML",
        "command": "python3 scripts/compare_delivery.py --json --delivery <file>",
        "use_when": "Compare ordered vs received pharmacy items.",
    },
    {
        "capability": "Asset Pack Reporting",
        "path": "scripts/game/report_phaser_asset_pack.py",
        "surface": "CLI",
        "command": "python3 scripts/game/report_phaser_asset_pack.py game-assets/manifests --root . --check-files",
        "use_when": "Inspect PixelLab/Phaser asset-pack readiness before bootstrap or project copy.",
    },
    {
        "capability": "Phaser Asset Bootstrap",
        "path": "scripts/game/bootstrap_phaser_asset_pack.py",
        "surface": "CLI",
        "command": "python3 scripts/game/bootstrap_phaser_asset_pack.py game-assets/manifests --out-dir game-assets/generated --root .",
        "use_when": "Generate Phaser JSON, loader TS, scene stub, and README from manifests.",
    },
]


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    raw = text[4:end]
    body = text[end + 4 :].lstrip("\n")
    meta: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip().strip('"').strip("'")
    return meta, body


def discover_owned_skills(root: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for skill_root in OWNED_SKILL_ROOTS:
        base = root / skill_root
        if not base.exists():
            continue
        for path in sorted(base.rglob("SKILL.md")):
            if any(part in SKIP_PARTS for part in path.relative_to(root).parts):
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            meta, _body = parse_frontmatter(text)
            rows.append(
                {
                    "name": meta.get("name") or path.parent.name,
                    "description": meta.get("description") or "(no description)",
                    "path": rel(path, root),
                    "family": skill_root,
                }
            )
    return sorted(rows, key=lambda item: (item["family"], item["name"]))


def discover_script_capabilities(root: Path) -> list[dict[str, str]]:
    return [item for item in SCRIPT_CAPABILITIES if (root / item["path"]).exists()]


def discover_protocols(root: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for folder in ("docs/protocols", "docs/runbooks"):
        base = root / folder
        if not base.exists():
            continue
        for path in sorted(base.glob("*.md")):
            title = path.stem.replace("-", " ")
            try:
                first_h1 = next(
                    line.lstrip("# ").strip()
                    for line in path.read_text(encoding="utf-8", errors="replace").splitlines()
                    if line.startswith("# ")
                )
                title = first_h1 or title
            except StopIteration:
                pass
            rows.append({"title": title, "path": rel(path, root), "family": folder})
    return rows


def discover_render_surfaces(root: Path) -> list[dict[str, str]]:
    registry = root / "skills" / "render-html" / "registry.json"
    if not registry.exists():
        return []
    try:
        data = json.loads(registry.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    rows: list[dict[str, str]] = []
    for name, item in sorted((data.get("surfaces") or {}).items()):
        rows.append(
            {
                "name": name,
                "title": str(item.get("title") or name),
                "description": str(item.get("description") or ""),
                "data_source": str(item.get("data_source") or ""),
            }
        )
    return rows


def parse_wiki_stats(root: Path) -> dict[str, int]:
    overview = root / "wiki" / "context" / "wiki-overview.md"
    if not overview.exists():
        return {}
    text = overview.read_text(encoding="utf-8", errors="replace")
    stats: dict[str, int] = {}
    for key in ("ENTITIES", "CONCEPTS", "SYNTHESIS", "SOURCES"):
        match = re.search(rf"\|\s*{key}\s*\|\s*(\d+)\s*\|", text)
        if match:
            stats[key.lower()] = int(match.group(1))
    match = re.search(r"\|\s*\*\*Total\*\*\s*\|\s*\*\*(\d+)\s+pages\*\*\s*\|", text)
    if match:
        stats["total_pages"] = int(match.group(1))
    return stats


def build_capability_map(root: Path = REPO_ROOT) -> dict[str, Any]:
    root = root.resolve()
    skills = discover_owned_skills(root)
    capabilities = discover_script_capabilities(root)
    protocols = discover_protocols(root)
    render_surfaces = discover_render_surfaces(root)
    wiki_stats = parse_wiki_stats(root)
    summary = {
        "owned_skill_count": len(skills),
        "script_count": len(capabilities),
        "protocol_count": len(protocols),
        "render_surface_count": len(render_surfaces),
        "wiki_page_count": wiki_stats.get("total_pages", 0),
    }
    return {
        "generated": date.today().isoformat(),
        "summary": summary,
        "wiki_stats": wiki_stats,
        "capabilities": capabilities,
        "skills": skills,
        "protocols": protocols,
        "render_surfaces": render_surfaces,
    }


def md_escape(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def clip(text: str, limit: int = 150) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def format_markdown(data: dict[str, Any]) -> str:
    summary = data["summary"]
    wiki_stats = data.get("wiki_stats") or {}
    lines = [
        "# Wiki Capability Map",
        "",
        "> Generated by `scripts/wiki/build-capability-map.py`.",
        f"> Last updated: {data['generated']}",
        "",
        "## Summary",
        "",
        "| Area | Count |",
        "|---|---:|",
        f"| Wiki pages | {summary['wiki_page_count']} |",
        f"| Owned skills | {summary['owned_skill_count']} |",
        f"| Script capabilities | {summary['script_count']} |",
        f"| Protocols/runbooks | {summary['protocol_count']} |",
        f"| HTML surfaces | {summary['render_surface_count']} |",
        "",
    ]
    if wiki_stats:
        lines.extend(
            [
                "## Wiki Knowledge Surface",
                "",
                "| Type | Count |",
                "|---|---:|",
                f"| Entities | {wiki_stats.get('entities', 0)} |",
                f"| Concepts | {wiki_stats.get('concepts', 0)} |",
                f"| Synthesis | {wiki_stats.get('synthesis', 0)} |",
                f"| Sources | {wiki_stats.get('sources', 0)} |",
                "",
            ]
        )

    lines.extend(
        [
            "## Capability Routing",
            "",
            "| Capability | Surface | Command | Use when |",
            "|---|---|---|---|",
        ]
    )
    for item in data["capabilities"]:
        lines.append(
            "| {capability} | {surface} | `{command}` | {use_when} |".format(
                capability=md_escape(item["capability"]),
                surface=md_escape(item["surface"]),
                command=md_escape(item["command"]),
                use_when=md_escape(item["use_when"]),
            )
        )

    lines.extend(["", "## Owned Skills", "", "| Skill | Family | Use when | Path |", "|---|---|---|---|"])
    for skill in data["skills"]:
        lines.append(
            "| `{name}` | {family} | {description} | `{path}` |".format(
                name=md_escape(skill["name"]),
                family=md_escape(skill["family"]),
                description=md_escape(clip(skill["description"])),
                path=md_escape(skill["path"]),
            )
        )

    lines.extend(["", "## Render HTML Surfaces", "", "| Surface | Title | Use | Data source |", "|---|---|---|---|"])
    for surface in data["render_surfaces"]:
        lines.append(
            "| `{name}` | {title} | {description} | `{data_source}` |".format(
                name=md_escape(surface["name"]),
                title=md_escape(surface["title"]),
                description=md_escape(clip(surface["description"])),
                data_source=md_escape(surface["data_source"]),
            )
        )

    lines.extend(["", "## Protocols And Runbooks", "", "| Title | Family | Path |", "|---|---|---|"])
    for protocol in data["protocols"]:
        lines.append(
            "| {title} | {family} | `{path}` |".format(
                title=md_escape(protocol["title"]),
                family=md_escape(protocol["family"]),
                path=md_escape(protocol["path"]),
            )
        )

    lines.extend(
        [
            "",
            "## Operating Rule",
            "",
            "Start at local search and generated maps first, then use skills/scripts, then delegate to free or cheap models, and keep primary-agent reasoning for final validation and high-risk decisions.",
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build A-Wiki's reusable capability map.")
    parser.add_argument("--root", default=str(REPO_ROOT), help="Repository root.")
    parser.add_argument(
        "--out",
        default="wiki/context/wiki-capability-map.md",
        help="Markdown output path. Use '-' for stdout.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of Markdown.")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    data = build_capability_map(root)
    output = json.dumps(data, ensure_ascii=False, indent=2) if args.json else format_markdown(data)
    if args.out == "-":
        print(output, end="" if output.endswith("\n") else "\n")
        return 0
    out = Path(args.out)
    if not out.is_absolute():
        out = root / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(output, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
