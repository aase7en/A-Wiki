"""Central Skill Brain generator — emits wiki/SKILL-INDEX.md (USA-1 §6).

This is the human/agent-readable "skill brain" every agent reads at session
start (via the SessionStart hook adapter, §5.2). It is the readable projection
of skills-registry.json — never hand-edited (Iron Law #9 extended).

Distinct from gen_agents_md.py (which emits a flat table fragment for splicing
into AGENTS.md): this generator emits a STANDALONE brain file organised by
domain, with an alias→canonical resolution table, a lifecycle-phase map, and a
"what to use when" quick-pick.

See: docs/architecture/universal-skill-architecture.md §6
"""
from __future__ import annotations

from collections import defaultdict

from .. import Registry

filename = "SKILL-INDEX.md"  # written to wiki/ by the orchestrator (special-cased)

# The Goal #5 domains in display order, then A-Wiki extensions.
PRIMARY_DOMAINS = [
    "code", "debug", "design", "ux-ui", "engineering",
    "trader", "medical", "business", "data",
]
EXTENSION_DOMAINS = [
    "security", "ai-ops", "productivity", "wiki",
    "iot", "env", "pharmacy", "thai",
    "logistics", "network", "media", "document", "sre",
]

DOMAIN_THAI = {
    "code": "เขียนโค้ด / ภาษาโปรแกรม",
    "debug": "ดีบัก / หาสาเหตุปัญหา",
    "design": "ดีไซน์ระบบ / สถาปัตยกรรม",
    "ux-ui": "UX/UI / Frontend / a11y",
    "engineering": "วิศวกร / Architect / Agent harness",
    "trader": "เทรด / DeFi / ตลาด",
    "medical": "การแพทย์ / ร้านยา / HIPAA",
    "business": "ธุรกิจ / การเงิน / CRM",
    "data": "Data Visualization / DB / Query",
    "security": "ความปลอดภัย / Hardening",
    "ai-ops": "AI ops / LLM / Cost",
    "productivity": "Productivity / Management",
    "wiki": "Wiki / Knowledge ops",
    "iot": "IoT / ฮาร์ดแวร์",
    "env": "Environment / น้ำเสีย",
    "pharmacy": "ร้านยา / สต็อกยา",
    "thai": "ภาษาไทย / เอกสารไทย",
    "logistics": "ลอจิสติกส์ / ซัพพลายเชน",
    "network": "เครือข่าย / Homelab",
    "media": "สื่อ / วิดีโอ / รูปภาพ",
    "document": "เอกสาร / docx/pdf/pptx/xlsx",
    "sre": "SRE / Observability / Deploy",
}


def _group_by_domain(skills: list[dict]) -> dict[str, list[dict]]:
    """Map domain -> sorted skill list. A skill appears under each of its domains."""
    by: dict[str, list[dict]] = defaultdict(list)
    for s in skills:
        for d in s.get("domain", []):
            by[d].append(s)
    for d in by:
        by[d].sort(key=lambda s: s["name"])
    return by


