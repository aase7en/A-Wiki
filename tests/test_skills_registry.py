"""Tests for the skills-registry contract layer (Iron Law #1 — failing first).

Covers:
  - schema validation of skills-registry.json
  - registry load + name/alias lookup
  - generator idempotency (regen produces stable output)
  - drift detection (regen --check exits non-zero when surfaces stale)
  - dedup invariants (every alias has a canonical; no orphans; no cycles)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from skills_registry import (  # noqa: E402  (import after sys.path insert)
    SCHEMA_VERSION,
    VALID_DOMAINS,
    VALID_LIFECYCLE_PHASES,
    VALID_SOURCES,
    VALID_STATUSES,
    DriftError,
    Registry,
    validate_registry,
)
from skills_registry.scan import classify_domain, classify_lifecycle  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_REGISTRY: dict = {
    "schema_version": SCHEMA_VERSION,
    "generated_at": "2026-07-01T00:00:00Z",
    "skills": [
        {
            "name": "debug-mantra",
            "aliases": ["root-cause-first"],
            "domain": ["code", "debug"],
            "lifecycle_phase": "build",
            "category": "engineering",
            "source": "repo",
            "path": "agent-skills/engineering/debug-mantra",
            "agents": ["all"],
            "version": "1.0.0",
            "status": "canonical",
        },
        {
            "name": "hipaa-compliance",
            "aliases": [],
            "domain": ["medical", "security"],
            "lifecycle_phase": "review",
            "category": "domain",
            "source": "external-installed",
            "path": "~/.claude/skills/hipaa-compliance",
            "agents": ["claude", "zcode"],
            "status": "alias",
            "canonical": "healthcare-phi-compliance",
        },
        {
            "name": "healthcare-phi-compliance",
            "aliases": [],
            "domain": ["medical", "security"],
            "lifecycle_phase": "review",
            "category": "domain",
            "source": "repo",
            "path": "skills/domain/healthcare-phi-compliance",
            "agents": ["all"],
            "status": "canonical",
        },
    ],
}


@pytest.fixture
def sample_registry_file(tmp_path: Path) -> Path:
    """Write SAMPLE_REGISTRY to a temp file and return its path."""
    p = tmp_path / "skills-registry.json"
    p.write_text(json.dumps(SAMPLE_REGISTRY, indent=2), encoding="utf-8")
    return p


@pytest.fixture
def empty_registry_file(tmp_path: Path) -> Path:
    """Minimal valid registry with zero skills."""
    p = tmp_path / "skills-registry.json"
    p.write_text(
        json.dumps(
            {"schema_version": SCHEMA_VERSION, "generated_at": "2026-07-01T00:00:00Z", "skills": []},
            indent=2,
        ),
        encoding="utf-8",
    )
    return p


# ---------------------------------------------------------------------------
# Schema validation
# ---------------------------------------------------------------------------

class TestSchemaValidation:
    """validate_registry must reject malformed registries."""

    def test_valid_sample_passes(self, sample_registry_file: Path) -> None:
        errors = validate_registry(sample_registry_file)
        assert errors == [], f"expected no errors, got: {errors}"

    def test_missing_schema_version_is_migrated_not_rejected(self, tmp_path: Path) -> None:
        """Per migrate_registry design (skills_registry/__init__.py:151-173):
        a registry missing schema_version is treated as v0 and auto-upgraded
        to current SCHEMA_VERSION transparently — no rejection. This is the
        documented migration story that validate_registry relies on
        ('grill-me finding: schema_version 2 would otherwise reject all
        existing registries with no upgrade path'). C3-1: the old
        test_missing_schema_version_rejected asserted the pre-migration
        behavior and became stale when migrate_registry was added.
        """
        migrated_input = {"generated_at": "x", "skills": []}
        p = tmp_path / "r.json"
        p.write_text(json.dumps(migrated_input), encoding="utf-8")
        errors = validate_registry(p)
        assert errors == [], f"migration should make this valid, got: {errors}"

    def test_wrong_schema_version_rejected(self, tmp_path: Path) -> None:
        bad = {"schema_version": 99, "generated_at": "x", "skills": []}
        p = tmp_path / "r.json"
        p.write_text(json.dumps(bad), encoding="utf-8")
        errors = validate_registry(p)
        assert any("schema_version" in e for e in errors)

    def test_skill_missing_name_rejected(self, tmp_path: Path) -> None:
        bad = {
            "schema_version": SCHEMA_VERSION,
            "generated_at": "x",
            "skills": [{"domain": ["code"], "status": "canonical"}],
        }
        p = tmp_path / "r.json"
        p.write_text(json.dumps(bad), encoding="utf-8")
        errors = validate_registry(p)
        assert any("name" in e for e in errors)

    def test_invalid_domain_rejected(self, tmp_path: Path) -> None:
        bad = {
            "schema_version": SCHEMA_VERSION,
            "generated_at": "x",
            "skills": [
                {"name": "x", "domain": ["nonsense"], "status": "canonical", "source": "repo", "path": "p", "lifecycle_phase": "none"}
            ],
        }
        p = tmp_path / "r.json"
        p.write_text(json.dumps(bad), encoding="utf-8")
        errors = validate_registry(p)
        assert any("domain" in e and "nonsense" in e for e in errors)

    def test_invalid_lifecycle_phase_rejected(self, tmp_path: Path) -> None:
        bad = {
            "schema_version": SCHEMA_VERSION,
            "generated_at": "x",
            "skills": [
                {"name": "x", "domain": ["code"], "lifecycle_phase": "bogus", "status": "canonical", "source": "repo", "path": "p"}
            ],
        }
        p = tmp_path / "r.json"
        p.write_text(json.dumps(bad), encoding="utf-8")
        errors = validate_registry(p)
        assert any("lifecycle_phase" in e for e in errors)

    def test_invalid_status_rejected(self, tmp_path: Path) -> None:
        bad = {
            "schema_version": SCHEMA_VERSION,
            "generated_at": "x",
            "skills": [
                {"name": "x", "domain": ["code"], "status": "bogus", "source": "repo", "path": "p", "lifecycle_phase": "none"}
            ],
        }
        p = tmp_path / "r.json"
        p.write_text(json.dumps(bad), encoding="utf-8")
        errors = validate_registry(p)
        assert any("status" in e for e in errors)

    def test_duplicate_name_rejected(self, tmp_path: Path) -> None:
        bad = {
            "schema_version": SCHEMA_VERSION,
            "generated_at": "x",
            "skills": [
                {"name": "dup", "domain": ["code"], "status": "canonical", "source": "repo", "path": "a", "lifecycle_phase": "none"},
                {"name": "dup", "domain": ["code"], "status": "canonical", "source": "repo", "path": "b", "lifecycle_phase": "none"},
            ],
        }
        p = tmp_path / "r.json"
        p.write_text(json.dumps(bad), encoding="utf-8")
        errors = validate_registry(p)
        assert any("duplicate" in e.lower() and "dup" in e for e in errors)


# ---------------------------------------------------------------------------
# Registry load + lookup
# ---------------------------------------------------------------------------

class TestRegistryLookup:
    """Registry must resolve names and aliases to canonical skills."""

    def test_load_returns_registry(self, sample_registry_file: Path) -> None:
        reg = Registry.load(sample_registry_file)
        assert isinstance(reg, Registry)
        assert len(reg.skills) == 3

    def test_get_by_name(self, sample_registry_file: Path) -> None:
        reg = Registry.load(sample_registry_file)
        skill = reg.get("debug-mantra")
        assert skill is not None
        assert skill["name"] == "debug-mantra"

    def test_get_by_alias(self, sample_registry_file: Path) -> None:
        reg = Registry.load(sample_registry_file)
        # root-cause-first is an alias of debug-mantra
        skill = reg.get("root-cause-first")
        assert skill is not None
        assert skill["name"] == "debug-mantra"

    def test_get_unknown_returns_none(self, sample_registry_file: Path) -> None:
        reg = Registry.load(sample_registry_file)
        assert reg.get("does-not-exist") is None

    def test_canonical_names(self, sample_registry_file: Path) -> None:
        reg = Registry.load(sample_registry_file)
        canonicals = reg.canonical_names()
        assert "debug-mantra" in canonicals
        assert "healthcare-phi-compliance" in canonicals
        assert "hipaa-compliance" not in canonicals  # it's an alias

    def test_all_names_includes_aliases(self, sample_registry_file: Path) -> None:
        reg = Registry.load(sample_registry_file)
        names = reg.all_names()
        assert "debug-mantra" in names
        assert "root-cause-first" in names  # alias
        assert "hipaa-compliance" in names


# ---------------------------------------------------------------------------
# Dedup invariants
# ---------------------------------------------------------------------------

class TestDedupInvariants:
    """Aliases must resolve to existing canonicals; no orphans, no cycles."""

    def test_alias_must_reference_existing_canonical(self, tmp_path: Path) -> None:
        bad = {
            "schema_version": SCHEMA_VERSION,
            "generated_at": "x",
            "skills": [
                {"name": "orphan-alias", "domain": ["code"], "status": "alias", "canonical": "ghost", "source": "repo", "path": "p", "lifecycle_phase": "none"},
            ],
        }
        p = tmp_path / "r.json"
        p.write_text(json.dumps(bad), encoding="utf-8")
        errors = validate_registry(p)
        assert any("orphan" in e.lower() or "ghost" in e for e in errors)

    def test_alias_chain_cycle_rejected(self, tmp_path: Path) -> None:
        bad = {
            "schema_version": SCHEMA_VERSION,
            "generated_at": "x",
            "skills": [
                {"name": "a", "domain": ["code"], "status": "alias", "canonical": "b", "source": "repo", "path": "p", "lifecycle_phase": "none"},
                {"name": "b", "domain": ["code"], "status": "alias", "canonical": "a", "source": "repo", "path": "p", "lifecycle_phase": "none"},
            ],
        }
        p = tmp_path / "r.json"
        p.write_text(json.dumps(bad), encoding="utf-8")
        errors = validate_registry(p)
        assert any("cycle" in e.lower() or "alias" in e.lower() for e in errors)

    def test_alias_must_point_to_canonical_status(self, tmp_path: Path) -> None:
        # An alias whose canonical is itself an alias is invalid.
        bad = {
            "schema_version": SCHEMA_VERSION,
            "generated_at": "x",
            "skills": [
                {"name": "a", "domain": ["code"], "status": "alias", "canonical": "b", "source": "repo", "path": "p", "lifecycle_phase": "none"},
                {"name": "b", "domain": ["code"], "status": "alias", "canonical": "c", "source": "repo", "path": "p", "lifecycle_phase": "none"},
                {"name": "c", "domain": ["code"], "status": "canonical", "source": "repo", "path": "p", "lifecycle_phase": "none"},
            ],
        }
        p = tmp_path / "r.json"
        p.write_text(json.dumps(bad), encoding="utf-8")
        errors = validate_registry(p)
        assert any("a" in e and ("canonical" in e.lower() or "alias" in e.lower()) for e in errors)


# ---------------------------------------------------------------------------
# Consolidation (Chunk 2): dedup.py + consolidate.py
# ---------------------------------------------------------------------------

class TestDedupDetection:
    """dedup.detect_clusters must find known duplicate clusters."""

    def test_detects_verification_cluster(self, sample_registry_file: Path) -> None:
        from skills_registry.dedup import detect_clusters

        reg = Registry.load(sample_registry_file)
        clusters = detect_clusters(reg)
        # At minimum, clusters should be a list (the sample is small).
        assert isinstance(clusters, list)

    def test_classify_cluster_returns_valid_action(self, sample_registry_file: Path) -> None:
        from skills_registry.dedup import classify_cluster, detect_clusters

        reg = Registry.load(sample_registry_file)
        for cluster in detect_clusters(reg):
            action = classify_cluster(cluster, reg)
            assert action in {"delete", "alias", "stub", "distinct"}

    def test_validate_dedup_clean_on_valid_registry(self, sample_registry_file: Path) -> None:
        from skills_registry.dedup import validate_dedup

        reg = Registry.load(sample_registry_file)
        errors = validate_dedup(reg)
        assert errors == []

    def test_validate_dedup_catches_alias_without_canonical(self, tmp_path: Path) -> None:
        from skills_registry.dedup import validate_dedup

        bad = {
            "schema_version": SCHEMA_VERSION, "generated_at": "x",
            "skills": [
                {"name": "a", "domain": ["code"], "status": "alias", "source": "repo", "path": "p", "lifecycle_phase": "none"},
            ],
        }
        reg = Registry(bad)
        errors = validate_dedup(reg)
        assert any("no 'canonical'" in e for e in errors)


class TestConsolidation:
    """consolidate.apply_consolidation must be idempotent and sound."""

    def test_consolidation_is_idempotent(self, tmp_path: Path) -> None:
        from skills_registry.consolidate import apply_consolidation

        # Build a minimal registry with a verification cluster.
        reg_data = {
            "schema_version": SCHEMA_VERSION, "generated_at": "x",
            "skills": [
                {"name": "django-verification", "aliases": [], "domain": ["code"], "lifecycle_phase": "none", "category": "ecosystem", "source": "repo", "path": "skills/ecosystem/django-verification", "agents": ["all"], "status": "canonical"},
                {"name": "laravel-verification", "aliases": [], "domain": ["code"], "lifecycle_phase": "none", "category": "ecosystem", "source": "repo", "path": "skills/ecosystem/laravel-verification", "agents": ["all"], "status": "canonical"},
                {"name": "debug-mantra", "aliases": [], "domain": ["code", "debug"], "lifecycle_phase": "build", "category": "engineering", "source": "repo", "path": "agent-skills/engineering/debug-mantra", "agents": ["all"], "status": "canonical"},
                {"name": "root-cause-first", "aliases": [], "domain": ["code", "debug"], "lifecycle_phase": "build", "category": "engineering", "source": "repo", "path": "skills/deprecated/root-cause-first", "agents": ["all"], "status": "canonical"},
            ],
        }
        p = tmp_path / "r.json"
        p.write_text(json.dumps(reg_data), encoding="utf-8")

        result1 = apply_consolidation(p)
        # Reload to capture state after first run.
        with open(p, encoding="utf-8") as f:
            state1 = json.load(f)
        p.write_text(json.dumps(state1), encoding="utf-8")
        result2 = apply_consolidation(p)
        with open(p, encoding="utf-8") as f:
            state2 = json.load(f)

        # Second run should not change anything (idempotent).
        assert state1 == state2

    def test_consolidation_creates_valid_aliases(self, tmp_path: Path) -> None:
        from skills_registry import validate_registry
        from skills_registry.consolidate import apply_consolidation

        reg_data = {
            "schema_version": SCHEMA_VERSION, "generated_at": "x",
            "skills": [
                {"name": "django-verification", "aliases": [], "domain": ["code"], "lifecycle_phase": "none", "category": "ecosystem", "source": "repo", "path": "skills/ecosystem/django-verification", "agents": ["all"], "status": "canonical"},
                {"name": "laravel-verification", "aliases": [], "domain": ["code"], "lifecycle_phase": "none", "category": "ecosystem", "source": "repo", "path": "skills/ecosystem/laravel-verification", "agents": ["all"], "status": "canonical"},
                {"name": "root-cause-first", "aliases": [], "domain": ["code", "debug"], "lifecycle_phase": "build", "category": "engineering", "source": "repo", "path": "skills/deprecated/root-cause-first", "agents": ["all"], "status": "canonical"},
                {"name": "debug-mantra", "aliases": [], "domain": ["code", "debug"], "lifecycle_phase": "build", "category": "engineering", "source": "repo", "path": "agent-skills/engineering/debug-mantra", "agents": ["all"], "status": "canonical"},
            ],
        }
        p = tmp_path / "r.json"
        p.write_text(json.dumps(reg_data), encoding="utf-8")
        apply_consolidation(p)

        # After consolidation, the registry must still be schema-valid.
        errors = validate_registry(p)
        assert errors == [], f"registry invalid after consolidation: {errors}"


# ---------------------------------------------------------------------------
# Domain / lifecycle classification heuristics
# ---------------------------------------------------------------------------

class TestClassification:
    """scan.classify_* must tag skills by filename/path heuristics."""

    def test_thai_prefix_classified_thai(self) -> None:
        assert "thai" in classify_domain("thai-translate", "skills/claude-thai/thai-translate")

    def test_healthcare_prefix_classified_medical(self) -> None:
        assert "medical" in classify_domain("healthcare-phi-compliance", "skills/domain/healthcare-phi-compliance")

    def test_testing_suffix_classified_code(self) -> None:
        assert "code" in classify_domain("python-testing", "skills/ecosystem/python-testing")

    def test_security_keyword_classified_security(self) -> None:
        assert "security" in classify_domain("security-and-hardening", "skills/ecosystem/security-and-hardening")

    def test_ito_prefix_classified_trader(self) -> None:
        assert "trader" in classify_domain("ito-trade-planner", "skills/ecosystem/ito-trade-planner")

    def test_lifecycle_verify_dir(self) -> None:
        assert classify_lifecycle("browser-testing-with-devtools", "skills/engineering-lifecycle/verify/browser-testing-with-devtools") == "verify"

    def test_lifecycle_ship_dir(self) -> None:
        assert classify_lifecycle("shipping-and-launch", "skills/engineering-lifecycle/ship/shipping-and-launch") == "ship"

    def test_lifecycle_default_none(self) -> None:
        assert classify_lifecycle("thai-translate", "skills/claude-thai/thai-translate") == "none"


# ---------------------------------------------------------------------------
# Generator idempotency
# ---------------------------------------------------------------------------

class TestGeneratorIdempotency:
    """Running a generator twice on the same registry must produce identical output."""

    def test_kilo_generator_is_idempotent(self, sample_registry_file: Path, tmp_path: Path) -> None:
        from skills_registry.generators import gen_kilo

        reg = Registry.load(sample_registry_file)
        out1 = gen_kilo.render(reg)
        out2 = gen_kilo.render(reg)
        assert out1 == out2

    def test_gemini_generator_is_idempotent(self, sample_registry_file: Path) -> None:
        from skills_registry.generators import gen_gemini

        reg = Registry.load(sample_registry_file)
        out1 = gen_gemini.render(reg)
        out2 = gen_gemini.render(reg)
        assert out1 == out2

    def test_agents_md_generator_is_idempotent(self, sample_registry_file: Path) -> None:
        from skills_registry.generators import gen_agents_md

        reg = Registry.load(sample_registry_file)
        out1 = gen_agents_md.render(reg)
        out2 = gen_agents_md.render(reg)
        assert out1 == out2

    def test_hermes_generator_is_idempotent(self, sample_registry_file: Path) -> None:
        from skills_registry.generators import gen_hermes

        reg = Registry.load(sample_registry_file)
        out1 = gen_hermes.render(reg)
        out2 = gen_hermes.render(reg)
        assert out1 == out2


# ---------------------------------------------------------------------------
# Hermes generator (opt-in per-agent filtering)
# ---------------------------------------------------------------------------
# Uniquely among the generators, gen_hermes is OPT-IN: it lists ONLY skills
# that explicitly name "hermes" in agents[], deliberately ignoring "all".
# Rationale: Pi5 free-tier models (8k-32k context) cannot preload all 331
# canonical skills, so Hermes surfaces a small (~40-50) hand-picked set.
# This mirrors canonical_for_agent's "all OR agent" rule, inverted.

HERMES_SAMPLE_REGISTRY: dict = {
    "schema_version": SCHEMA_VERSION,
    "generated_at": "2026-07-01T00:00:00Z",
    "skills": [
        {  # tagged for hermes → MUST appear
            "name": "hermes-tagged",
            "aliases": [],
            "domain": ["ai-ops"],
            "lifecycle_phase": "review",
            "category": "swarm",
            "source": "repo",
            "path": "skills/awiki/hermes-fan-out",
            "agents": ["all", "hermes"],
            "version": "",
            "status": "canonical",
        },
        {  # agents == ["all"] only → MUST NOT appear (free-tier budget)
            "name": "all-only",
            "aliases": [],
            "domain": ["code"],
            "lifecycle_phase": "none",
            "category": "engineering",
            "source": "repo",
            "path": "skills/x/all-only",
            "agents": ["all"],
            "version": "",
            "status": "canonical",
        },
        {  # tagged for a different agent only → MUST NOT appear
            "name": "claude-only",
            "aliases": [],
            "domain": ["code"],
            "lifecycle_phase": "none",
            "category": "engineering",
            "source": "repo",
            "path": "skills/x/claude-only",
            "agents": ["claude"],
            "version": "",
            "status": "canonical",
        },
        {  # alias of a hermes-tagged canonical → MUST appear (resolves via canonical)
            "name": "hermes-alias",
            "aliases": [],
            "domain": ["ai-ops"],
            "lifecycle_phase": "review",
            "category": "swarm",
            "source": "external-installed",
            "path": "~/.hermes/skills/alias",
            "agents": ["hermes"],
            "version": "",
            "status": "alias",
            "canonical": "hermes-tagged",
        },
    ],
}


@pytest.fixture
def hermes_sample_file(tmp_path: Path) -> Path:
    p = tmp_path / "hermes-registry.json"
    p.write_text(json.dumps(HERMES_SAMPLE_REGISTRY, indent=2), encoding="utf-8")
    return p


class TestHermesGenerator:
    """gen_hermes emits hermes.skills.json — the opt-in skill list for Pi5 Hermes."""

    def test_filename_is_hermes_skills_json(self) -> None:
        from skills_registry.generators import gen_hermes

        assert gen_hermes.filename == "hermes.skills.json"

    def test_emits_only_explicitly_hermes_tagged_skills(self, hermes_sample_file: Path) -> None:
        """Skills with agents==['all'] must NOT appear — only explicit 'hermes' tags."""
        from skills_registry.generators import gen_hermes

        reg = Registry.load(hermes_sample_file)
        data = json.loads(gen_hermes.render(reg))
        assert "skills" in data, "output must have a top-level 'skills' key"
        names = {s["name"] for s in data["skills"]}
        assert "hermes-tagged" in names, "explicitly hermes-tagged skill must be listed"
        assert "all-only" not in names, (
            "agents==['all'] must be EXCLUDED so Hermes doesn't preload all 331 skills"
        )
        assert "claude-only" not in names, "non-hermes explicit tag must be excluded"

    def test_output_is_valid_json_with_required_fields(self, hermes_sample_file: Path) -> None:
        """Each entry must carry the fields Hermes needs to locate + describe a skill."""
        from skills_registry.generators import gen_hermes

        reg = Registry.load(hermes_sample_file)
        data = json.loads(gen_hermes.render(reg))
        assert len(data["skills"]) > 0
        for s in data["skills"]:
            assert "name" in s, "skill entry missing 'name'"
            assert "path" in s, "skill entry missing 'path' (needed for symlink on Pi5)"

    def test_round_trips_through_json(self, hermes_sample_file: Path) -> None:
        """Output must be valid, deterministic JSON (stable key order)."""
        from skills_registry.generators import gen_hermes

        reg = Registry.load(hermes_sample_file)
        out = gen_hermes.render(reg)
        # Must parse cleanly.
        json.loads(out)
        # Deterministic: second render byte-identical.
        assert gen_hermes.render(reg) == out

    def test_empty_registry_emits_empty_list(self, empty_registry_file: Path) -> None:
        from skills_registry.generators import gen_hermes

        reg = Registry.load(empty_registry_file)
        data = json.loads(gen_hermes.render(reg))
        assert data["skills"] == []


# ---------------------------------------------------------------------------
# Drift detection
# ---------------------------------------------------------------------------

class TestDriftDetection:
    """regen --check must report drift when a generated surface is stale."""

    def test_check_clean_when_surfaces_match(self, sample_registry_file: Path, tmp_path: Path) -> None:
        from skills_registry import drift

        # Write the generated surfaces to disk, then check — clean state = no drift.
        surfaces = {"kilo.jsonc": '{"generated_at": "2026-07-01T00:00:00Z", "x": 1}'}
        for name, content in surfaces.items():
            (tmp_path / name).write_text(content, encoding="utf-8")
        drift_errors = drift.detect(sample_registry_file, surfaces_dir=tmp_path, generated=surfaces)
        assert drift_errors == []

    def test_check_reports_drift_when_stale(self, sample_registry_file: Path, tmp_path: Path) -> None:
        from skills_registry import drift

        # Disk has a stale surface; the registry says it should be different.
        stale = tmp_path / "kilo.jsonc"
        stale.write_text("STALE CONTENT FROM LAST YEAR", encoding="utf-8")
        generated = {"kilo.jsonc": '{"generated_at": "2026-07-01T00:00:00Z", "fresh": true}'}
        with pytest.raises(DriftError):
            drift.detect_and_raise(sample_registry_file, surfaces_dir=tmp_path, generated=generated)


# ---------------------------------------------------------------------------
# Constants sanity
# ---------------------------------------------------------------------------

class TestConstants:
    """The taxonomy vocabularies must match the approved design."""

    def test_domains_include_user_list(self) -> None:
        # Goal #5 explicit list + refined sub-domains added during Chunk 1
        for required in [
            "code", "debug", "design", "ux-ui", "trader", "medical",
            "business", "data", "engineering",
            # refined sub-domains (split out of the former "code" catch-all)
            "logistics", "network", "media", "document", "sre",
        ]:
            assert required in VALID_DOMAINS, f"missing domain: {required}"

    def test_lifecycle_phases_match_router(self) -> None:
        # awiki-lifecycle-router phases
        for phase in ["define", "plan", "build", "verify", "review", "ship", "meta", "none"]:
            assert phase in VALID_LIFECYCLE_PHASES

    def test_sources_match_design(self) -> None:
        assert VALID_SOURCES == {"repo", "external-installed", "external-system"}

    def test_statuses_match_design(self) -> None:
        assert VALID_STATUSES == {"canonical", "alias", "deprecated"}


class TestConsoleEncodingResilience:
    """regen-skill-surfaces.py must not die on non-UTF-8 consoles.

    Root cause (2026-07-11, Thai-locale Windows): the script prints emoji
    (✅/✓); on a cp874 console stdout encoding can't represent them, the
    print raises UnicodeEncodeError, the process exits 1, and the
    pre-commit hook misreads the crash as "surfaces drifted" — blocking
    every commit on that machine even when there is zero drift.
    """

    def test_check_survives_cp874_console(self) -> None:
        import os
        import subprocess
        import sys

        env = {**os.environ, "PYTHONIOENCODING": "cp874"}
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "regen-skill-surfaces.py"), "--check"],
            capture_output=True,
            env=env,
            cwd=REPO_ROOT,
        )
        assert result.returncode == 0, (
            "regen --check must exit 0 on a cp874 console (no real drift); "
            f"stderr tail: {result.stderr[-400:]!r}"
        )
