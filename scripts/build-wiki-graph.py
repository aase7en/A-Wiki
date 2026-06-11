#!/usr/bin/env python3
"""
build-wiki-graph.py — Parse wiki/*.md, extract links, output knowledge graph JSON.

Nodes: each markdown file under wiki/
Edges: [[wikilink]] + [text](relative.md) link references + semantic typing

Edge types (5):
  - wikilink   : generic [[page]] cross-reference
  - mdlink     : [text](path.md) link
  - depends    : target is a dependency/import/requirement of source
                (triggered by: "requires", "depends on", "needs", "install", "import")
  - extends    : target extends/broadens/specializes the source concept
                (triggered by: "see also", "related", "further", "more info", "continuation")
  - implements : target implements a concept described by source
                (triggered by: "implement", "example", "tutorial", "how to", "guide")

Output: .wiki-graph.json at repo root.

Schema:
{
  "generated_at": "2026-05-24",
  "stats": {"nodes": N, "edges": M, "broken_links": K, "orphans": J, "hubs": [...],
            "edges_by_type": {"wikilink": N, "mdlink": N, ...}},
  "nodes": [{"path": "wiki/...", "title": "...", "domain": "iot"}, ...],
  "edges": [{"from": "...", "to": "...", "type": "wikilink|mdlink|depends|extends|implements", "broken": false}, ...]
}

Companion: scripts/query-graph.py for queries.
"""
from __future__ import annotations
import argparse
import datetime as dt
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WIKI_DIR = REPO_ROOT / "wiki"
OUTPUT = REPO_ROOT / ".wiki-graph.json"

# Root-level pages that are wiki-linkable (referenced from inside wiki/)
ROOT_PAGES = ("CLAUDE.md", "README.md", "profile.md", "index.md")

# Skip these source dirs from outgoing-link extraction — content is auto-generated
# (truncated table cells in context overviews) so wikilinks there are noise.
# Files still appear as graph nodes; we just don't follow their outgoing links.
PARSE_SKIP_DIRS = (WIKI_DIR / "context",)

WIKILINK_RE = re.compile(r"\[\[([^\]\|#]+)(?:#[^\]\|]*)?(?:\|[^\]]+)?\]\]")
MDLINK_RE = re.compile(r"\[(?:[^\]]+)\]\(([^)]+\.md)(?:#[^)]*)?\)")
H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
# Strip fenced code blocks (``` ... ```) and inline code (`...`) before link extraction
CODE_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")

# Semantic type triggers: key phrases within the surrounding line of the link
SEMANTIC_TRIGGERS: dict[str, list[re.Pattern]] = {
    "depends": [
        re.compile(r"\b(?:requires?|depends?\s+on|needs?\s+|install|import|setup)\b", re.IGNORECASE),
    ],
    "extends": [
        re.compile(r"\b(?:see\s+also|related|further|more\s+info|continuation|read\s+more)\b", re.IGNORECASE),
    ],
    "implements": [
        re.compile(r"\b(?:implement|example|tutorial|how\s+to|guide|walkthrough)\b", re.IGNORECASE),
    ],
}


def collect_files() -> list[Path]:
    if not WIKI_DIR.is_dir():
        return []
    files = [p for p in WIKI_DIR.rglob("*.md") if p.is_file()]
    for name in ROOT_PAGES:
        p = REPO_ROOT / name
        if p.is_file():
            files.append(p)
    # Also include domain index pages at root (index-iot.md, index-env.md, ...)
    for p in REPO_ROOT.glob("index-*.md"):
        if p.is_file():
            files.append(p)
    return sorted(set(files))


def strip_code(text: str) -> str:
    """Remove fenced and inline code so placeholder wikilinks in examples aren't matched."""
    text = CODE_FENCE_RE.sub("", text)
    text = INLINE_CODE_RE.sub("", text)
    return text


def should_parse_links(path: Path) -> bool:
    """Files we keep as graph nodes but skip when scanning for outgoing links."""
    for d in PARSE_SKIP_DIRS:
        try:
            path.relative_to(d)
            return False
        except ValueError:
            pass
    return True


