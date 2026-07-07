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

STRATEGIC_LANES = [
    {
        "id": "design-web",
        "goal": "Production-grade website, dashboard, and visual design workflow.",
        "route": "frontend-design -> webapp-testing -> Canva only for export/brand assets.",
        "verify": "Playwright/browser visual smoke plus build/type checks for the target app.",
        "safety": "No private analytics or brand secrets in tracked repo; generated review HTML stays in exports/html/.",
    },
    {
        "id": "game-lightweight-highend",
        "goal": "High-end-feeling but lightweight web games such as Sunday Invest Moon.",
        "route": "Phaser/Vite/TypeScript -> PixelLab manifest -> asset report -> bootstrap/copy.",
        "verify": "Asset pack report, logic tests, typecheck/build, and FPS/blank-canvas smoke.",
        "safety": "Binary/raw assets stay outside tracked wiki unless intentionally curated; secrets come from drive/.",
    },
    {
        "id": "revenue-engine",
        "goal": "Turn wiki knowledge into public-safe content, product ideas, and validation loops.",
        "route": "local wiki search -> Creator Layer -> verified market research -> content/product package.",
        "verify": "Source table, privacy check, and trend/latest verification before public claims.",
        "safety": "Voice, analytics, drafts, customer data, and private evidence stay in drive/personal/creator/.",
    },
    {
        "id": "premium-auto-trading",
        "goal": "Premium trading research and bot operations with strict paper/read-only/live separation.",
        "route": "paper trading first -> read-only portfolio feed -> live backend only after security review.",
        "verify": "Bot Trading Iron Law, feed boundary scan, risk guard tests, audit log checks.",
        "safety": "No client-side secrets, no browser exchange calls, no live execution without backend kill switch.",
    },
]

CAPABILITY_UPGRADE_MATRIX = [
    {
        "area": "Second brain",
        "current": "Wiki pages, graph, skills, hooks, and generated context already exist.",
        "upgrade": "Four strategic capability lanes with clear routing and safety gates.",
        "verify": "python3 scripts/wiki/build-capability-map.py --out -",
    },
    {
        "area": "Knowledge graph",
        "current": "Graph reports broken links and orphans, but the work is not lane-prioritized.",
        "upgrade": "Graph hygiene baseline and P0 cleanup queue by source domain.",
        "verify": "python3 scripts/wiki/query-graph.py --broken && python3 scripts/wiki/query-graph.py --orphans",
    },
    {
        "area": "Website design",
        "current": "Frontend/design and web testing skills are available.",
        "upgrade": "Design QA route combines frontend skill, browser/Playwright verification, and Canva export only when useful.",
        "verify": "Run target app build plus Playwright visual smoke.",
    },
    {
        "area": "High-end lightweight game",
        "current": "Phaser, Sunday Invest Moon, PixelLab, and manifest scripts exist.",
        "upgrade": "Game lane locks performance budget, asset manifest validation, and no-secret runtime rules.",
        "verify": "python3 scripts/game/report_phaser_asset_pack.py game-assets/manifests --root . --check-files",
    },
    {
        "area": "Revenue engine",
        "current": "Creator Layer and Thai/social skills exist.",
        "upgrade": "Revenue work flows from wiki evidence to product/content idea to validation before publishing.",
        "verify": "python3 scripts/check-privacy.py plus source/date/link review for latest claims.",
    },
    {
        "area": "Premium auto trading",
        "current": "Freqtrade notes, read-only feed contract, and trading iron law exist.",
        "upgrade": "Three-tier trading model: paper, read-only, live backend with risk/security approval.",
        "verify": "Trading-specific tests in product repo plus A-Wiki privacy/preflight checks.",
    },
]

