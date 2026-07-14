"""Skills service for the Live Dashboard.

Reads skills-registry.json and answers filtered/queried views for the
"🧩 Skills" dashboard tab. Per-agent visibility uses the registry's
canonical_for_agent() logic — the dashboard only shows skills an agent can
actually invoke.

Caching: the registry is loaded lazily and reloaded when the file mtime
changes, so edits to skills-registry.json show up on the next request without
restarting the server.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, parse_qs

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from skills_registry import Registry  # noqa: E402

REGISTRY_FILE = REPO_ROOT / "skills-registry.json"
WALKTHROUGHS_FILE = REPO_ROOT / "scripts" / "live-dashboard" / "skill-walkthroughs.json"

# Known agents — used for the agent dropdown + skill_count per agent.
KNOWN_AGENTS = ["all", "claude", "codex", "zcode", "gemini", "antigravity",
                "hermes", "kilo", "cline", "cursor", "windsurf", "openclaw"]

# Fields exposed in list view (compact). Detail view returns everything.
LIST_FIELDS = (
    "name", "domain", "lifecycle_phase", "category", "invocation",
    "th_description", "when_to_use", "agents", "status", "path", "source",
)

_cache: dict[str, Any] = {"registry": None, "mtime": 0.0, "loaded": 0.0}

# Lifecycle phase order — used to compute "related skills" (prev/next phase).
PHASE_ORDER = ("define", "plan", "build", "verify", "review", "ship", "meta", "none")


def _is_installed(skill: dict[str, Any]) -> bool:
    """Whether the SKILL.md exists on disk for this skill.

    `source=repo` skills are checked under the repo. `external-installed`
    skills are always treated as installed (they exist on this machine).
    `external-system` skills (vendored snapshots) are checked under the repo.
    """
    src = skill.get("source")
    if src == "external-installed":
        return True
    if src == "external-system":
        # Vendored snapshot path — check existence.
        p = skill.get("path")
        if not p:
            return False
        return (REPO_ROOT / p).is_file()
    if src == "repo":
        p = skill.get("path")
        if not p:
            return False
        return (REPO_ROOT / p).is_file()
    return False


def _invocation_hint(skill: dict[str, Any]) -> str:
    """Best-effort copyable invocation string for the 📋 button.

    Source-of-truth priority:
      1. registry `invocation_hint` field (authoritative, batch-LLM-filled)
      2. heuristic fallback (slash command / script path / bare name)

    The heuristic covers skills that have not yet been batch-filled.
    """
    # Priority 1 — registry field (set by batch_thai.py --field invocation_hint).
    hint = skill.get("invocation_hint")
    if isinstance(hint, str) and hint.strip():
        return hint.strip()

    # Priority 2 — heuristic fallback.
    name = skill.get("name", "")
    # Slash-command skills (Telegram bot, A-Wiki core commands).
    if name.startswith("a-wiki-") or name in {"wiki", "search", "review", "spec", "plan", "build", "ship"}:
        return f"/{name}"
    # Script-backed skills with a known path → emit `python <path>`.
    path = skill.get("path") or ""
    if path.endswith(".py"):
        return f"python {path}"
    return name


def _related_skills(reg: Registry, skill: dict[str, Any], limit: int = 5) -> list[dict[str, Any]]:
    """Compute related skills: same phase first, then same domain.

    Returns compact list items (name + th_description + invocation).
    """
    name = skill.get("name")
    phase = skill.get("lifecycle_phase", "none")
    domains = skill.get("domain") or []
    if isinstance(domains, str):
        domains = [domains]

    candidates: list[tuple[int, dict[str, Any]]] = []  # (score, skill)
    for s in reg.skills:
        if s.get("status") != "canonical" or s.get("name") == name:
            continue
        s_phase = s.get("lifecycle_phase", "none")
        s_domains = s.get("domain") or []
        if isinstance(s_domains, str):
            s_domains = [s_domains]
        score = 0
        if phase != "none" and s_phase == phase:
            score += 3
        shared = set(domains) & set(s_domains)
        score += len(shared)
        if score > 0:
            candidates.append((score, s))
    candidates.sort(key=lambda kv: (-kv[0], kv[1].get("name", "")))
    out = []
    for _, s in candidates[:limit]:
        out.append({
            "name": s.get("name"),
            "th_description": s.get("th_description", ""),
            "invocation": s.get("invocation", "manual"),
            "phase": s.get("lifecycle_phase", "none"),
            "domains": s.get("domain", []),
            "installed": _is_installed(s),
        })
    return out


def _load_registry() -> Registry:
    """Lazily load + cache the registry; reload when file mtime changes."""
    try:
        mtime = REGISTRY_FILE.stat().st_mtime
    except OSError:
        mtime = 0.0
    now = time.time()
    if _cache["registry"] is None or mtime != _cache["mtime"]:
        try:
            _cache["registry"] = Registry.load(REGISTRY_FILE)
            _cache["mtime"] = mtime
            _cache["loaded"] = now
        except Exception:
            # Keep last good cache if reload fails — never crash the server.
            if _cache["registry"] is None:
                raise
    return _cache["registry"]


def _skill_list_item(skill: dict[str, Any]) -> dict[str, Any]:
    """Compact view of a skill for the list endpoint."""
    item = {k: skill.get(k) for k in LIST_FIELDS}
    item["installed"] = _is_installed(skill)
    item["invocation_hint"] = _invocation_hint(skill)
    return item


def _matches_query(skill: dict[str, Any], q: str) -> bool:
    """Case-insensitive substring match across name + th_description + when_to_use."""
    if not q:
        return True
    q_lower = q.lower()
    haystack = " ".join(
        str(skill.get(k, "")) for k in ("name", "th_description", "when_to_use")
    ).lower()
    return q_lower in haystack


def _stats(skills: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate counts for filter chips in the UI."""
    by_domain: dict[str, int] = {}
    by_invocation: dict[str, int] = {}
    by_agent: dict[str, int] = {}
    by_category: dict[str, int] = {}
    has_thai = 0
    for s in skills:
        domains = s.get("domain") or []
        if isinstance(domains, str):
            domains = [domains]
        for d in domains:
            by_domain[d] = by_domain.get(d, 0) + 1
        inv = s.get("invocation") or "manual"
        by_invocation[inv] = by_invocation.get(inv, 0) + 1
        agents = s.get("agents") or []
        if "all" in agents:
            for a in KNOWN_AGENTS:
                if a != "all":
                    by_agent[a] = by_agent.get(a, 0) + 1
        else:
            for a in agents:
                by_agent[a] = by_agent.get(a, 0) + 1
        cat = s.get("category") or "uncategorized"
        by_category[cat] = by_category.get(cat, 0) + 1
        if s.get("th_description"):
            has_thai += 1
    return {
        "total": len(skills),
        "by_domain": dict(sorted(by_domain.items(), key=lambda kv: -kv[1])),
        "by_invocation": by_invocation,
        "by_agent": dict(sorted(by_agent.items(), key=lambda kv: -kv[1])),
        "by_category": dict(sorted(by_category.items(), key=lambda kv: -kv[1])),
        "has_thai": has_thai,
    }