def is_external_target(target: str) -> bool:
    """Target refers to a file that exists in the repo but outside the indexed graph."""
    t = target.strip().lstrip("/")
    if not t:
        return False
    if (REPO_ROOT / t).exists():
        return True
    if not t.endswith(".md") and (REPO_ROOT / (t + ".md")).exists():
        return True
    return False


def is_external_url(target: str) -> bool:
    """Target is an external URL/protocol and should not count as a local broken link."""
    return target.strip().startswith(("http://", "https://", "mailto:"))


def infer_domain(path: Path) -> str:
    parts = path.relative_to(REPO_ROOT).parts
    if not (len(parts) >= 2 and parts[0] == "wiki"):
        return "other"
    section = parts[1]
    if section == "context":
        return "context"
    if section in ("entities", "concepts") and len(parts) >= 4:
        # wiki/entities/<domain>/<file>.md
        return parts[2]
    if section in ("sources", "synthesis"):
        # No domain subdir — section name itself
        return section
    return "other"


def extract_title(text: str, fallback: str) -> str:
    body = text
    m = FRONTMATTER_RE.match(text)
    if m:
        body = text[m.end():]
    h1 = H1_RE.search(body)
    return h1.group(1).strip() if h1 else fallback


def resolve_wikilink(target: str, all_paths: dict[str, Path]) -> Path | None:
    """Try to resolve [[target]] to an actual file by stem or last-segment match."""
    t = target.strip()
    if not t:
        return None
    # try exact path under wiki/
    candidates = [
        f"wiki/{t}.md",
        f"wiki/{t}",
        f"{t}.md",
        f"{t}",
    ]
    for c in candidates:
        p = (REPO_ROOT / c).resolve()
        try:
            rel = p.relative_to(REPO_ROOT).as_posix()
        except ValueError:
            continue
        if rel in all_paths:
            return all_paths[rel]
    # fallback: match by stem (last path segment)
    stem = t.rsplit("/", 1)[-1].removesuffix(".md")
    matches = [p for rel, p in all_paths.items() if p.stem == stem]
    if len(matches) == 1:
        return matches[0]
    return None


def resolve_mdlink(source: Path, target: str, all_paths: dict[str, Path]) -> Path | None:
    """Resolve [text](relative.md) — relative to source's dir, or to repo root if leading `/`."""
    t = target.strip()
    if t.startswith("http://") or t.startswith("https://") or t.startswith("mailto:"):
        return None
    try:
        if t.startswith("/"):
            p = (REPO_ROOT / t.lstrip("/")).resolve()
        else:
            p = (source.parent / t).resolve()
        rel = p.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return None
    return all_paths.get(rel)


def infer_semantic_type(context_line: str, link_text: str, link_target: str, base_type: str) -> str:
    """
    Given the line containing the link, try to infer a semantic edge type.
    Returns one of: wikilink, mdlink, depends, extends, implements
    """
    if base_type == "mdlink":
        # mdlink preserves its own type classification
        # But can be upgraded to semantic if triggers match context
        pass

    # Check trivially: if the link text itself is a trigger phrase
    text_lower = link_text.lower().strip()
    if text_lower in ("see also", "see"):
        return "extends"
    if text_lower in ("example", "examples", "tutorial", "guide", "walkthrough"):
        return "implements"
    if text_lower in ("requirements", "prerequisites", "dependencies", "install"):
        return "depends"

    # Check context line for trigger phrases
    for edge_type, patterns in SEMANTIC_TRIGGERS.items():
        for pat in patterns:
            if pat.search(context_line):
                return edge_type

    return base_type


def extract_link_context(text: str, match_start: int, match_end: int, window: int = 60) -> str:
    """Extract surrounding context of a link match."""
    start = max(0, match_start - window)
    end = min(len(text), match_end + window)
    return text[start:end]


