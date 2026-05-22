#!/usr/bin/env python3
"""
build-wiki-graph.py — Parse wiki/*.md, extract links, output knowledge graph JSON.

Nodes: each markdown file under wiki/
Edges: [[wikilink]] + [text](relative.md) link references

Output: .wiki-graph.json at repo root.

Schema:
{
  "generated_at": "2026-05-18",
  "stats": {"nodes": N, "edges": M, "broken_links": K, "orphans": J, "hubs": [...]},
  "nodes": [{"path": "wiki/...", "title": "...", "domain": "iot"}, ...],
  "edges": [{"from": "...", "to": "...", "type": "wikilink|mdlink", "broken": false}, ...]
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
ROOT_PAGES = ("CLAUDE.md", "README.md", "profile.md", "log.md", "index.md")

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


def build() -> dict:
    files = collect_files()
    path_lookup = {p.relative_to(REPO_ROOT).as_posix(): p for p in files}

    nodes = []
    edges = []
    broken = 0
    in_degree: Counter[str] = Counter()
    out_degree: Counter[str] = Counter()

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
        for m in WIKILINK_RE.finditer(scan_text):
            target = m.group(1).strip()
            resolved = resolve_wikilink(target, path_lookup)
            to_rel = resolved.relative_to(REPO_ROOT).as_posix() if resolved else None
            key = (rel, to_rel or f"?{target}", "wikilink")
            if key in seen_edges:
                continue
            seen_edges.add(key)
            external = resolved is None and is_external_target(target)
            edges.append({
                "from": rel,
                "to": to_rel or target,
                "type": "wikilink",
                "broken": resolved is None and not external,
                "external": external,
            })
            if resolved:
                in_degree[to_rel] += 1
                out_degree[rel] += 1
            elif not external:
                broken += 1
        for m in MDLINK_RE.finditer(scan_text):
            target = m.group(1).strip()
            resolved = resolve_mdlink(fp, target, path_lookup)
            to_rel = resolved.relative_to(REPO_ROOT).as_posix() if resolved else None
            key = (rel, to_rel or f"?{target}", "mdlink")
            if key in seen_edges:
                continue
            seen_edges.add(key)
            external = resolved is None and is_external_target(target)
            edges.append({
                "from": rel,
                "to": to_rel or target,
                "type": "mdlink",
                "broken": resolved is None and not external,
                "external": external,
            })
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
        print(
            f"built {out}: {s['nodes']} nodes, {s['edges']} edges, "
            f"{s['broken_links']} broken, {s['orphans']} orphans"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