def list_skills(query_string: str = "") -> dict[str, Any]:
    """GET /api/skills — filtered list view.

    Query params:
      agent=<name>       — only skills visible to that agent (uses canonical_for_agent)
      invocation=auto|manual|both
      domain=<d>         — domain filter (matches any of the skill's domains)
      category=<c>       — category filter (e.g. 'subagent', 'skill'); matches
                           the registry's 'category' field. Uncategorised skills
                           report category='uncategorized' for filter purposes.
      q=<text>           — substring search across name + th_description + when_to_use
      limit=<n>          — cap results (default 500)
    """
    params = parse_qs(query_string)
    agent = (params.get("agent", ["all"])[0]).lower()
    invocation = params.get("invocation", [None])[0]
    domain = params.get("domain", [None])[0]
    category = params.get("category", [None])[0]
    installed_only = params.get("installed", ["0"])[0] in ("1", "true", "yes")
    q = params.get("q", [""])[0]
    try:
        limit = int(params.get("limit", ["500"])[0])
    except ValueError:
        limit = 500

    reg = _load_registry()

    # Per-agent visibility: canonical_for_agent already handles the "all" list.
    if agent and agent != "all":
        allowed_names = {s["name"] for s in reg.canonical_for_agent(agent)}
        skills = [s for s in reg.skills if s.get("name") in allowed_names]
    else:
        skills = [s for s in reg.skills if s.get("status") == "canonical"]

    # Apply filters
    if invocation:
        skills = [s for s in skills if (s.get("invocation") or "manual") == invocation]
    if domain:
        skills = [
            s for s in skills
            if domain in (s.get("domain") if isinstance(s.get("domain"), list)
                          else [s.get("domain")] if s.get("domain") else [])
        ]
    if category:
        # Normalize missing category to 'uncategorized' so category=uncategorized
        # still matches skills without an explicit category field.
        skills = [s for s in skills if (s.get("category") or "uncategorized") == category]
    if installed_only:
        skills = [s for s in skills if _is_installed(s)]
    skills = [s for s in skills if _matches_query(s, q)]

    # Sort: has Thai first (most useful), then alphabetical
    skills.sort(key=lambda s: (not bool(s.get("th_description")), s.get("name", "")))

    items = [_skill_list_item(s) for s in skills[:limit]]
    return {
        "skills": items,
        "count": len(items),
        "total_matched": len(skills),
        "filters": {
            "agent": agent, "invocation": invocation, "domain": domain,
            "category": category, "installed": installed_only, "q": q,
        },
        "stats": _stats(skills),
        "agents": KNOWN_AGENTS,
        "loaded_at": _cache["loaded"],
    }