def build() -> dict:
    files = collect_files()
    path_lookup = {p.relative_to(REPO_ROOT).as_posix(): p for p in files}

    nodes = []
    edges = []
    broken = 0
    in_degree: Counter[str] = Counter()
    out_degree: Counter[str] = Counter()
    edges_by_type: Counter[str] = Counter()

    for fp in files:
        rel = fp.relative_to(REPO_ROOT).as_posix()
        try:
            text = fp.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = ""
        nodes.append({
            "path": rel,
            "title": extract_title(text, fp.stem),
            "domain": infer_domain(fp),
        })
        in_degree.setdefault(rel, 0)
        out_degree.setdefault(rel, 0)

        if not should_parse_links(fp):
            continue

        scan_text = strip_code(text)
        seen_edges: set[tuple[str, str, str]] = set()

        # Process wikilinks
        for m in WIKILINK_RE.finditer(scan_text):
            target = m.group(1).strip()
            resolved = resolve_wikilink(target, path_lookup)
            to_rel = resolved.relative_to(REPO_ROOT).as_posix() if resolved else None

            # Extract context for semantic typing
            ctx = extract_link_context(scan_text, m.start(), m.end())
            # Get the link text (after | in [[target|text]])
            link_text = m.group(0).split("|")[-1].rstrip("]]") if "|" in m.group(0) else target
            etype = infer_semantic_type(ctx, link_text, target, "wikilink")

            key = (rel, to_rel or f"?{target}", etype)
            if key in seen_edges:
                continue
            seen_edges.add(key)
            external = resolved is None and (is_external_url(target) or is_external_target(target))
            edges.append({
                "from": rel,
                "to": to_rel or target,
                "type": etype,
                "broken": resolved is None and not external,
                "external": external,
            })
            edges_by_type[etype] += 1
            if resolved:
                in_degree[to_rel] += 1
                out_degree[rel] += 1
            elif not external:
                broken += 1

        # Process markdown links
        for m in MDLINK_RE.finditer(scan_text):
            target = m.group(1).strip()
            resolved = resolve_mdlink(fp, target, path_lookup)
            to_rel = resolved.relative_to(REPO_ROOT).as_posix() if resolved else None

            # Extract context for semantic typing
            ctx = extract_link_context(scan_text, m.start(), m.end())
            # The link text is the [text] part before the (target)
            bracket_match = re.search(r"\[([^\]]*)\]", scan_text[max(0, m.start()-200):m.start()])
            link_text = bracket_match.group(1) if bracket_match else target
            etype = infer_semantic_type(ctx, link_text, target, "mdlink")

            key = (rel, to_rel or f"?{target}", etype)
            if key in seen_edges:
                continue
            seen_edges.add(key)
            external = resolved is None and (is_external_url(target) or is_external_target(target))
            edges.append({
                "from": rel,
                "to": to_rel or target,
                "type": etype,
                "broken": resolved is None and not external,
                "external": external,
            })
            edges_by_type[etype] += 1
            if resolved:
                in_degree[to_rel] += 1
                out_degree[rel] += 1
            elif not external:
                broken += 1

    orphans = sorted(p for p in path_lookup if in_degree[p] == 0 and out_degree[p] == 0)
    # Hubs = top 10 by (in + out) excluding context/ noise
    score = {p: in_degree[p] + out_degree[p] for p in path_lookup}
    hubs = sorted(score.items(), key=lambda kv: -kv[1])[:10]

    return {
        "generated_at": dt.date.today().isoformat(),
        "stats": {
            "nodes": len(nodes),
            "edges": len(edges),
            "edges_by_type": dict(edges_by_type),
            "broken_links": broken,
            "orphans": len(orphans),
            "hubs": [{"path": p, "score": s} for p, s in hubs if s > 0],
            "orphans_list": orphans[:20],
        },
        "nodes": nodes,
        "edges": edges,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", default=str(OUTPUT))
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args()

    graph = build()
    out = Path(args.output)
    out.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")
    if not args.quiet:
        s = graph["stats"]
        ebt = s.get("edges_by_type", {})
        type_summary = " ".join(f"{k}={v}" for k, v in sorted(ebt.items()))
        print(
            f"built {out}: {s['nodes']} nodes, {s['edges']} edges "
            f"({type_summary}), {s['broken_links']} broken, {s['orphans']} orphans"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
