"""Brain Bridge v0.2 — verify / recall / claim.

thin brain-side operations for the A-Conductor control plane (and any agent):
  verify — run repo gates bounded, structured JSON (read-only side effects:
           the gates themselves are the repo's canonical checks)
  recall — search the L1 memory ledger read-only; summaries re-redacted
           before leaving the brain (defense in depth)
  claim  — append a COLLAB claim row; ONLY after an entry-gate GO and
           idempotent per (topic, agent)
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

from .gate import entry_gate
from .state import parse_claims

SCHEMA = "awiki-conductor/v1"
REPO_ROOT = Path(__file__).resolve().parents[1]


class VerifyError(ValueError):
    """Unknown gate — fail closed instead of silently skipping."""


class ClaimConflict(RuntimeError):
    """Refused: gate NO-GO / missing COLLAB / topic already claimed."""


# canonical gate commands (name → argv); ALL read-only for the repo tree
GATE_COMMANDS: dict[str, list[str]] = {
    "registry": [sys.executable, "scripts/hooks/registry.py", "--check"],
    "scan": [sys.executable, "scripts/security/scan_repo.py", "--ci",
             "--baseline", "scripts/security/baseline.txt"],
    "health": [sys.executable, "scripts/health/wiki_health.py", "--baseline",
               "scripts/health/wiki-health-baseline.txt"],
}


def run_verify(repo_root: Path | None = None, gates: list[str] | None = None,
               timeout: float = 300) -> dict:
    root = Path(repo_root) if repo_root else REPO_ROOT
    names = gates or ["registry"]
    unknown = [g for g in names if g not in GATE_COMMANDS]
    if unknown:
        raise VerifyError(f"unknown gate(s): {unknown} — known: {sorted(GATE_COMMANDS)}")
    results = []
    for name in names:
        started = time.monotonic()
        try:
            proc = subprocess.run(
                GATE_COMMANDS[name], capture_output=True, text=True,
                encoding="utf-8", errors="replace", cwd=str(root),
                timeout=timeout or 0.001)
            passed = proc.returncode == 0
            detail = (proc.stderr or proc.stdout or "").strip().splitlines()
            detail = detail[-1][:200] if detail else "ok"
        except subprocess.TimeoutExpired:
            passed = False
            detail = f"timeout after {timeout}s"
        results.append({"gate": name, "passed": passed, "detail": detail,
                        "duration_s": round(time.monotonic() - started, 3)})
    return {"schema": SCHEMA, "results": results,
            "all_passed": all(r["passed"] for r in results)}


def recall(query: str, ledger: Path | None = None, limit: int = 10) -> list[dict]:
    root_ledger = REPO_ROOT / ".tmp" / "memory-ledger.jsonl"
    path = Path(ledger) if ledger else root_ledger
    if not query or not path.is_file():
        return []
    sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))
    import memory_ledger  # the L1 primitive — one engine, no duplicates
    import semantic_recall  # same BM25 engine the recall_on_prompt hook uses
    hits = semantic_recall.search(path, query, limit=limit)
    if not hits:  # small ledgers (<10) fall back to term-overlap in the hook
        hits = memory_ledger.MemoryLedger(path).search(query, limit=limit)
    out = []
    for h in hits:
        entry = dict(h)
        entry["summary"] = memory_ledger._redact(str(entry.get("summary", "")))
        out.append(entry)
    return out


def add_claim(repo_root: Path | None = None, topic: str = "",
              agent: str = "unknown", scope: str = "<scope>",
              branch: str = "<branch>") -> dict:
    root = Path(repo_root) if repo_root else Path.cwd()
    collab = root / "COLLAB.md"
    if not collab.is_file():
        raise ClaimConflict("COLLAB.md missing — claim requires the continuity table")

    # exact-slug ownership FIRST — a repeat claim by the SAME agent is
    # idempotent even though the gate flags the existing row as a conflict
    claims = parse_claims(collab)
    slug = topic.strip().lower()
    for c in claims:
        if c["chunk"].strip().lower() == slug:
            if c["agent"].strip().lower() == agent.strip().lower():
                return {"claimed": True, "already": True, "topic": topic}
            raise ClaimConflict(f"'{topic}' already claimed by {c['agent']!r}")

    verdict = entry_gate(root, topic=topic, agent=agent)
    if verdict["conflicts"]:
        raise ClaimConflict("conflict with live claim: " + "; ".join(verdict["conflicts"]))

    row = f"| {topic} | {agent} | {date.today().isoformat()} | {scope} | {branch} |\n"
    text = collab.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    # append into the claims table: after the last consecutive table row
    last_table = 0
    in_claims = False
    for i, line in enumerate(lines):
        if line.startswith("|") and "chunk/wo" in line.lower():
            in_claims = True
        if in_claims and line.strip().startswith("|"):
            last_table = i
    if last_table == 0:
        raise ClaimConflict("claims table not found in COLLAB.md")
    lines.insert(last_table + 1, row)
    collab.write_text("".join(lines), encoding="utf-8")
    return {"claimed": True, "already": False, "topic": topic,
            "claim_row": row.strip()}


# ── Slice 1: wiki search + graph navigation (A-Conductor Phase 4) ──────
# Thin wrappers over the brain's existing engines — query-rag.py (hybrid
# FTS5+vec RRF), search-wiki.py (FTS5 BM25), query-graph.py (neighbors/
# hubs). The bridge adds NO engine of its own (division of labor).

def _run_json(argv: list[str], timeout: float = 120) -> list[dict]:
    proc = subprocess.run(
        [sys.executable, *argv], capture_output=True, text=True,
        encoding="utf-8", errors="replace", cwd=str(REPO_ROOT), timeout=timeout)
    if proc.returncode != 0:
        raise RuntimeError(f"{' '.join(argv[:2])} failed: "
                           f"{(proc.stderr or proc.stdout).strip()[:200]}")
    return json.loads(proc.stdout or "[]")


def search_wiki(query: str, mode: str = "hybrid", limit: int = 8) -> dict:
    if mode not in ("fts", "hybrid"):
        raise VerifyError(f"unknown search mode {mode!r} (fts|hybrid)")
    if not query.strip():
        return {"schema": SCHEMA, "mode": mode, "hits": []}
    try:
        if mode == "hybrid":
            hits = _run_json(["scripts/wiki/query-rag.py", query,
                              "--limit", str(limit), "--json"], timeout=180)
        else:
            hits = _run_json(["scripts/wiki/search-wiki.py", query,
                              "--limit", str(limit), "--json"])
    except (RuntimeError, json.JSONDecodeError):
        if mode == "hybrid":
            # vector deps missing on this machine → deterministic downgrade
            # to plain FTS, reported honestly (never a silent empty answer)
            mode = "fts"
            hits = _run_json(["scripts/wiki/search-wiki.py", query,
                              "--limit", str(limit), "--json"])
        else:
            raise
    slim = [{"path": h.get("path"), "title": h.get("title"),
             "score": h.get("score"), "snippet": (h.get("snippet") or "")[:200]}
            for h in hits[:limit]]
    return {"schema": SCHEMA, "mode": mode, "query": query, "hits": slim}


def _load_graph() -> dict:
    graph_path = REPO_ROOT / ".wiki-graph.json"
    if not graph_path.is_file():
        return {"nodes": [], "edges": []}
    return json.loads(graph_path.read_text(encoding="utf-8"))


def related_pages(page: str, edge_type: str | None = None) -> dict:
    """Graph neighbors of one page (adjacency over .wiki-graph.json)."""
    graph = _load_graph()
    edges = graph.get("edges", [])
    want = page.replace("\\", "/").lstrip("./")
    neighbors: dict[str, dict] = {}
    for e in edges:
        if edge_type and e.get("type") != edge_type:
            continue
        src = (e.get("from") or "").replace("\\", "/")
        dst = (e.get("to") or "").replace("\\", "/")
        if src == want:
            key = dst
            rel = "outgoing"
        elif dst == want:
            key = src
            rel = "incoming"
        else:
            continue
        if key and not e.get("broken"):
            slot = neighbors.setdefault(key, {"page": key, "relations": set()})
            slot["relations"].add(f'{rel}:{e.get("type", "wikilink")}')
    out = [{"page": v["page"],
            "relations": sorted(v["relations"])} for v in neighbors.values()]
    out.sort(key=lambda n: -len(n["relations"]))
    return {"schema": SCHEMA, "page": want, "neighbors": out}


def graph_hubs(limit: int = 10, domain: str | None = None) -> dict:
    graph = _load_graph()
    if domain:
        dom_by_path = {n.get("path"): n.get("domain")
                       for n in graph.get("nodes", [])}
    degree: dict[str, int] = {}
    for e in graph.get("edges", []):
        if e.get("broken"):
            continue
        for end in (e.get("from"), e.get("to")):
            if end:
                degree[end] = degree.get(end, 0) + 1
    hubs = [{"path": p, "degree": d} for p, d in degree.items()
            if not domain or dom_by_path.get(p) == domain]
    hubs.sort(key=lambda h: -h["degree"])
    return {"schema": SCHEMA, "hubs": hubs[:limit]}