def get_skill(name: str) -> dict[str, Any] | None:
    """GET /api/skills/<name> — full detail for one skill.

    Augments the raw registry entry with:
      - installed: bool — whether SKILL.md exists on disk
      - invocation_hint: str — copyable command for the 📋 button
      - related: list — up to 5 skills sharing phase/domain (with th_description)
    """
    reg = _load_registry()
    skill = reg.get(name)
    if skill is None:
        return None
    # Copy so we don't mutate the cached registry entry.
    out = dict(skill)
    out["installed"] = _is_installed(skill)
    out["invocation_hint"] = _invocation_hint(skill)
    out["related"] = _related_skills(reg, skill)
    out["history"] = skill_history(name)
    return out


def agent_overview() -> dict[str, Any]:
    """GET /api/skills/agents — per-agent skill counts + which agents exist."""
    reg = _load_registry()
    canonical = [s for s in reg.skills if s.get("status") == "canonical"]
    counts = {}
    for agent in KNOWN_AGENTS:
        if agent == "all":
            counts[agent] = len(canonical)
        else:
            counts[agent] = len(reg.canonical_for_agent(agent))
    return {
        "agents": KNOWN_AGENTS,
        "skill_counts": counts,
        "total_canonical": len(canonical),
    }


# ---------------------------------------------------------------------------
# Coverage stats — powers the "📊 Coverage" dashboard tab
# ---------------------------------------------------------------------------

# Fields whose coverage we track. Each must be an optional v2 field; coverage
# is the fraction of canonical skills that have it populated.
_COVERAGE_FIELDS = ("th_description", "when_to_use", "examples",
                    "process_steps", "invocation_hint", "invocation")


def _skill_has(skill: dict[str, Any], field: str) -> bool:
    """True if the skill has a non-empty value for the field."""
    v = skill.get(field)
    if v is None:
        return False
    if isinstance(v, str):
        return bool(v.strip())
    if isinstance(v, list):
        return len(v) > 0
    return True


