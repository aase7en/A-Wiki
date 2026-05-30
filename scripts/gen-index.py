#!/usr/bin/env python3
"""
gen-index.py — Auto-generate wiki/context/overview files by scanning all wiki .md files.

Generates 6 files (token-split to keep auto-loaded baseline small):

  wiki/context/wiki-overview.md     — Stats + synthesis (cross-domain) + pointers (auto-loaded)
  wiki/context/overview-iot.md      — IoT entities + concepts
  wiki/context/overview-env.md      — Environmental Health entities + concepts
  wiki/context/overview-ai.md       — AI Tools entities + concepts
  wiki/context/overview-pharmacy.md — Pharmacy entities + concepts
  wiki/context/overview-sources.md  — All ingested sources

CLAUDE.md auto-loads only the slim wiki-overview.md. Domain files are read
on-demand when the user asks about that domain (Topic Router pattern in
wiki/CLAUDE.md).

Usage:
    python3 scripts/gen-index.py             # write all files
    python3 scripts/gen-index.py --check     # exit 1 if any file out of date (CI)
    python3 scripts/gen-index.py --stdout    # print main wiki-overview to stdout
"""
from __future__ import annotations
import argparse
import datetime as dt
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WIKI_DIR = REPO_ROOT / "wiki"
CONTEXT_DIR = WIKI_DIR / "context"
MAIN_OUTPUT = CONTEXT_DIR / "wiki-overview.md"

# Sections + domain order (controls output layout)
SECTION_ORDER = ["entities", "concepts", "synthesis", "sources"]
DOMAIN_ORDER = ["iot", "env", "ai-tools", "pharmacy"]
SECTION_TITLES = {
    "entities": "ENTITIES",
    "concepts": "CONCEPTS",
    "synthesis": "SYNTHESIS",
    "sources": "SOURCES",
}
DOMAIN_TITLES = {
    "iot": "IoT",
    "env": "Environmental Health",
    "ai-tools": "AI Tools",
    "pharmacy": "Pharmacy",
}
# Short slug used in per-domain output filename (e.g. "ai-tools" → "ai")
DOMAIN_FILE_SLUG = {
    "iot": "iot",
    "env": "env",
    "ai-tools": "ai",
    "pharmacy": "pharmacy",
}

ABSTRACT_MAX = 65


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parse YAML-ish frontmatter (no PyYAML dep). Returns (meta, body)."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    raw = text[3:end].strip()
    body = text[end + 4 :].lstrip("\n")
    meta: dict[str, str | list[str]] = {}
    for line in raw.splitlines():
        line = line.rstrip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        if val.startswith("[") and val.endswith("]"):
            items = [s.strip().strip('"').strip("'") for s in val[1:-1].split(",")]
            meta[key] = [s for s in items if s]
        else:
            meta[key] = val.strip('"').strip("'")
    return meta, body


def extract_abstract(body: str) -> str:
    """Find a one-line abstract from the page body.

    Priority:
      1. Line starting with `> TL;DR:` (or `> **TL;DR**:`)
      2. First non-empty paragraph after H1, that isn't a heading/table/list/blockquote
    """
    lines = body.splitlines()
    for ln in lines:
        m = re.match(r"^\s*>\s*\**TL;DR\**\s*[:：]\s*(.+)", ln, re.IGNORECASE)
        if m:
            return clip(m.group(1).strip())
    seen_h1 = False
    buf: list[str] = []
    for ln in lines:
        s = ln.strip()
        if s.startswith("# ") and not seen_h1:
            seen_h1 = True
            continue
        if not seen_h1:
            continue
        if not s:
            if buf:
                break
            continue
        if s.startswith(("#", "|", "-", "*", ">", "```", "**ผู้")):
            if buf:
                break
            continue
        buf.append(s)
        if sum(len(x) for x in buf) > ABSTRACT_MAX:
            break
    if buf:
        return clip(" ".join(buf))
    return "(no abstract)"


def clip(s: str) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) <= ABSTRACT_MAX:
        return s
    return s[: ABSTRACT_MAX - 1].rstrip() + "…"


