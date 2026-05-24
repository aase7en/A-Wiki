#!/usr/bin/env python3
"""
gen-domain-indexes.py — Generate per-domain index pages at repo root.

Output files:
  - index-iot.md
  - index-env.md
  - index-ai-tools.md
  - index-pharmacy.md

Each index shows:
  - Stats (entity count, synthesis count, broken links, total edges)
  - All entities sorted by type/hub score
  - Cross-domain bridges (dependencies between domains)
  - Recent updates from journal (last 30 days)
  - Top domain hubs from knowledge graph

Usage:
    python3 scripts/gen-domain-indexes.py         # generate all 4
    python3 scripts/gen-domain-indexes.py --json  # also dump JSON counts
    python3 scripts/gen-domain-indexes.py --quiet # suppress print
"""
from __future__ import annotations
import argparse
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GRAPHBUILDER = REPO_ROOT / "scripts" / "build-wiki-graph.py"
GRAPH_PATH = REPO_ROOT / ".wiki-graph.json"
WIKI_DIR = REPO_ROOT / "wiki"
JOURNAL_DIR = REPO_ROOT / "journal" / "2026"

# Entity-to-domain mapping (path segment)
ENTITY_DIR_MAP = {
    "iot": "IoT & Hardware",
    "env": "Environmental Monitoring",
    "ai-tools": "AI Tools & LLMs",
    "pharmacy": "Pharmacy & Healthcare",
}

# Edge type display icons
TYPE_ICON = {
    "wikilink": "🔗",
    "mdlink": "📎",
    "depends": "⬇️",
    "extends": "➡️",
    "implements": "⚡",
}

H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)


def extract_title(text: str, fallback: str) -> str:
    m = H1_RE.search(text)
    return m.group(1).strip() if m else fallback


def load_graph() -> dict:
    if not GRAPH_PATH.exists():
        subprocess.run([sys.executable, str(GRAPHBUILDER), "--quiet"], check=True)
    return json.loads(GRAPH_PATH.read_text(encoding="utf-8"))


def get_domain_entity_paths(domain_key: str) -> list[str]:
    """Return all relative paths under wiki/entities/<domain>/"""
    d = WIKI_DIR / "entities" / domain_key
    if not d.is_dir():
        return []
    return sorted(
        p.relative_to(REPO_ROOT).as_posix()
        for p in d.rglob("*.md") if p.is_file()
    )


def get_domain_concept_paths(domain_key: str) -> list[str]:
    """Return paths under wiki/concepts/<domain>/"""
    d = WIKI_DIR / "concepts" / domain_key
    if not d.is_dir():
        return []
    return sorted(
        p.relative_to(REPO_ROOT).as_posix()
        for p in d.rglob("*.md") if p.is_file()
    )


def get_domain_synthesis_paths(domain_key: str) -> list[str]:
    """Return wiki/synthesis/ pages whose content references this domain."""
    d = WIKI_DIR / "synthesis"
    if not d.is_dir():
        return []
    domain_lower = domain_key.lower().replace("-", " ")
    results = []
    for p in d.rglob("*.md"):
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            continue
        # Check if the frontmatter or content contains a domain tag/key
        if domain_lower in text.lower()[:2000]:
            results.append(p.relative_to(REPO_ROOT).as_posix())
    return sorted(results)


def get_domain_edges(graph: dict, domain_paths: set[str]) -> list[dict]:
    """Filter graph edges involving any path in domain_paths."""
    return [
        e for e in graph["edges"]
        if (e["from"] in domain_paths or e["to"] in domain_paths)
        and not e["broken"]
    ]


def compute_hub_scores(domain_paths: set[str], edges: list[dict]) -> dict[str, int]:
    """Compute (in+out) degree for domain paths."""
    score: Counter[str] = Counter()
    for e in edges:
        if e["from"] in domain_paths:
            score[e["from"]] += 1
        if e["to"] in domain_paths:
            score[e["to"]] += 1
    return dict(score)