def coverage_stats(compare: str | None = None) -> dict[str, Any]:
    """GET /api/coverage — coverage metrics for the Coverage tab.

    Returns overall %, broken down by domain / agent / phase, plus lists of
    skills still missing each tracked field (for quick-fill UI).

    If compare="agentA,agentB" is given, also returns a `diff` object with:
      - only_a: skills visible to A but not B (names)
      - only_b: skills visible to B but not A (names)
      - shared: skills visible to both
    """
    reg = _load_registry()
    skills = [s for s in reg.skills if s.get("status") == "canonical"]
    total = len(skills)
    if total == 0:
        return {"overall": {}, "by_domain": {}, "by_agent": {}, "by_phase": {},
                "missing": {}, "total": 0}

    def _pct(n: int) -> float:
        return round(n * 100.0 / total, 1)

    # Overall
    overall: dict[str, float] = {}
    missing: dict[str, list[str]] = {}
    for field in _COVERAGE_FIELDS:
        n_have = sum(1 for s in skills if _skill_has(s, field))
        overall[field] = _pct(n_have)
        miss_list = [s["name"] for s in skills if not _skill_has(s, field)]
        # Keep it short — UI shows top 10 with a "see all" hint.
        missing[field] = miss_list[:50]

    # By domain
    by_domain: dict[str, dict[str, float]] = {}
    domain_totals: dict[str, int] = {}
    for s in skills:
        domains = s.get("domain") or []
        if isinstance(domains, str):
            domains = [domains]
        for d in domains:
            domain_totals[d] = domain_totals.get(d, 0) + 1
    for d, d_total in domain_totals.items():
        bucket: dict[str, float] = {}
        for field in _COVERAGE_FIELDS:
            n_have = sum(
                1 for s in skills
                if d in (s.get("domain") if isinstance(s.get("domain"), list)
                         else [s.get("domain")] if s.get("domain") else [])
                and _skill_has(s, field)
            )
            bucket[field] = round(n_have * 100.0 / d_total, 1) if d_total else 0.0
        by_domain[d] = bucket

    # By agent (canonical_for_agent gives the per-agent view)
    by_agent: dict[str, dict[str, float]] = {}
    for agent in KNOWN_AGENTS:
        if agent == "all":
            view = skills
        else:
            allowed = {s["name"] for s in reg.canonical_for_agent(agent)}
            view = [s for s in skills if s["name"] in allowed]
        if not view:
            continue
        bucket = {}
        for field in _COVERAGE_FIELDS:
            n_have = sum(1 for s in view if _skill_has(s, field))
            bucket[field] = round(n_have * 100.0 / len(view), 1)
        by_agent[agent] = bucket

    # By lifecycle phase
    by_phase: dict[str, dict[str, float]] = {}
    phase_totals: dict[str, int] = {}
    for s in skills:
        p = s.get("lifecycle_phase") or "none"
        phase_totals[p] = phase_totals.get(p, 0) + 1
    for p, p_total in phase_totals.items():
        view = [s for s in skills if (s.get("lifecycle_phase") or "none") == p]
        bucket = {}
        for field in _COVERAGE_FIELDS:
            n_have = sum(1 for s in view if _skill_has(s, field))
            bucket[field] = round(n_have * 100.0 / p_total, 1) if p_total else 0.0
        by_phase[p] = bucket

    result = {
        "overall": overall,
        "by_domain": by_domain,
        "by_agent": by_agent,
        "by_phase": by_phase,
        "missing": missing,
        "total": total,
        "fields": list(_COVERAGE_FIELDS),
    }

    # Agent comparison: ?compare=claude,zcode → diff of visible skill sets.
    if compare:
        parts = [p.strip().lower() for p in compare.split(",") if p.strip()]
        if len(parts) >= 2:
            a, b = parts[0], parts[1]
            set_a = {s["name"] for s in reg.canonical_for_agent(a)} if a != "all" else {s["name"] for s in skills}
            set_b = {s["name"] for s in reg.canonical_for_agent(b)} if b != "all" else {s["name"] for s in skills}
            result["diff"] = {
                "agent_a": a,
                "agent_b": b,
                "only_a": sorted(set_a - set_b)[:50],
                "only_b": sorted(set_b - set_a)[:50],
                "shared": len(set_a & set_b),
                "only_a_count": len(set_a - set_b),
                "only_b_count": len(set_b - set_a),
            }

    return result


# ---------------------------------------------------------------------------
# Skill dependency graph — powers the "🧬 Graph" toggle in the Skills tab
# ---------------------------------------------------------------------------

# Domain → color mapping (mirrors skillsDomainColor() in the HTML).
_DOMAIN_COLORS: dict[str, str] = {
    "code": "#60a5fa", "debug": "#f87171", "design": "#a78bfa", "ux-ui": "#f472b6",
    "trader": "#fbbf24", "medical": "#34d399", "business": "#22d3ee", "data": "#60a5fa",
    "engineering": "#5eead4", "security": "#f87171", "ai-ops": "#a78bfa",
    "productivity": "#fbbf24", "wiki": "#34d399", "iot": "#94a3b8", "env": "#34d399",
    "pharmacy": "#34d399", "thai": "#f472b6", "logistics": "#fb923c", "network": "#22d3ee",
    "media": "#c084fc", "document": "#e2e8f0", "sre": "#f87171",
}
_DOMAIN_COLOR_DEFAULT = "#94a3b8"


