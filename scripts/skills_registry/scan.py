"""Bootstrap scanner — walk all skill surfaces and emit a draft registry.

Surfaces scanned (per the architecture audit):
  - skills/                     (repo canonical, excl. _upstream/, deprecated/)
  - agent-skills/               (Iron-Law variants)
  - ~/.claude/skills/           (external-installed)
  - ~/.codex/skills/.system/    (external-system)
  - .kilo/skills/               (external-installed, Kilo-only)

The scanner parses SKILL.md frontmatter WITHOUT PyYAML (repo convention — see
check_harness_routing.py / gen-index.py) and auto-classifies domain +
lifecycle_phase via filename/path heuristics.  The output is a DRAFT for human
review; it is not authoritative until committed to skills-registry.json.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from . import (
    SCHEMA_VERSION,
    VALID_DOMAINS,
    VALID_LIFECYCLE_PHASES,
    VALID_SOURCES,
)


# ---------------------------------------------------------------------------
# Frontmatter parsing (manual — no PyYAML dependency, per repo convention)
# ---------------------------------------------------------------------------

def parse_frontmatter(content: str) -> dict[str, Any]:
    """Parse YAML frontmatter from a markdown file into a dict.

    Handles scalar values and inline lists ``[a, b]``. Good enough for
    SKILL.md frontmatter (which is intentionally simple).  Mirrors the
    pattern in scripts/gen-index.py.
    """
    if not content.startswith("---"):
        return {}
    end = content.find("\n---", 3)
    if end < 0:
        return {}
    fm = content[3:end]
    out: dict[str, Any] = {}
    for line in fm.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        if not key:
            continue
        # inline list
        if val.startswith("[") and val.endswith("]"):
            items = [v.strip().strip("'\"") for v in val[1:-1].split(",") if v.strip()]
            out[key] = items
        else:
            # strip quotes
            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                val = val[1:-1]
            out[key] = val
    return out


# ---------------------------------------------------------------------------
# Classification heuristics (Goal #5 domains + lifecycle phases)
# ---------------------------------------------------------------------------

# Order matters: first match wins. More specific prefixes first.
_DOMAIN_RULES: list[tuple[str, tuple[str, ...]]] = [
    # Explicit filename/path prefixes
    ("thai", ("thai-",)),
    ("medical", ("healthcare-", "hipaa", "openmed", "pharmacy-")),
    ("pharmacy", ("pharmacy",)),
    ("trader", ("ito-", "prediction-market", "defi-", "llm-trading", "evm-", "nodejs-keccak")),
    ("security", ("security", "gateguard", "safety-guard", "defi-amm", "llm-trading-agent-security")),
    ("design", ("frontend-design", "design-system", "canvas-design", "liquid-glass", "theme-factory", "brand-")),
    ("ux-ui", ("frontend-a11y", "accessibility", "make-interfaces", "ui-demo", "ui-to-vue")),
    ("wiki", ("wiki-", "ingest-source", "lint-wiki", "obsidian", "render-html", "export-notebooklm", "ask-notebooklm")),
    ("ai-ops", ("agent-", "autonomous-", "continuous-", "mcp-", "delegate-", "swarm", "model-", "eval-harness", "benchmark", "cost-", "token-", "context-budget", "strategic-compact", "prompt-optimizer")),
    ("productivity", ("management-talk", "post-mortem", "planning-", "plan-", "blueprint", "doc-coauthoring", "article-writing")),
    ("env", ("env-", "energy-procurement")),
    ("iot", ("mqtt", "iot-")),
    ("data", ("data-", "recsys-", "clickhouse", "postgres", "mysql", "redis", "prisma", "database")),
    # --- refined sub-domains (split out of the former "code" catch-all) ---
    ("business", ("market-research", "marketing-campaign", "seo", "lead-", "investor-", "email-ops", "internal-comms", "customer-billing", "finance-billing", "finance")),
    ("logistics", ("inventory", "production-scheduling", "quality-nonconformance", "returns-reverse", "logistics-", "carrier-", "customs-trade")),
    ("network", ("network-", "netmiko", "cisco-ios", "homelab-network", "homelab-pihole", "homelab-vlan", "homelab-wireguard")),
    ("media", ("imagegen", "fal-ai", "video-editing", "video-", "manim", "remotion", "slack-gif", "algorithmic-art", "pixellab", "videodb", "motion-")),
    ("document", ("docx", "/pdf", "pptx", "xlsx", "excel-generator", "word-generator", "assessment-generator", "nutrient-document", "frontend-slides", "visa-doc-translate")),
    ("sre", ("observability", "canary-watch", "production-audit", "ci-cd", "deployment-patterns", "opens")),
    # scientific / research
    ("data", ("gget", "pubmed-database", "uspto-database", "scholar-evaluation", "literature-review", "mle-workflow", "recsys-")),
    # verification / quality (lifecycle verify phase, distinct from language-testing)
    ("debug", ("verification-loop", "verify-before-done", "scrutinize", "browser-qa")),
]

# Keywords that map a skill to a domain regardless of prefix.
_DOMAIN_KEYWORDS: dict[str, tuple[str, ...]] = {
    "debug": ("debug", "root-cause"),
    "code": ("-testing", "-tdd", "-patterns", "-verification", "tdd-workflow", "e2e-testing", "webapp-testing", "browser-qa", "browser-testing"),
    "engineering": ("architecture", "hexagonal", "latency-critical", "latency", "production-"),
}


def classify_domain(name: str, path: str) -> list[str]:
    """Heuristically tag a skill with one or more domains by name + path.

    Returns a sorted unique list.  Falls back to ['code'] for dev-flavored
    skills and [] for anything unclassifiable (reviewer fills it in).
    """
    domains: set[str] = set()
    haystack = f"{name} {path}".lower()

    for domain, prefixes in _DOMAIN_RULES:
        if any(haystack.startswith(p) or f"/{p}" in haystack for p in prefixes):
            domains.add(domain)

    for domain, keywords in _DOMAIN_KEYWORDS.items():
        if any(kw in haystack for kw in keywords):
            domains.add(domain)

    # Lifecycle build/verify/review/ship dirs imply engineering/code.
    if "/engineering-lifecycle/" in path.lower():
        domains.add("engineering")
        domains.add("code")

    # Default: skills under skills/ecosystem or skills/claude-code that we
    # couldn't classify are usually code/dev tooling.
    if not domains and any(seg in path.lower() for seg in ("skills/ecosystem/", "skills/claude-code/", "agent-skills/")):
        domains.add("code")

    # Filter to valid domains only (safety).
    domains = {d for d in domains if d in VALID_DOMAINS}
    return sorted(domains) if domains else ["code"]  # never empty


_LIFECYCLE_DIR_MAP: dict[str, str] = {
    "define": "define",
    "plan": "plan",
    "build": "build",
    "verify": "verify",
    "review": "review",
    "ship": "ship",
}


def classify_lifecycle(name: str, path: str) -> str:
    """Tag a skill with its lifecycle phase by path, or 'none'."""
    low = path.lower()
    if "/engineering-lifecycle/" in low:
        for phase in _LIFECYCLE_DIR_MAP:
            if f"/{phase}/" in low:
                return phase
        return "meta"  # router itself lives at the root of engineering-lifecycle/
    # A-Wiki Iron-Law variants.
    if "agent-skills/engineering/" in low:
        if "debug" in name.lower():
            return "verify"
        if "scrutinize" in name.lower() or "post-mortem" in name.lower():
            return "review"
    if "agent-skills/productivity/" in low:
        return "meta"
    return "none"


# ---------------------------------------------------------------------------
# Surface walking
# ---------------------------------------------------------------------------

def find_skill_files(repo_root: Path) -> list[dict[str, Any]]:
    """Walk all known surfaces and return raw skill descriptors.

    Each descriptor has: name, path (relative or absolute), source, frontmatter.
    De-duplicates by name, preferring repo source over external.
    """
    repo_root = Path(repo_root)
    raw: list[dict[str, Any]] = []

    # --- repo surfaces ---
    for source, base_rel in (
        ("repo", "skills"),
        ("repo", "agent-skills"),
    ):
        base = repo_root / base_rel
        if not base.is_dir():
            continue
        for skill_md in base.rglob("SKILL.md"):
            rel = skill_md.relative_to(repo_root).as_posix()
            # Skip vendored mirrors, deprecation graveyards, and skill-local
            # artifact subdirs (examples/, references/) — these hold runnable
            # demos / notebooks / external materials, never standalone skills.
            # Documented in docs/protocols/skill-frontmatter-schema.md §Skill
            # folder layout convention.
            low = rel.lower()
            if ("/_upstream/" in low or "/deprecated/" in low or "/.git/" in low
                    or "/examples/" in low or "/references/" in low):
                continue
            fm = parse_frontmatter(skill_md.read_text(encoding="utf-8", errors="replace"))
            name = fm.get("name") or skill_md.parent.name
            raw.append({
                "name": str(name),
                "path": rel,
                "source": source,
                "frontmatter": fm,
            })

    # --- external surfaces (machine-local) ---
    # SECURITY: store paths as portable ~/... or %HOME%/... so the public
    # registry never contains a personal machine path (Iron Laws + Storage
    # Decision Rule). The actual file is resolved at runtime via Path.home().
    home = Path.home()
    for source, base, home_rel in (
        ("external-installed", home / ".claude" / "skills", "~/.claude/skills"),
        ("external-installed", home / ".kilo" / "skills", "~/.kilo/skills"),
        ("external-installed", home / ".agents" / "skills", "~/.agents/skills"),
        ("external-system", home / ".codex" / "skills" / ".system", "~/.codex/skills/.system"),
    ):
        if not base.is_dir():
            continue
        for skill_md in base.rglob("SKILL.md"):
            fm = parse_frontmatter(skill_md.read_text(encoding="utf-8", errors="replace"))
            name = fm.get("name") or skill_md.parent.name
            # Portable path: <home-rel>/<subpath under base>
            rel_under_base = skill_md.relative_to(base).as_posix()
            portable_path = f"{home_rel}/{rel_under_base}"
            raw.append({
                "name": str(name),
                "path": portable_path,
                "source": source,
                "frontmatter": fm,
            })

    # De-duplicate by name: repo > external-system > external-installed.
    source_priority = {"repo": 0, "external-system": 1, "external-installed": 2}
    by_name: dict[str, dict[str, Any]] = {}
    for item in raw:
        name = item["name"]
        if name not in by_name or source_priority[item["source"]] < source_priority[by_name[name]["source"]]:
            by_name[name] = item
    return list(by_name.values())


# ---------------------------------------------------------------------------
# Draft registry emission
# ---------------------------------------------------------------------------

def build_draft_registry(repo_root: Path, generated_at: str = "DRAFT") -> dict[str, Any]:
    """Produce a draft skills-registry.json dict for human review."""
    skills: list[dict[str, Any]] = []
    for item in find_skill_files(repo_root):
        fm = item["frontmatter"]
        name = item["name"]
        path = item["path"]
        skills.append({
            "name": name,
            "aliases": fm.get("aliases", []),
            "domain": classify_domain(name, path),
            "lifecycle_phase": classify_lifecycle(name, path),
            "category": _infer_category(path),
            "source": item["source"],
            "path": path,
            "agents": ["all"],
            "version": fm.get("version", ""),
            "status": "canonical",
            "description": fm.get("description", "")[:160],  # keep draft readable
        })
    skills.sort(key=lambda s: s["name"])
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "skills": skills,
    }


_CATEGORY_DIR_MAP: list[tuple[str, str]] = [
    ("engineering-lifecycle", "engineering-lifecycle"),
    ("agent-skills/engineering", "engineering"),
    ("agent-skills/productivity", "productivity"),
    ("agent-skills/swarm-intelligence", "ai-ops"),
    ("agent-skills/infrastructure", "engineering"),
    ("skills/claude-thai", "thai"),
    ("skills/claude-code", "wiki"),
    ("skills/ecosystem", "ecosystem"),
    ("skills/domain", "domain"),
    ("skills/automation", "automation"),
    ("skills/delegation", "delegation"),
    ("skills/research", "research"),
]


def _infer_category(path: str) -> str:
    low = path.lower()
    for needle, category in _CATEGORY_DIR_MAP:
        if needle in low:
            return category
    return "uncategorized"


__all__ = [
    "parse_frontmatter",
    "classify_domain",
    "classify_lifecycle",
    "find_skill_files",
    "build_draft_registry",
]