def find_cross_domain_edges(graph: dict, domain_paths: set[str], current_domain: str) -> list[dict]:
    """Find edges that go from domain_paths to paths in OTHER domains."""
    domain_node_map = {}
    for node in graph["nodes"]:
        d = node.get("domain", "other")
        if d == current_domain or d in ENTITY_DIR_MAP:
            domain_node_map[node["path"]] = d

    result = []
    for e in graph["edges"]:
        if e["broken"]:
            continue
        if e["from"] in domain_paths:
            to_domain = domain_node_map.get(e["to"], "other")
            if to_domain != current_domain and to_domain in ENTITY_DIR_MAP:
                result.append({**e, "from_domain": current_domain, "to_domain": to_domain})
        elif e["to"] in domain_paths:
            from_domain = domain_node_map.get(e["from"], "other")
            if from_domain != current_domain and from_domain in ENTITY_DIR_MAP:
                result.append({**e, "from_domain": from_domain, "to_domain": current_domain})
    return sorted(result, key=lambda x: (x.get("to_domain", ""), x["from"]))


def get_recent_journal_entries(domain_key: str, days: int = 30) -> list[tuple[str, str]]:
    """Return list of (date_str, snippet) from journal mentioning this domain."""
    if not JOURNAL_DIR.is_dir():
        return []
    cutoff = date.today() - timedelta(days=days)
    domain_lower = domain_key.lower().replace("-", " ")
    results = []
    for p in sorted(JOURNAL_DIR.glob("*.md"), reverse=True):
        # Filename is YYYY-MM-DD.md
        try:
            fdate = date.fromisoformat(p.stem)
        except ValueError:
            continue
        if fdate < cutoff:
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            continue
        # Look for domain mentions (case-insensitive in first 500 chars)
        if domain_lower in text.lower()[:500]:
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            snippet = lines[2] if len(lines) > 2 else (lines[1] if len(lines) > 1 else "mentioned")
            if len(snippet) > 120:
                snippet = snippet[:117] + "..."
            results.append((p.stem, snippet))
    return results[:5]