def _domain_color(domains: list[str] | str) -> str:
    if isinstance(domains, str):
        domains = [domains]
    for d in domains:
        if d in _DOMAIN_COLORS:
            return _DOMAIN_COLORS[d]
    return _DOMAIN_COLOR_DEFAULT


def skill_graph(
    domain: str | None = None,
    phase: str | None = None,
    all_skills: bool = False,
    limit: int = 500,
) -> dict[str, Any]:
    """GET /api/skills/graph — build a skill relationship graph for vis-network.

    Nodes are canonical skills. Edges represent meaningful relationships:
      - Same lifecycle_phase (phase != "none") → weight 3
      - 2+ shared domains → weight 2
      - 1 shared domain → weight 1 (only included if also same phase → combined 4)

    By default (all_skills=False) only skills with lifecycle_phase != "none" are
    included, producing a focused graph of ~40 skills. Pass all_skills=True to
    include all canonical skills (slower but complete).

    Optional domain/phase filters narrow the node set further.
    """
    reg = _load_registry()
    skills = [s for s in reg.skills if s.get("status") == "canonical"]

    # Default: exclude phase=none (they have no lifecycle relationships).
    if not all_skills:
        skills = [s for s in skills if (s.get("lifecycle_phase") or "none") != "none"]

    # Optional filters.
    if domain:
        skills = [
            s for s in skills
            if domain in (s.get("domain") if isinstance(s.get("domain"), list)
                          else [s.get("domain")] if s.get("domain") else [])
        ]
    if phase:
        skills = [s for s in skills if (s.get("lifecycle_phase") or "none") == phase]

    skills = skills[:limit]

    # Build nodes.
    nodes: list[dict[str, Any]] = []
    for s in skills:
        name = s.get("name", "")
        domains = s.get("domain") or []
        if isinstance(domains, str):
            domains = [domains]
        p = s.get("lifecycle_phase") or "none"
        color = _domain_color(domains)
        nodes.append({
            "id": name,
            "label": name,
            "title": s.get("th_description", "")[:80] or name,
            "domain": domains,
            "phase": p,
            "color": color,
            "installed": _is_installed(s),
        })

    # Build edges: pairwise scoring (only weight >= 2 kept).
    edges: list[dict[str, Any]] = []
    n = len(skills)
    for i in range(n):
        a = skills[i]
        a_phase = a.get("lifecycle_phase") or "none"
        a_domains = a.get("domain") or []
        if isinstance(a_domains, str):
            a_domains = [a_domains]
        a_name = a.get("name", "")
        for j in range(i + 1, n):
            b = skills[j]
            b_phase = b.get("lifecycle_phase") or "none"
            b_domains = b.get("domain") or []
            if isinstance(b_domains, str):
                b_domains = [b_domains]
            b_name = b.get("name", "")
            weight = 0
            if a_phase != "none" and a_phase == b_phase:
                weight += 3
            shared = len(set(a_domains) & set(b_domains))
            if shared >= 2:
                weight += 2
            elif shared == 1:
                weight += 1
            if weight >= 2:
                edges.append({
                    "from": a_name,
                    "to": b_name,
                    "weight": weight,
                    "id": f"{a_name}→{b_name}",
                })

    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {"nodes": len(nodes), "edges": len(edges)},
        "filters": {"domain": domain, "phase": phase, "all": all_skills},
    }


# ---------------------------------------------------------------------------
# Walkthrough difficulty scoring — auto-score 0-100 from step count + skill complexity
# ---------------------------------------------------------------------------

# Phases/domains that add complexity when present in a walkthrough.
_HARD_PHASES = frozenset({"review", "ship", "verify"})
_HARD_DOMAINS = frozenset({"security", "sre", "debug"})


