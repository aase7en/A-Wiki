"""Integrity tests for the A-Suite (A-Wiki A-Suite v2).

The failure this guards against is concrete and already happened once in this
repo: skills/engineering-lifecycle/awiki-lifecycle-router/SKILL.md routes to
seven skills under skills/engineering-lifecycle/build/ — a directory that does
not exist — and to `grill-me`, which is an alias. Nothing caught it, because
nothing ever checked that a skill named in prose actually exists.

The A-* packs are pure dispatchers, so almost every line of them is a reference
to another skill. Without this test they would rot the same way.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from skills_registry import Registry, routing  # noqa: E402

REGISTRY = Registry.load(REPO_ROOT / "skills-registry.json")

# The A-Suite entry points, discovered from the registry rather than hardcoded
# so a newly added pack is covered automatically.
ENTRY_POINTS = [
    s for s in REGISTRY.skills
    if s.get("status") == "canonical"
    and s["name"].startswith("a-")
    and s.get("category") == "pipeline"
    and len(s.get("path", "").split("/")) == 4
]

# Backticked tokens that look like skill names: kebab-case, 2+ segments.
SKILL_TOKEN = re.compile(r"`([a-z][a-z0-9]*(?:-[a-z0-9]+)+)`")

# Backticked kebab tokens that are not skills — paths, fields, env vars, phases.
NOT_SKILLS = {
    "done-criteria", "root-cause", "kebab-case", "cost-first", "self-contained",
    "a-focus", "cost-tier", "no-ledger", "focus-set", "skill-route",
    "pre-mortem", "right-size", "multi-step", "second-opinion", "sub-question",
    "cross-check", "design-system",  # design-system IS a skill; kept below
}
NOT_SKILLS.discard("design-system")


def skill_refs(text: str) -> set[str]:
    """Backticked skill-shaped tokens in a SKILL.md body."""
    out = set()
    for tok in SKILL_TOKEN.findall(text):
        if tok in NOT_SKILLS or "/" in tok or "." in tok:
            continue
        out.add(tok)
    return out


@pytest.mark.parametrize("skill", ENTRY_POINTS, ids=lambda s: s["name"])
class TestEntryPoint:
    def test_skill_md_exists_at_the_registered_path(self, skill):
        assert (REPO_ROOT / skill["path"]).exists(), (
            f"{skill['name']} registered at {skill['path']} but the file is missing"
        )

    def test_every_skill_it_references_actually_exists(self, skill):
        """No dangling references — the awiki-lifecycle-router failure mode.

        A reference resolves if it is EITHER a registry skill OR a persona file
        under agents/. a-council legitimately names code-reviewer,
        test-engineer, security-auditor and web-performance-auditor, which are
        agent definitions at agents/*.md, not registry entries.
        """
        text = (REPO_ROOT / skill["path"]).read_text(encoding="utf-8")
        body = text.split("---", 2)[-1]          # skip frontmatter
        missing = [
            ref for ref in skill_refs(body)
            if REGISTRY.get(ref) is None
            and not (REPO_ROOT / "agents" / f"{ref}.md").exists()
            and ref != skill["name"]
        ]
        assert not missing, f"{skill['name']} references non-existent skill(s): {sorted(missing)}"

    def test_does_not_reference_a_deprecated_skill(self, skill):
        text = (REPO_ROOT / skill["path"]).read_text(encoding="utf-8")
        body = text.split("---", 2)[-1]
        by_name = {s["name"]: s for s in REGISTRY.skills}
        deprecated = [
            ref for ref in skill_refs(body)
            if by_name.get(ref, {}).get("status") == "deprecated"
        ]
        assert not deprecated, (
            f"{skill['name']} chains through deprecated skill(s): {sorted(deprecated)}"
        )

    def test_frontmatter_declares_the_registry_fields(self, skill):
        text = (REPO_ROOT / skill["path"]).read_text(encoding="utf-8")
        head = text.split("---", 2)[1]
        for field in ("name:", "domain:", "lifecycle_phase:", "status:", "invocation:"):
            assert field in head, f"{skill['name']} frontmatter missing {field}"

    def test_a_phase_is_valid_when_present(self, skill):
        phase = skill.get("a_phase")
        if phase is not None:
            assert phase in routing.VALID_A_PHASES


ROUTER_DOC = REPO_ROOT / "skills" / "engineering-lifecycle" / "awiki-lifecycle-router" / "SKILL.md"
COMMAND_DOCS = sorted((REPO_ROOT / "commands").glob("A-*.md"))


def _refs_resolve(path: Path) -> tuple[list[str], list[str]]:
    by_name = {s["name"]: s for s in REGISTRY.skills}
    body = path.read_text(encoding="utf-8").split("---", 2)[-1]
    refs = skill_refs(body)
    missing = [
        r for r in refs
        if REGISTRY.get(r) is None and not (REPO_ROOT / "agents" / f"{r}.md").exists()
    ]
    deprecated = [r for r in refs if by_name.get(r, {}).get("status") == "deprecated"]
    return missing, deprecated


class TestLifecycleRouter:
    """The router rotted once already — seven routes into a build/ directory
    that does not exist. Nothing noticed for months. Now it is checked."""

    def test_router_references_resolve(self):
        missing, deprecated = _refs_resolve(ROUTER_DOC)
        assert not missing, f"awiki-lifecycle-router references missing skill(s): {missing}"
        assert not deprecated, f"awiki-lifecycle-router routes to deprecated: {deprecated}"

    def test_router_points_at_the_generated_table(self):
        text = ROUTER_DOC.read_text(encoding="utf-8")
        assert "A-ROUTER.md" in text, "router must defer to the generated table"

    def test_router_does_not_route_into_a_nonexistent_directory(self):
        text = ROUTER_DOC.read_text(encoding="utf-8")
        for dead in ("build/incremental-implementation", "build/frontend-ui-engineering",
                     "build/test-driven-development", "build/context-engineering"):
            assert dead not in text, f"router still routes to nonexistent {dead}"


@pytest.mark.parametrize("doc", COMMAND_DOCS, ids=lambda p: p.name)
class TestCommandDocs:
    def test_references_resolve(self, doc):
        missing, deprecated = _refs_resolve(doc)
        assert not missing, f"{doc.name} references missing skill(s): {missing}"
        assert not deprecated, f"{doc.name} references deprecated skill(s): {deprecated}"

    def test_maps_to_an_existing_skill_file(self, doc):
        text = doc.read_text(encoding="utf-8")
        m = re.search(r"Maps to: `([^`]+)`", text)
        assert m, f"{doc.name} has no 'Maps to:' line"
        assert (REPO_ROOT / m.group(1)).exists(), f"{doc.name} maps to a missing file"

    def test_title_is_not_truncated_mid_word(self, doc):
        first = doc.read_text(encoding="utf-8").splitlines()[0]
        assert not re.search(r"[A-Za-z]\.\.\.$", first), f"{doc.name} title cut mid-word"


class TestCommandCoverage:
    def test_every_entry_point_has_a_command_doc(self):
        names = {d.name.lower().replace(".md", "") for d in COMMAND_DOCS}
        for s in ENTRY_POINTS:
            hint = (s.get("invocation_hint") or f"/{s['name']}").split()[0].lstrip("/")
            assert hint.lower() in names, f"{s['name']} has no commands/{hint}.md"


class TestTriggerHygiene:
    def test_no_two_skills_claim_the_same_trigger(self):
        """A shared trigger makes routing order-dependent and unpredictable."""
        owners: dict[str, list[str]] = {}
        for s in REGISTRY.skills:
            for t in s.get("triggers") or []:
                owners.setdefault(t, []).append(s["name"])
        clashes = {t: names for t, names in owners.items() if len(names) > 1}
        assert not clashes, f"triggers claimed by more than one skill: {clashes}"

    def test_all_registry_triggers_pass_validation(self):
        errors = []
        for s in REGISTRY.skills:
            if s.get("triggers"):
                errors += routing.validate_triggers(s["triggers"], s["name"])
        assert not errors, errors

    def test_the_fallback_skills_have_no_triggers(self):
        """a-think is the fallback and a-loop is autonomous — neither may fire
        on a keyword, or they would hijack prompts meant for a real skill."""
        for name in ("a-think", "a-loop"):
            s = REGISTRY.get(name)
            assert s is not None
            assert not s.get("triggers"), f"{name} must not have triggers"

    def test_every_entry_point_is_reachable(self):
        """Either it has triggers, or it is a documented explicit-only skill."""
        explicit_only = {"a-think", "a-loop", "a-router"}
        for s in ENTRY_POINTS:
            if s["name"] in explicit_only:
                continue
            assert s.get("triggers"), (
                f"{s['name']} has no triggers and is not in the explicit-only "
                f"list — no agent will ever auto-pick it"
            )