def generate_index(domain_key: str) -> str:
    graph = load_graph()
    domain_label = ENTITY_DIR_MAP[domain_key]
    entity_paths = get_domain_entity_paths(domain_key)
    concept_paths = get_domain_concept_paths(domain_key)
    synthesis_paths = get_domain_synthesis_paths(domain_key)

    all_domain_paths = set(entity_paths + concept_paths + synthesis_paths)

    lines = []
    lines.append(f"# {domain_label} — Knowledge Index")
    lines.append("")
    lines.append(f"> Auto-generated index for `{domain_key}` domain. Updated {date.today().isoformat()}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # === Stats ===
    domain_edges = get_domain_edges(graph, all_domain_paths)
    ebt: Counter[str] = Counter()
    broken = 0
    for e in domain_edges:
        ebt[e["type"]] += 1
        if e["broken"]:
            broken += 1
    concept_count = len([p for p in all_domain_paths if "concepts/" in p])
    synth_count = len([p for p in all_domain_paths if "synthesis/" in p])

    lines.append("## 📊 Domain Stats")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Entities | {len(entity_paths)} |")
    lines.append(f"| Concepts | {concept_count} |")
    lines.append(f"| Synthesis | {synth_count} |")
    lines.append(f"| Total pages | {len(all_domain_paths)} |")
    lines.append(f"| Knowledge Graph Edges | {len(domain_edges)} |")
    lines.append(f"| Broken Links | {broken} |")
    lines.append("")
    if ebt:
        lines.append("**Edges by type:**")
        for etype in ("wikilink", "mdlink", "depends", "extends", "implements"):
            cnt = ebt.get(etype, 0)
            if cnt:
                icon = TYPE_ICON.get(etype, "•")
                lines.append(f"- {icon} **{etype}**: {cnt}")
    lines.append("")

    # === Hub Pages ===
    hubs = compute_hub_scores(all_domain_paths, domain_edges)
    sorted_hubs = sorted(hubs.items(), key=lambda x: -x[1])
    if sorted_hubs:
        lines.append("## 🔥 Top Hubs (Most Connected)")
        lines.append("")
        lines.append("| Page | Connections |")
        lines.append("|------|-------------|")
        for path, score in sorted_hubs[:10]:
            title = path.replace(f"wiki/entities/{domain_key}/", "").removesuffix(".md").replace("-", " ").title()
            link = path.removesuffix(".md")
            lines.append(f"| [{title}](/{link}) | {score} |")
        lines.append("")

    # === All Entities ===
    if entity_paths:
        lines.append("## 📦 Entities")
        lines.append("")
        # Build descriptions from headers
        entity_info = []
        for p in entity_paths:
            fp = REPO_ROOT / p
            try:
                text = fp.read_text(encoding="utf-8")
                title = extract_title(text, fp.stem.replace("-", " ").title())
            except Exception:
                title = fp.stem.replace("-", " ").title()
            link = p.removesuffix(".md")
            hscore = hubs.get(p, 0)
            entity_info.append((hscore, link, title))
        entity_info.sort(key=lambda x: -x[0])

        lines.append(f"**{len(entity_info)} entities** — sorted by connectivity (hub score)")
        lines.append("")
        for score, link, title in entity_info:
            score_str = f" [{score}c]" if score > 0 else ""
            lines.append(f"- [[{link}|{title}]]{score_str}")
        lines.append("")

    # === Concepts ===
    if concept_paths:
        lines.append("## 🧠 Concepts")
        lines.append("")
        for p in concept_paths:
            fp = REPO_ROOT / p
            try:
                text = fp.read_text(encoding="utf-8")
                title = extract_title(text, fp.stem.replace("-", " ").title())
            except Exception:
                title = fp.stem.replace("-", " ").title()
            link = p.removesuffix(".md")
            hscore = hubs.get(p, 0)
            score_str = f" [{hscore}c]" if hscore > 0 else ""
            lines.append(f"- [[{link}|{title}]]{score_str}")
        lines.append("")

    # === Synthesis ===
    if synthesis_paths:
        lines.append("## 🔬 Synthesis Documents")
        lines.append("")
        for p in synthesis_paths:
            link = p.removesuffix(".md")
            lines.append(f"- [[{link}]]")
        lines.append("")

    # === Cross-Domain Bridges ===
    bridges = find_cross_domain_edges(graph, all_domain_paths, domain_key)
    if bridges:
        lines.append("## 🌉 Cross-Domain Bridges")
        lines.append("")
        lines.append("| Source | Type | Target Domain |")
        lines.append("|--------|------|---------------|")
        for e in bridges[:15]:
            s_title = e["from"].rsplit("/", 1)[-1].removesuffix(".md").replace("-", " ").title()
            t_title = e.get("to_domain", "other")
            icon = TYPE_ICON.get(e["type"], "•")
            lines.append(f"| [[{e['from'].removesuffix('.md')}|{s_title}]] | {icon} {e['type']} | {t_title} |")
        if len(bridges) > 15:
            lines.append(f"| ... and {len(bridges) - 15} more bridges | | |")
        lines.append("")

    # === Recent Journal ===
    journal = get_recent_journal_entries(domain_key)
    if journal:
        lines.append("## 📅 Recent Journal Activity")
        lines.append("")
        for date_str, snippet in journal:
            lines.append(f"- **{date_str}**: {snippet}")
        lines.append("")

    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--json", action="store_true", help="Dump JSON counts")
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args()

    counts = {}

    for domain_key in ["iot", "env", "ai-tools", "pharmacy"]:
        content = generate_index(domain_key)
        filename = f"index-{domain_key}.md"
        outpath = REPO_ROOT / filename
        outpath.write_text(content, encoding="utf-8")

        # Count lines for feedback
        entity_count = len(get_domain_entity_paths(domain_key))
        counts[domain_key] = entity_count

        if not args.quiet:
            print(f"generated {filename}: {entity_count} entities → {outpath}")

    if args.json:
        print(json.dumps(counts, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())