def walkthrough_difficulty(flow: dict[str, Any]) -> dict[str, Any]:
    """Score a walkthrough flow's difficulty from 0-100.

    Factors (max scores in parens):
      - step_count (0-30): 1 step=5pts, 8+ steps=30pts (linear)
      - skill complexity (0-25): hard phases/domains = +5 each (max 25)
      - process_steps richness (0-20): skills with 4+ process_steps = +3 each (max 20)
      - phase diversity (0-25): distinct phases = +5 each (max 25)

    Returns: {score, level, factors}.
    """
    steps = flow.get("steps", []) if isinstance(flow, dict) else []
    reg = _load_registry()

    # Factor 1: step count (0-30)
    n = len(steps)
    step_score = min(30, max(0, n * 5)) if n > 0 else 0

    # Factor 2: skill complexity — hard phases/domains (0-25)
    hard_count = 0
    phases_seen: set[str] = set()
    process_rich_count = 0
    for step in steps:
        skill_name = step.get("skill", "") if isinstance(step, dict) else ""
        skill = reg.get(skill_name) if skill_name else None
        if not skill:
            continue
        p = skill.get("lifecycle_phase", "none")
        domains = skill.get("domain") or []
        if isinstance(domains, str):
            domains = [domains]
        if p in _HARD_PHASES or any(d in _HARD_DOMAINS for d in domains):
            hard_count += 1
        if p != "none":
            phases_seen.add(p)
        ps = skill.get("process_steps") or []
        if isinstance(ps, list) and len(ps) >= 4:
            process_rich_count += 1

    complexity_score = min(25, hard_count * 5)

    # Factor 3: process_steps richness (0-20)
    process_score = min(20, process_rich_count * 3)

    # Factor 4: phase diversity (0-25)
    diversity_score = min(25, len(phases_seen) * 5)

    score = step_score + complexity_score + process_score + diversity_score
    score = max(0, min(100, score))
    level = "เริ่มต้น" if score <= 33 else "ปานกลาง" if score <= 66 else "ขั้นสูง"

    return {
        "score": score,
        "level": level,
        "factors": {
            "step_count": step_score,
            "skill_complexity": complexity_score,
            "process_steps_richness": process_score,
            "phase_diversity": diversity_score,
            "steps": n,
            "hard_skills": hard_count,
            "distinct_phases": len(phases_seen),
        },
    }


__all__ = [
    "list_skills", "get_skill", "agent_overview", "coverage_stats",
    "skill_graph", "walkthrough_difficulty", "recommend_skills",
    "skill_history", "KNOWN_AGENTS",
]


# ---------------------------------------------------------------------------
# Skill versioning + git history — display-only (no registry schema change)
# ---------------------------------------------------------------------------

import subprocess  # noqa: E402 — late import, isolated to this function