MCP_ALLOWLIST = [
    {
        "server": "awiki",
        "status": "Keep",
        "use": "Local wiki search, semantic search, page reads, and graph neighbors.",
        "gate": "Read-mostly; auto-approved tools must stay scoped to A-Wiki knowledge.",
    },
    {
        "server": "filesystem",
        "status": "Keep scoped",
        "use": "Repo-local file access for agents that support MCP.",
        "gate": "Restrict roots to the repo; never expose drive/, raw/, secrets, or home-wide paths.",
    },
    {
        "server": "github",
        "status": "Keep when needed",
        "use": "Repository, issue, and PR inspection where connector/CLI is not enough.",
        "gate": "Prefer read-only for review; A-Wiki workflow still commits directly to main.",
    },
    {
        "server": "supabase",
        "status": "Allow after task need",
        "use": "Database/project work for web apps that actually use Supabase.",
        "gate": "Use least privilege and never store project tokens in tracked files.",
    },
    {
        "server": "trading/exchange",
        "status": "Reject by default",
        "use": "No direct exchange/broker MCP inside A-Wiki agent context.",
        "gate": "Only a reviewed backend may hold trading authority; clients and wiki agents stay read-only/paper.",
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
    stats: dict[str, int] = {}
    for section in ("entities", "concepts", "synthesis", "sources"):
        base = root / "wiki" / section
        stats[section] = len(list(base.rglob("*.md"))) if base.exists() else 0
    stats["total_pages"] = sum(stats.values())
    return stats


def classify_graph_domain(path: str) -> str:
    parts = Path(path).parts
    if len(parts) >= 4 and parts[0] == "wiki" and parts[1] in {"entities", "concepts"}:
        return parts[2]
    if len(parts) >= 3 and parts[0] == "wiki" and parts[1] in {"synthesis", "sources", "context"}:
        return parts[1]
    if parts and parts[0] == "wiki":
        return "wiki-other"
    return "repo-root"


def read_graph_hygiene(root: Path) -> dict[str, Any]:
    graph_path = root / ".wiki-graph.json"
    fallback = {
        "nodes": 0,
        "edges": 0,
        "broken_links": 0,
        "orphans": 0,
        "broken_by_domain": {},
        "orphan_by_domain": {},
        "orphan_samples": [],
        "status": "missing",
    }
    if not graph_path.exists():
        return fallback
    try:
        graph = json.loads(graph_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        fallback["status"] = "invalid-json"
        return fallback
    stats = graph.get("stats") or {}
    broken_by_domain: dict[str, int] = {}
    for edge in graph.get("edges") or []:
        if not edge.get("broken"):
            continue
        domain = classify_graph_domain(str(edge.get("from") or ""))
        broken_by_domain[domain] = broken_by_domain.get(domain, 0) + 1
    orphan_list = list(stats.get("orphans_list") or [])
    orphan_by_domain = {
        str(domain): int(count)
        for domain, count in (stats.get("orphan_by_domain") or {}).items()
        if int(count)
    }
    if not orphan_by_domain:
        for path in orphan_list:
            domain = classify_graph_domain(str(path))
            orphan_by_domain[domain] = orphan_by_domain.get(domain, 0) + 1
    return {
        "nodes": int(stats.get("nodes") or 0),
        "edges": int(stats.get("edges") or 0),
        "broken_links": int(stats.get("broken_links") or 0),
        "orphans": int(stats.get("orphans") or 0),
        "broken_by_domain": dict(sorted(broken_by_domain.items(), key=lambda item: (-item[1], item[0]))),
        "orphan_by_domain": dict(sorted(orphan_by_domain.items(), key=lambda item: (-item[1], item[0]))),
        "orphan_samples": orphan_list[:10],
        "status": "ok",
    }


def build_capability_map(root: Path = REPO_ROOT) -> dict[str, Any]:
    root = root.resolve()
    skills = discover_owned_skills(root)
    capabilities = discover_script_capabilities(root)
    protocols = discover_protocols(root)
    render_surfaces = discover_render_surfaces(root)
    wiki_stats = parse_wiki_stats(root)
    graph_hygiene = read_graph_hygiene(root)
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
        "strategic_lanes": STRATEGIC_LANES,
        "upgrade_matrix": CAPABILITY_UPGRADE_MATRIX,
        "graph_hygiene": graph_hygiene,
        "mcp_allowlist": MCP_ALLOWLIST,
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
            "## Strategic Capability Lanes",
            "",
            "| Lane | Goal | Route | Verify | Safety gate |",
            "|---|---|---|---|---|",
        ]
    )
    for lane in data.get("strategic_lanes") or []:
        lines.append(
            "| `{id}` | {goal} | {route} | {verify} | {safety} |".format(
                id=md_escape(lane["id"]),
                goal=md_escape(lane["goal"]),
                route=md_escape(lane["route"]),
                verify=md_escape(lane["verify"]),
                safety=md_escape(lane["safety"]),
            )
        )

    lines.extend(
        [
            "",
            "## Capability Upgrade Matrix",
            "",
            "| Area | Current capability | Upgraded capability | Verification |",
            "|---|---|---|---|",
        ]
    )
    for item in data.get("upgrade_matrix") or []:
        lines.append(
            "| {area} | {current} | {upgrade} | `{verify}` |".format(
                area=md_escape(item["area"]),
                current=md_escape(item["current"]),
                upgrade=md_escape(item["upgrade"]),
                verify=md_escape(item["verify"]),
            )
        )

    # NOTE: Knowledge Graph Hygiene (Nodes/Edges/Broken/Orphans) was removed
    # from this markdown catalog because those live counters shift every
    # gen-index run, making gen-index.py --check non-deterministic. The data
    # is still collected in data["graph_hygiene"] and rendered to a separate
    # wiki/context/graph-hygiene.md by scripts/gen-index.py (excluded from
    # the --check gate). See ADR on separating stable catalog from volatile
    # live metrics.

    lines.extend(
        [
            "## MCP Allowlist",
            "",
            "| Server | Status | Use | Gate |",
            "|---|---|---|---|",
        ]
    )
    for item in data.get("mcp_allowlist") or []:
        lines.append(
            "| `{server}` | {status} | {use} | {gate} |".format(
                server=md_escape(item["server"]),
                status=md_escape(item["status"]),
                use=md_escape(item["use"]),
                gate=md_escape(item["gate"]),
            )
        )

    lines.extend(
        [
            "",
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