def slug_from_path(p: Path) -> str:
    return p.stem


def domain_from_path(p: Path, section: str) -> str:
    """Extract domain (iot/env/ai-tools) from path. Sources/synthesis have no subfolder."""
    rel = p.relative_to(WIKI_DIR)
    parts = rel.parts
    if len(parts) >= 3 and parts[0] in ("entities", "concepts"):
        return parts[1]
    return ""


def collect_pages() -> dict[str, dict[str, list[dict]]]:
    """Walk wiki/, return {section: {domain: [page_record, ...]}}."""
    pages: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for section in SECTION_ORDER:
        section_dir = WIKI_DIR / section
        if not section_dir.is_dir():
            continue
        for md_path in sorted(section_dir.rglob("*.md")):
            try:
                text = md_path.read_text(encoding="utf-8")
            except Exception as e:
                print(f"warn: cannot read {md_path}: {e}", file=sys.stderr)
                continue
            meta, body = parse_frontmatter(text)
            domain = domain_from_path(md_path, section)
            rec = {
                "slug": slug_from_path(md_path),
                "path": str(md_path.relative_to(REPO_ROOT)),
                "abstract": extract_abstract(body),
                "tags": meta.get("tags") or [],
                "type": meta.get("type", section.rstrip("s")),
                "category": meta.get("category", ""),
                "quality": meta.get("quality", ""),
                "title": meta.get("title", ""),
            }
            pages[section][domain].append(rec)
    return pages


def _table_rows(rows: list[dict]) -> list[str]:
    out = ["| slug | abstract |", "|------|----------|"]
    for r in sorted(rows, key=lambda r: r["slug"]):
        abstract = r["abstract"].replace("|", "\\|")
        out.append(f"| `{r['slug']}` | {abstract} |")
    return out


def render_main(pages: dict[str, dict[str, list[dict]]]) -> str:
    """Slim main overview — stats + synthesis (cross-domain) + pointers."""
    today = dt.date.today().isoformat()
    total = sum(len(rows) for sec in pages.values() for rows in sec.values())
    counts = {sec: sum(len(rows) for rows in pages[sec].values()) for sec in SECTION_ORDER}

    out: list[str] = []
    out.append("# Wiki Overview — Auto-generated INDEX (slim)")
    out.append("")
    out.append("> ⚙️ **Auto-generated by `scripts/gen-index.py`** — do not edit manually.")
    out.append(f"> Last updated: {today}  |  Run: `python3 scripts/gen-index.py`")
    out.append("")
    out.append("> 🎯 **Token-split**: This file is loaded every session. Domain details live in")
    out.append("> separate `overview-<domain>.md` files — read on demand when the user asks")
    out.append("> about that specific domain.")
    out.append("")
    out.append("---")
    out.append("")
    out.append("## Stats")
    out.append("")
    out.append("| Type | Count |")
    out.append("|------|-------|")
    for sec in SECTION_ORDER:
        out.append(f"| {SECTION_TITLES[sec]} | {counts.get(sec, 0)} |")
    out.append(f"| **Total** | **{total} pages** |")
    out.append("")
    out.append("---")
    out.append("")
    out.append("## Domain Indexes (load on demand)")
    out.append("")
    # Per-domain counts row
    ent = pages.get("entities", {})
    con = pages.get("concepts", {})
    out.append("| Domain | Entities | Concepts | Context File | Rich Index |")
    out.append("|--------|----------|----------|--------------|------------|")
    for dom in DOMAIN_ORDER:
        e = len(ent.get(dom, []))
        c = len(con.get(dom, []))
        slug = DOMAIN_FILE_SLUG[dom]
        out.append(f"| {DOMAIN_TITLES[dom]} | {e} | {c} | `wiki/context/overview-{slug}.md` | `index-{slug}.md` |")
    out.append("")
    src_count = sum(len(rows) for rows in pages.get("sources", {}).values())
    out.append(f"- **Sources** ({src_count}): `wiki/context/overview-sources.md`")
    out.append(f"- **Regen rich indexes**: `python3 scripts/gen-domain-indexes.py`")
    out.append("")

    # Synthesis stays in main — it's cross-domain by definition (typically small)
    synthesis_pages = pages.get("synthesis", {})
    syn_rows: list[dict] = []
    for rows in synthesis_pages.values():
        syn_rows.extend(rows)
    if syn_rows:
        out.append("---")
        out.append("")
        out.append("## SYNTHESIS (cross-domain — kept inline for quick recall)")
        out.append("")
        out.extend(_table_rows(syn_rows))
        out.append("")

    out.append("---")
    out.append("")
    out.append(f"*Slim baseline. Detailed entries split across 5 domain files. "
               f"Total {total} pages across {len(SECTION_ORDER)} sections.*")
    out.append("")
    return "\n".join(out)