def skill_history(name: str) -> dict[str, Any]:
    """Get version + last-modified info for a skill via git log of its SKILL.md.

    Uses subprocess with arg list (never shell=True) for security.
    Returns: {version, last_commit_date, last_commit_hash, commit_count}.
    Fails gracefully (returns empty dict) if git fails or path missing.
    """
    reg = _load_registry()
    skill = reg.get(name)
    if not skill:
        return {}

    version = skill.get("version", "") or ""
    path = skill.get("path", "")
    if not path:
        return {"version": version, "last_commit_date": "", "last_commit_hash": "", "commit_count": 0}

    skill_file = REPO_ROOT / path
    if not skill_file.is_file():
        return {"version": version, "last_commit_date": "", "last_commit_hash": "", "commit_count": 0}

    result: dict[str, Any] = {
        "version": version,
        "last_commit_date": "",
        "last_commit_hash": "",
        "commit_count": 0,
    }
    try:
        # Last commit info: git log -1 --format=%cd|%h --date=short -- <path>
        proc = subprocess.run(
            ["git", "log", "-1", "--format=%cd|%h", "--date=short", "--", path],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=5, cwd=str(REPO_ROOT),
        )
        if proc.returncode == 0 and proc.stdout.strip():
            parts = proc.stdout.strip().split("|", 1)
            if len(parts) == 2:
                result["last_commit_date"] = parts[0].strip()
                result["last_commit_hash"] = parts[1].strip()

        # Commit count: git rev-list --count HEAD -- <path>
        proc2 = subprocess.run(
            ["git", "rev-list", "--count", "HEAD", "--", path],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=5, cwd=str(REPO_ROOT),
        )
        if proc2.returncode == 0 and proc2.stdout.strip().isdigit():
            result["commit_count"] = int(proc2.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        # Git not available or timed out — return what we have (version only).
        pass
    return result


# ---------------------------------------------------------------------------
# Skill recommender — text-based multi-field scoring with match reasons
# ---------------------------------------------------------------------------

def recommend_skills(query: str, limit: int = 5) -> dict[str, Any]:
    """Recommend skills based on a text query (natural language OK).

    Scoring per matched field:
      - th_description substring → 3 pts
      - when_to_use substring → 2 pts
      - name substring → 2 pts
      - examples[].how substring → 1 pt
    Boosts:
      - has process_steps → +2
      - has invocation_hint → +1

    Returns top N skills with score + match_reason (which fields matched).
    Empty query → empty results.
    """
    query = (query or "").strip().lower()
    if not query:
        return {"query": query, "results": [], "total_matched": 0, "walkthroughs": []}

    reg = _load_registry()
    skills = [s for s in reg.skills if s.get("status") == "canonical"]

    results: list[dict[str, Any]] = []
    for s in skills:
        score = 0
        reasons: list[str] = []

        th_desc = (s.get("th_description") or "").lower()
        when = (s.get("when_to_use") or "").lower()
        name = (s.get("name") or "").lower()

        if query in th_desc:
            score += 3
            reasons.append("ตรงคำอธิบายไทย")
        if query in when:
            score += 2
            reasons.append("ตรง 'ใช้เมื่อไหร่'")
        if query in name:
            score += 2
            reasons.append("ตรงชื่อ skill")
        # examples[].how
        for ex in (s.get("examples") or []):
            if isinstance(ex, dict):
                how = (ex.get("how") or "").lower()
                if query in how:
                    score += 1
                    reasons.append("ตรงตัวอย่าง")
                    break  # only count once

        if score == 0:
            continue

        # Boosts.
        if s.get("process_steps"):
            score += 2
        if s.get("invocation_hint"):
            score += 1

        results.append({
            "name": s.get("name"),
            "score": score,
            "match_reason": ", ".join(reasons) or "partial match",
            "th_description": (s.get("th_description") or "")[:100],
            "invocation_hint": _invocation_hint(s),
            "domain": s.get("domain") or [],
            "lifecycle_phase": s.get("lifecycle_phase", "none"),
        })

    results.sort(key=lambda r: (-r["score"], r["name"]))

    # Also match walkthroughs (multi-skill flows) by title/summary.
    walkthrough_matches: list[dict[str, Any]] = []
    try:
        walk_data = _load_walkthroughs_for_recommend()
        for wid, flow in walk_data.items():
            if wid == "_meta":
                continue
            title = (flow.get("title_th") or "").lower()
            summary = (flow.get("summary_th") or "").lower()
            fid = wid.lower()
            w_score = 0
            if query in title:
                w_score += 5
            if query in summary:
                w_score += 3
            if query in fid:
                w_score += 4  # id match (English) is strong signal for Thai titles
            if w_score > 0:
                walkthrough_matches.append({
                    "id": wid,
                    "title_th": flow.get("title_th", wid),
                    "score": w_score,
                    "step_count": len(flow.get("steps", [])),
                    "match_reason": "ตรงชื่อ/สรุป flow",
                })
        walkthrough_matches.sort(key=lambda w: -w["score"])
    except Exception:
        pass  # walk file missing — return empty list

    return {
        "query": query,
        "results": results[:limit],
        "total_matched": len(results),
        "walkthroughs": walkthrough_matches[:3],
    }


def _load_walkthroughs_for_recommend() -> dict[str, Any]:
    """Load skill-walkthroughs.json for the recommender. Cached by mtime."""
    if not WALKTHROUGHS_FILE.is_file():
        return {}
    try:
        mtime = WALKTHROUGHS_FILE.stat().st_mtime
    except OSError:
        mtime = 0.0
    cache = _cache.get("walkthroughs")
    cache_mtime = _cache.get("walkthroughs_mtime", 0.0)
    if cache is None or mtime != cache_mtime:
        try:
            with open(WALKTHROUGHS_FILE, "r", encoding="utf-8") as f:
                _cache["walkthroughs"] = json.load(f)
            _cache["walkthroughs_mtime"] = mtime
        except (json.JSONDecodeError, OSError):
            return {}
    return _cache.get("walkthroughs") or {}