def render(registry: Registry) -> str:
    canonical = sorted(registry.canonical_for_agent("all"), key=lambda s: s["name"])
    by_domain = _group_by_domain(canonical)

    # Collect alias→canonical entries for the resolution table.
    aliases: list[tuple[str, str, str]] = []  # (alias_name, canonical_name, note)
    for s in registry.skills:
        if s.get("status") == "alias" and s.get("canonical"):
            aliases.append((s["name"], s["canonical"], s.get("migrated_to", "")))
        # deprecated skills with a canonical pointer also belong here.
        # canonical field = the replacement name; migrated_to = the human note.
        if s.get("status") == "deprecated":
            canonical_name = s.get("canonical") or s.get("migrated_to", "")
            # migrated_to may embed "name (note): ..." — extract just the name if so.
            if canonical_name and "(" in canonical_name:
                canonical_name = canonical_name.split("(")[0].strip()
            note = s.get("migrated_to", "")
            if canonical_name:
                aliases.append((s["name"], canonical_name, note))
    aliases.sort()

    out: list[str] = []
    out.append("# 🧠 SKILL-INDEX — A-Wiki Central Skill Brain")
    out.append("")
    out.append("> **AUTO-GENERATED** by `scripts/skills_registry/generators/gen_skill_index.py`")
    out.append("> from `skills-registry.json`. **Do not edit by hand** (Iron Law #9).")
    out.append("> Run `python scripts/regen-skill-surfaces.py` to refresh.")
    out.append(">")
    out.append("> This is the central skill brain. **Every agent reads this at session")
    out.append("> start** (USA-1 §6) so all agents see the same canonical skill set.")
    out.append("")
    out.append(f"**Total canonical skills**: {len(canonical)} · **Aliases/deprecated**: {len(aliases)}")
    out.append("")

    # Domain Summary
    out.append("## 📊 Domain Summary")
    out.append("")
    out.append("| Domain | Thai | Skills |")
    out.append("|--------|------|--------|")
    all_domains = PRIMARY_DOMAINS + EXTENSION_DOMAINS
    for d in all_domains:
        if d in by_domain:
            out.append(f"| `{d}` | {DOMAIN_THAI.get(d, '')} | {len(by_domain[d])} |")
    # any domain not in our display list (future-proof)
    for d in sorted(by_domain):
        if d not in all_domains:
            out.append(f"| `{d}` | {DOMAIN_THAI.get(d, '')} | {len(by_domain[d])} |")
    out.append("")

    # Per-domain tables (Goal #5 domains first)
    out.append("## 🎯 Skills by Domain")
    out.append("")

    def render_domain(d: str) -> None:
        skills = by_domain.get(d, [])
        if not skills:
            return
        out.append(f"### `{d}` — {DOMAIN_THAI.get(d, '')}")
        out.append("")
        out.append("| Skill | Lifecycle | Category | Description |")
        out.append("|-------|-----------|----------|-------------|")
        for s in skills:
            phase = s.get("lifecycle_phase", "none")
            category = s.get("category", "")
            desc = s.get("th_description") or s.get("description", "")
            desc = desc.replace("|", "\\|").replace("\n", " ")
            if len(desc) > 100:
                desc = desc[:97] + "..."
            out.append(f"| `{s['name']}` | {phase} | {category} | {desc} |")
        out.append("")

    out.append("### Goal #5 primary domains")
    out.append("")
    for d in PRIMARY_DOMAINS:
        render_domain(d)

    if any(d in by_domain for d in EXTENSION_DOMAINS):
        out.append("### A-Wiki extension domains")
        out.append("")
        for d in EXTENSION_DOMAINS:
            render_domain(d)

    # Lifecycle-phase map
    out.append("## 🔄 Lifecycle-Phase Map")
    out.append("")
    out.append("Skills that participate in the engineering lifecycle (DEFINE→PLAN→BUILD→VERIFY→REVIEW→SHIP):")
    out.append("")
    by_phase: dict[str, list[dict]] = defaultdict(list)
    for s in canonical:
        p = s.get("lifecycle_phase", "none")
        if p != "none":
            by_phase[p].append(s)
    for p in ["define", "plan", "build", "verify", "review", "ship", "meta"]:
        if p in by_phase:
            names = ", ".join(f"`{s['name']}`" for s in sorted(by_phase[p], key=lambda x: x["name"]))
            out.append(f"- **{p.upper()}**: {names}")
    out.append("")

    # Alias resolution table
    if aliases:
        out.append("## 🔁 Alias → Canonical Resolution")
        out.append("")
        out.append("Deprecated/alias skills and their canonical replacement. Agents invoking the")
        out.append("alias name auto-resolve to the canonical (USA-1 §7.2).")
        out.append("")
        out.append("| Alias / Deprecated | → Canonical | Note |")
        out.append("|--------------------|-------------|------|")
        for alias_name, canonical_name, note in aliases:
            note_display = note if note else ""
            out.append(f"| `{alias_name}` | `{canonical_name}` | {note_display} |")
        out.append("")

    # Quick-pick
    out.append("## ⚡ Quick-Pick — what to use when")
    out.append("")
    out.append("| Intent | Skill(s) |")
    out.append("|--------|----------|")
    quick_picks = [
        ("Refine a vague idea before building", "`brainstorm-before-build`"),
        ("Write a spec before coding", "`spec-driven-development`"),
        ("Break a spec into verifiable tasks", "`planning-and-task-breakdown`"),
        ("Implement code (thin slices)", "`incremental-implementation`"),
        ("Write the failing test first", "`test-driven-development` · `tdd` · `tdd-workflow`"),
        ("Something is broken — find root cause", "`debug-mantra` · `root-cause-first`"),
        ("Review code", "`scrutinize` · `code-simplification`"),
        ("Security review", "`security-and-hardening` · `hipaa-compliance` · `thai-pdpa`"),
        ("Performance optimization", "`performance-optimization` · `react-performance`"),
        ("Ship / deploy / release", "`shipping-and-launch` · `git-workflow-and-versioning`"),
        ("Write an ADR / doc", "`documentation-and-adrs`"),
        ("Ingest a source into the wiki", "`ingest-source`"),
        ("Search the wiki locally (free)", "`wiki-search-local`"),
        ("Cross-file synthesis", "`ask-notebooklm`"),
        ("Find existing skills before creating", "`skill-scout`"),
        ("Delegate to a free model", "`delegate-subagent`"),
    ]
    for intent, skills_str in quick_picks:
        out.append(f"| {intent} | {skills_str} |")
    out.append("")

    out.append("---")
    out.append("")
    out.append("*USA-1 §6 — A-Wiki v1.2 · Central Skill Brain · auto-generated*")
    return "\n".join(out) + "\n"