def render_domain(domain: str, pages: dict[str, dict[str, list[dict]]]) -> str:
    """Per-domain overview — entities + concepts for one domain."""
    today = dt.date.today().isoformat()
    title = DOMAIN_TITLES[domain]
    entities = pages.get("entities", {}).get(domain, [])
    concepts = pages.get("concepts", {}).get(domain, [])

    out: list[str] = []
    out.append(f"# Overview — {title}")
    out.append("")
    out.append("> ⚙️ **Auto-generated by `scripts/gen-index.py`** — do not edit manually.")
    out.append(f"> Last updated: {today}  |  Domain slug: `{domain}`")
    out.append("")
    out.append(f"> 📖 **When to load**: Read this file when the user asks about {title}-specific")
    out.append("> pages. The slim `wiki-overview.md` only carries cross-domain synthesis.")
    out.append("")
    out.append("---")
    out.append("")
    out.append("## Stats")
    out.append("")
    out.append(f"- Entities: **{len(entities)}**")
    out.append(f"- Concepts: **{len(concepts)}**")
    out.append("")
    if entities:
        out.append("---")
        out.append("")
        out.append("## ENTITIES")
        out.append("")
        out.extend(_table_rows(entities))
        out.append("")
    if concepts:
        out.append("---")
        out.append("")
        out.append("## CONCEPTS")
        out.append("")
        out.extend(_table_rows(concepts))
        out.append("")
    return "\n".join(out)


def render_sources(pages: dict[str, dict[str, list[dict]]]) -> str:
    """All sources in a single file (kept out of baseline to save tokens)."""
    today = dt.date.today().isoformat()
    src_pages = pages.get("sources", {})
    rows: list[dict] = []
    for v in src_pages.values():
        rows.extend(v)

    out: list[str] = []
    out.append("# Overview — Sources")
    out.append("")
    out.append("> ⚙️ **Auto-generated by `scripts/gen-index.py`** — do not edit manually.")
    out.append(f"> Last updated: {today}")
    out.append("")
    out.append("> 📖 **When to load**: Read this file when the user references a specific source,")
    out.append("> or when ingesting/verifying. The slim `wiki-overview.md` does not list sources.")
    out.append("")
    out.append("---")
    out.append("")
    out.append(f"## Stats — {len(rows)} sources")
    out.append("")
    if rows:
        out.extend(_table_rows(rows))
        out.append("")
    return "\n".join(out)


