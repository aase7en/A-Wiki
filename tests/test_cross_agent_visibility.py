"""Tests for cross-agent skill visibility (Chunk 5 — failing first).

Verifies that every canonical skill in the registry is discoverable by every
agent surface the registry claims to serve. This catches the root cause R2
(two discovery paradigms with no sync layer) by asserting the generator output
actually contains paths to each canonical skill.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from skills_registry import Registry, validate_registry  # noqa: E402
from skills_registry.generators import gen_agents_md, gen_gemini, gen_kilo  # noqa: E402

REGISTRY_PATH = REPO_ROOT / "skills-registry.json"


@pytest.fixture(scope="module")
def registry() -> Registry:
    errors = validate_registry(REGISTRY_PATH)
    assert errors == [], f"registry invalid: {errors}"
    return Registry.load(REGISTRY_PATH)


class TestRegistryHealth:
    """The registry itself must be sound before checking agent visibility."""

    def test_registry_exists(self) -> None:
        assert REGISTRY_PATH.exists(), "skills-registry.json missing"

    def test_registry_valid(self) -> None:
        errors = validate_registry(REGISTRY_PATH)
        assert errors == [], f"registry invalid: {errors}"

    def test_registry_has_skills(self, registry: Registry) -> None:
        assert len(registry.skills) > 100, "expected 100+ skills in registry"

    def test_every_canonical_has_domain(self, registry: Registry) -> None:
        missing = [s["name"] for s in registry.skills if s.get("status") == "canonical" and not s.get("domain")]
        assert not missing, f"canonical skills missing domain: {missing[:10]}"


class TestAgentSurfacesGenerated:
    """Generated surfaces must exist and be non-empty."""

    def test_skills_index_generated(self, registry: Registry) -> None:
        out = gen_agents_md.render(registry)
        assert "AUTO-GENERATED" in out
        assert "| Skill |" in out  # table header

    def test_kilo_paths_generated(self, registry: Registry) -> None:
        out = gen_kilo.render(registry)
        data = json.loads(out)
        assert "skills" in data
        assert len(data["skills"]["paths"]) > 5, "expected multiple skill paths for Kilo"

    def test_gemini_skills_generated(self, registry: Registry) -> None:
        out = gen_gemini.render(registry)
        data = json.loads(out)
        assert "skills" in data
        assert len(data["skills"]) > 0, "expected at least one Gemini skill group"


class TestCrossAgentVisibility:
    """The core assertion: canonical skills are discoverable across surfaces."""

    def test_skills_index_lists_all_canonical(self, registry: Registry) -> None:
        """The AGENTS.md index must list every canonical skill by name."""
        out = gen_agents_md.render(registry)
        canonical = registry.canonical_names()
        missing = [name for name in canonical if f"`{name}`" not in out]
        # Allow a small tolerance for skills with unusual formatting.
        assert len(missing) == 0, (
            f"{len(missing)} canonical skill(s) missing from skills-index: {missing[:10]}"
        )

    def test_kilo_paths_cover_canonical_dirs(self, registry: Registry) -> None:
        """Kilo paths must include the top-level dir of every canonical repo skill."""
        out = gen_kilo.render(registry)
        for skill in registry.canonical_for_agent("kilo"):
            if skill.get("source") != "repo":
                continue
            path = skill.get("path", "")
            parts = Path(path).parts
            if len(parts) >= 2:
                top = f"./{parts[0]}/{parts[1]}"
                assert top in out, f"Kilo paths missing {top} for {skill['name']}"

    def test_no_drift(self) -> None:
        """Generated surfaces on disk must match what the registry would produce."""
        from skills_registry import drift
        reg = Registry.load(REGISTRY_PATH)
        generated = {
            gen_kilo.filename: gen_kilo.render(reg),
            gen_gemini.filename: gen_gemini.render(reg),
            gen_agents_md.filename: gen_agents_md.render(reg),
        }
        surfaces_dir = REPO_ROOT / "scripts" / "skills_registry" / "generated"
        errors = drift.detect(REGISTRY_PATH, surfaces_dir, generated)
        assert errors == [], f"drift detected: {errors}"


class TestDedupIntegrity:
    """Post-Chunk-2 dedup invariants must hold on the live registry."""

    def test_all_aliases_resolve(self, registry: Registry) -> None:
        """Every alias must resolve to a canonical skill."""
        for skill in registry.skills:
            if skill.get("status") == "alias":
                canonical = skill.get("canonical")
                assert canonical, f"alias '{skill['name']}' has no canonical"
                resolved = registry.get(canonical)
                assert resolved is not None, (
                    f"alias '{skill['name']}' → '{canonical}' which is not resolvable"
                )
                assert resolved.get("status") != "alias", (
                    f"alias '{skill['name']}' → '{canonical}' which is itself an alias"
                )

    def test_no_orphan_migrated_to(self, registry: Registry) -> None:
        """Deprecated skills must point to existing successors."""
        names = registry.all_names()
        for skill in registry.skills:
            if skill.get("status") == "deprecated":
                target = skill.get("migrated_to")
                if target:
                    assert target in names, (
                        f"deprecated '{skill['name']}' migrated_to '{target}' not found"
                    )