def collect_outputs(pages: dict[str, dict[str, list[dict]]]) -> dict[Path, str]:
    """Return mapping of output_path → rendered content for all files this script writes."""
    main_output = CONTEXT_DIR / "wiki-overview.md"
    outputs: dict[Path, str] = {main_output: render_main(pages)}
    for dom in DOMAIN_ORDER:
        slug = DOMAIN_FILE_SLUG[dom]
        outputs[CONTEXT_DIR / f"overview-{slug}.md"] = render_domain(dom, pages)
    outputs[CONTEXT_DIR / "overview-sources.md"] = render_sources(pages)
    return outputs


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate wiki context overview files from wiki/ tree")
    ap.add_argument("--stdout", action="store_true",
                    help="Print main wiki-overview to stdout (don't write any file)")
    ap.add_argument("--check", action="store_true",
                    help="Exit 1 if any generated file is out of date (CI mode)")
    ap.add_argument("--domain", type=str,
                    help="Regenerate only a single domain overview file (iot|env|ai-tools|pharmacy)")
    ap.add_argument("--fetch-arxiv", action="store_true",
                    help="Also refresh arXiv source suggestions (network; can be slow)")
    args = ap.parse_args()

    pages = collect_pages()
    outputs = collect_outputs(pages)

    if args.stdout:
        sys.stdout.write(outputs[CONTEXT_DIR / "wiki-overview.md"])
        return 0

    if args.check:
        # Strip the "Last updated: YYYY-MM-DD" date before comparing so that the
        # check reflects actual wiki-content changes, not just the generation date.
        _date_re = re.compile(r"(Last updated:)\s*\d{4}-\d{2}-\d{2}")
        def _norm(s: str) -> str:
            return _date_re.sub(r"\1 <date>", s).strip()

        stale: list[Path] = []
        for path, content in outputs.items():
            existing = path.read_text(encoding="utf-8") if path.exists() else ""
            if _norm(existing) != _norm(content):
                stale.append(path)
        if stale:
            for p in stale:
                print(f"::: {p.relative_to(REPO_ROOT)} is out of date — run scripts/gen-index.py",
                      file=sys.stderr)
            return 1
        return 0

    CONTEXT_DIR.mkdir(parents=True, exist_ok=True)

    if args.domain:
        # Regenerate only one domain overview
        slug = args.domain
        dom = slug if slug in DOMAIN_ORDER else slug
        # Find the domain key
        dom_key = slug  # slugs match DOMAIN_ORDER keys
        path = CONTEXT_DIR / f"overview-{DOMAIN_FILE_SLUG[dom_key]}.md"
        content = render_domain(dom_key, pages)
        path.write_text(content, encoding="utf-8")
        print(f"[OK] Wrote single domain file: {path.relative_to(REPO_ROOT)}")
        return 0

    for path, content in outputs.items():
        path.write_text(content, encoding="utf-8")
    total = sum(len(r) for s in pages.values() for r in s.values())
    print(f"[OK] Wrote {len(outputs)} files in {CONTEXT_DIR.relative_to(REPO_ROOT)} ({total} pages)")

    # Chain: rebuild local search index + knowledge graph + embeddings (Phase 2-4 upgrade)
    # Best-effort — don't fail gen-index if these aren't installed yet
    import subprocess
    scripts_dir = REPO_ROOT / "scripts"
    for chained in ("build-wiki-index.py", "build-wiki-graph.py", "build-canvas.py"):
        sp = scripts_dir / chained
        if sp.exists():
            try:
                subprocess.run([sys.executable, str(sp)], check=True, capture_output=True)
                print(f"[OK] chained: {chained}")
            except subprocess.CalledProcessError as e:
                print(f"[WARN] {chained} failed: {e.stderr.decode('utf-8', 'replace')[:200]}", file=sys.stderr)

    # Chain: auto-synthesis pipeline (Phase 4c)
    for chained_script in ("raw-to-source.py", "raw-to-synth.py"):
        sp = scripts_dir / chained_script
        if sp.exists():
            try:
                subprocess.run(
                    [sys.executable, str(sp), "--apply"] if chained_script == "raw-to-source.py" else [sys.executable, str(sp)],
                    check=True, capture_output=True
                )
                print(f"[OK] chained: {chained_script}")
            except subprocess.CalledProcessError as e:
                print(f"[WARN] raw-to-synth.py failed: {e.stderr.decode('utf-8', 'replace')[:200]}", file=sys.stderr)

    # Chain: arXiv fetch (Phase 4) — Tier 1 search for domain-relevant papers, silent for speed
    arxiv_fetcher = scripts_dir / "fetch-arxiv.py"
    fetch_arxiv = args.fetch_arxiv or os.environ.get("AWIKI_GEN_INDEX_FETCH_ARXIV") == "1"
    if arxiv_fetcher.exists() and fetch_arxiv and not args.check:
        arxiv_queries = {
            "iot":       'cat:cs.NI AND (IoT OR LoRa OR "embedded systems" OR "edge computing")',
            "ai-tools":  'cat:cs.AI AND (LLM OR "large language model" OR "agent benchmark" OR MCP)',
            "pharmacy":  'cat:cs.CE AND (pharmacy OR drug OR vaccine OR "cold chain")',
            "env":       'cat:physics.ao-ph AND ("air quality" OR "water quality" OR wastewater OR sensor)',
        }
        for domain, query in arxiv_queries.items():
            try:
                subprocess.run(
                    [sys.executable, str(arxiv_fetcher), "--search", query, "--max", "2"],
                    check=True, capture_output=True, timeout=30
                )
            except subprocess.TimeoutExpired:
                pass  # arXiv API slow, skip silently
            except subprocess.CalledProcessError:
                pass  # No results for this domain, skip silently

    # Chain: Skeptical Reviewer (Phase 5) — deterministic health check
    reviewer = scripts_dir / "review-check.py"
    if reviewer.exists() and not args.check:
        try:
            subprocess.run([sys.executable, str(reviewer), "--profile", "content"], check=True, capture_output=True)
            print(f"[OK] chained: review-check.py --profile content (report -> wiki/context/review-report.md)")
        except subprocess.CalledProcessError as e:
            print(f"[WARN] review-check.py failed: {e.stderr.decode('utf-8', 'replace')[:200]}", file=sys.stderr)

    # Chain: build sqlite-vec semantic index (fastembed paraphrase-multilingual-MiniLM-L12-v2)
    vec_builder = scripts_dir / "build-vec-index.py"
    if vec_builder.exists():
        try:
            subprocess.run([sys.executable, str(vec_builder)], check=True, capture_output=True, timeout=300)
            print(f"[OK] chained: build-vec-index.py")
        except subprocess.TimeoutExpired:
            print(f"[WARN] build-vec-index.py timed out (>5min)", file=sys.stderr)
        except subprocess.CalledProcessError as e:
            print(f"[WARN] build-vec-index.py failed: {e.stderr.decode('utf-8', 'replace')[:200]}", file=sys.stderr)

    # Regenerate wiki/context/knowledge-graph.md from .wiki-graph.json
    graph_json = REPO_ROOT / ".wiki-graph.json"
    if graph_json.exists():
        try:
            import json as _json
            g = _json.loads(graph_json.read_text(encoding="utf-8"))
            s = g["stats"]
            lines = [
                "# Knowledge Graph (auto-generated)",
                "",
                f"_Generated: {g['generated_at']}_  •  _Source: `.wiki-graph.json` (regen by `scripts/gen-index.py`)_",
                "",
                "## Stats",
                "",
                f"- **Nodes**: {s['nodes']}",
                f"- **Edges**: {s['edges']}",
                f"- **Broken links**: {s['broken_links']} (run `python3 scripts/query-graph.py --broken`)",
                f"- **Orphans**: {s['orphans']} (run `python3 scripts/query-graph.py --orphans`)",
                "",
                "## Top Hubs (most-connected)",
                "",
            ]
            for h in s.get("hubs", [])[:10]:
                lines.append(f"- `{h['path']}` ({h['score']} edges)")
            lines += [
                "",
                "## Query CLI",
                "",
                "```bash",
                "python3 scripts/query-graph.py --neighbors wiki/entities/iot/mqtt-protocol.md",
                "python3 scripts/query-graph.py --orphans",
                "python3 scripts/query-graph.py --hubs",
                "python3 scripts/query-graph.py --broken",
                "python3 scripts/query-graph.py --cross-domain",
                "python3 scripts/query-graph.py --path FROM TO",
                "```",
                "",
            ]
            (CONTEXT_DIR / "knowledge-graph.md").write_text("\n".join(lines), encoding="utf-8")
            print(f"[OK] regenerated: wiki/context/knowledge-graph.md")
        except Exception as e:
            print(f"[WARN] knowledge-graph.md regen failed: {e}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
