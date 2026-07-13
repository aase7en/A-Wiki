"""Skills registry — single source of truth for A-Wiki skill surfaces.

Public API
==========
- ``Registry``           — load + query the registry (by name / alias / canonical).
- ``validate_registry``  — return a list of schema/dedup violation strings.
- ``DriftError``         — raised when generated surfaces are stale.
- Constants: ``SCHEMA_VERSION``, ``VALID_DOMAINS``, ``VALID_LIFECYCLE_PHASES``,
  ``VALID_SOURCES``, ``VALID_STATUSES``.

The registry JSON lives at ``<repo>/skills-registry.json`` and is the Layer 1
contract: every agent surface (Kilo ``kilo.jsonc``, Gemini ``settings.json``,
Hermes ``lifecycle-config.json``, ZCode/Claude symlink farms, AGENTS.md tables)
is GENERATED from it by ``scripts/regen-skill-surfaces.py``.  Agents never edit
generated surfaces by hand; they edit the registry, then regen.

See: docs/protocols/skill-frontmatter-schema.md (Chunk 3 of the architecture).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Taxonomy — single vocabulary for the whole registry.
# Adding a domain/phase here automatically makes it usable everywhere.
# ---------------------------------------------------------------------------

SCHEMA_VERSION: int = 2

# Goal #5 domains (Code, debug, Design, UX/UI, Trader, Medical, Business,
# Data, Engineering Architect) + A-Wiki-native extensions.
VALID_DOMAINS: frozenset[str] = frozenset({
    # user-requested (Goal #5)
    "code", "debug", "design", "ux-ui", "trader", "medical",
    "business", "data", "engineering",
    # A-Wiki extensions
    "security", "ai-ops", "productivity", "wiki",
    "iot", "env", "pharmacy", "thai",
    # refined sub-domains (split out of the former "code" catch-all)
    "logistics",   # supply-chain, carrier, customs, inventory, returns
    "network",     # bgp, cisco, netmiko, homelab network gear
    "media",       # video/image/audio generation & editing
    "document",    # docx/pdf/pptx/xlsx generators
    "sre",         # observability, canary, production-audit, deployment
})

# Mirrors awiki-lifecycle-router phases + meta/none for non-lifecycle skills.
VALID_LIFECYCLE_PHASES: frozenset[str] = frozenset({
    "define", "plan", "build", "verify", "review", "ship", "meta", "none",
})

VALID_SOURCES: frozenset[str] = frozenset({
    "repo",               # tracked in this git repo (portable)
    "external-installed", # machine-local installed skill (~/.claude/skills/...)
    "external-system",    # vendored from an upstream system (~/.codex/.system/)
})

VALID_STATUSES: frozenset[str] = frozenset({
    "canonical",   # the primary implementation; others may alias to it
    "alias",       # thin entrypoint that re-routes to a canonical (needs `canonical`)
    "deprecated",  # do not use; routes to `migrated_to` if present
})

# v2 — how a skill is invoked. Used by the live dashboard "Skills" view.
#   auto   = SessionStart hook loads it (e.g. lifecycle-router, debug-mantra)
#   manual = user types /skill-name
#   both   = auto in some contexts, manual otherwise
VALID_INVOCATIONS: frozenset[str] = frozenset({"auto", "manual", "both"})

REQUIRED_SKILL_FIELDS: tuple[str, ...] = (
    "name", "domain", "lifecycle_phase", "category", "source", "path", "status",
)


class DriftError(Exception):
    """Raised when a generated surface no longer matches the registry."""


# ---------------------------------------------------------------------------
# Registry container
# ---------------------------------------------------------------------------

class Registry:
    """In-memory view of skills-registry.json with name/alias resolution."""

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data
        self.skills: list[dict[str, Any]] = list(data.get("skills", []))
        # name -> skill dict (canonical names only)
        self._by_name: dict[str, dict[str, Any]] = {s["name"]: s for s in self.skills if "name" in s}
        # alias -> canonical name
        self._alias_to_canonical: dict[str, str] = {}
        for s in self.skills:
            for alias in s.get("aliases", []) or []:
                self._alias_to_canonical[alias] = s["name"]
            # status: alias skills declare `canonical:` directly.
            if s.get("status") == "alias" and s.get("canonical"):
                self._alias_to_canonical[s["name"]] = s["canonical"]

    # -- construction -------------------------------------------------------

    @classmethod
    def load(cls, path: Path | str) -> "Registry":
        """Load and return a Registry. Does NOT validate — call validate_registry first if needed."""
        with open(path, "r", encoding="utf-8") as f:
            return cls(json.load(f))

    # -- queries ------------------------------------------------------------

    def get(self, name: str) -> dict[str, Any] | None:
        """Resolve a name OR alias to its canonical skill dict, or None."""
        # Direct canonical hit.
        if name in self._by_name and self._by_name[name].get("status") != "alias":
            return self._by_name[name]
        # Alias → canonical.
        canonical = self._alias_to_canonical.get(name)
        if canonical and canonical in self._by_name:
            target = self._by_name[canonical]
            if target.get("status") != "alias":
                return target
        return None

    def canonical_names(self) -> set[str]:
        """Names of all canonical (non-alias, non-deprecated) skills."""
        return {
            s["name"] for s in self.skills
            if s.get("status") == "canonical"
        }

    def all_names(self) -> set[str]:
        """Every resolvable name: canonicals + aliases + deprecated names."""
        names: set[str] = set(self._by_name.keys())
        names.update(self._alias_to_canonical.keys())
        return names

    def canonical_for_agent(self, agent: str) -> list[dict[str, Any]]:
        """Canonical skills visible to a given agent (agents list contains 'all' or the agent)."""
        return [
            s for s in self.skills
            if s.get("status") == "canonical"
            and ("all" in (s.get("agents") or []) or agent in (s.get("agents") or []))
        ]


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def migrate_registry(data: dict[str, Any]) -> dict[str, Any]:
    """Upgrade a registry dict from its declared schema_version to SCHEMA_VERSION.

    Each step transforms v(n) → v(n+1) in place. When the registry's version is
    already current, this is a no-op. This is the migration story that
    validate_registry relies on (grill-me finding: schema_version 2 would
    otherwise reject all existing registries with no upgrade path).

    Add a new step here whenever SCHEMA_VERSION bumps. Steps must be additive
    (never drop fields silently) and idempotent.
    """
    version = data.get("schema_version", 0)
    # v1 → v2: add optional dashboard/guide fields. Backward-compatible —
    # skills without these fields default sensibly and still validate.
    #   invocation defaults to "manual" (most skills are user-invoked).
    #   th_description, when_to_use, examples, process_steps stay absent
    #   until the Thai guide content (CHUNK 2) populates them.
    if version < 2:
        for skill in data.get("skills", []):
            skill.setdefault("invocation", "manual")
        data["schema_version"] = 2
        version = 2
    return data


def validate_registry(path: Path | str) -> list[str]:
    """Return a list of human-readable error strings. Empty list = valid."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read registry: {exc}"]

    errors: list[str] = []

    # Migrate before validating so older registries upgrade transparently.
    data = migrate_registry(data)

    # Top-level
    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(
            f"schema_version must be {SCHEMA_VERSION}, got {data.get('schema_version')!r}"
        )
    if "generated_at" not in data:
        errors.append("missing top-level key: generated_at")

    skills = data.get("skills")
    if not isinstance(skills, list):
        errors.append("skills must be a list")
        return errors

    seen_names: dict[str, int] = {}
    by_name: dict[str, dict[str, Any]] = {}

    for i, skill in enumerate(skills):
        ctx = f"skills[{i}]"

        # Required fields
        for field in REQUIRED_SKILL_FIELDS:
            if field not in skill:
                errors.append(f"{ctx}: missing required field '{field}'")

        name = skill.get("name")
        if name:
            if name in seen_names:
                errors.append(f"{ctx}: duplicate name '{name}' (also at skills[{seen_names[name]}])")
            else:
                seen_names[name] = i
                by_name[name] = skill

        # Enum validation
        domain = skill.get("domain")
        if isinstance(domain, list):
            bad = [d for d in domain if d not in VALID_DOMAINS]
            for d in bad:
                errors.append(f"{ctx} ({name}): invalid domain {d!r}; valid: {sorted(VALID_DOMAINS)}")
        elif domain is not None:
            errors.append(f"{ctx} ({name}): domain must be a list")

        phase = skill.get("lifecycle_phase")
        if phase is not None and phase not in VALID_LIFECYCLE_PHASES:
            errors.append(
                f"{ctx} ({name}): invalid lifecycle_phase {phase!r}; "
                f"valid: {sorted(VALID_LIFECYCLE_PHASES)}"
            )

        source = skill.get("source")
        if source is not None and source not in VALID_SOURCES:
            errors.append(f"{ctx} ({name}): invalid source {source!r}; valid: {sorted(VALID_SOURCES)}")

        status = skill.get("status")
        if status is not None and status not in VALID_STATUSES:
            errors.append(f"{ctx} ({name}): invalid status {status!r}; valid: {sorted(VALID_STATUSES)}")

        # v2 — invocation (auto/manual/both) for the dashboard Skills view
        invocation = skill.get("invocation")
        if invocation is not None and invocation not in VALID_INVOCATIONS:
            errors.append(
                f"{ctx} ({name}): invalid invocation {invocation!r}; "
                f"valid: {sorted(VALID_INVOCATIONS)}"
            )

        # v2 — examples must be a list of {scenario, how} objects (if present)
        examples = skill.get("examples")
        if examples is not None:
            if not isinstance(examples, list):
                errors.append(f"{ctx} ({name}): examples must be a list")
            else:
                for j, ex in enumerate(examples):
                    if not isinstance(ex, dict) or "scenario" not in ex or "how" not in ex:
                        errors.append(
                            f"{ctx} ({name}): examples[{j}] must have 'scenario' and 'how' keys"
                        )

        # v2 — process_steps must be a list of strings (if present)
        process_steps = skill.get("process_steps")
        if process_steps is not None and not (
            isinstance(process_steps, list)
            and all(isinstance(s, str) for s in process_steps)
        ):
            errors.append(f"{ctx} ({name}): process_steps must be a list of strings")

        # Status-specific requirements
        if status == "alias":
            canonical = skill.get("canonical")
            if not canonical:
                errors.append(f"{ctx} ({name}): status 'alias' requires a 'canonical' field")
        if status == "deprecated":
            # migrated_to is recommended but not strictly required.
            pass

    # Cross-skill: alias canonicals must point to existing canonical skills.
    for skill in skills:
        name = skill.get("name")
        if skill.get("status") == "alias":
            canonical = skill.get("canonical")
            if canonical and canonical not in by_name:
                errors.append(
                    f"orphan alias: '{name}' → canonical '{canonical}' does not exist"
                )
            elif canonical and by_name.get(canonical, {}).get("status") != "canonical":
                errors.append(
                    f"invalid alias: '{name}' → '{canonical}' which is not status 'canonical' "
                    f"(aliases must resolve to a canonical skill, not another alias)"
                )

    # Cycle detection across alias chains.
    errors.extend(_detect_alias_cycles(by_name))

    return errors


def _detect_alias_cycles(by_name: dict[str, dict[str, Any]]) -> list[str]:
    """Walk alias→canonical chains and report any cycle (A→B→A)."""
    errors: list[str] = []
    for start in by_name:
        seen: list[str] = []
        current: str | None = start
        while current and current in by_name and by_name[current].get("status") == "alias":
            if current in seen:
                cycle = " → ".join(seen + [current])
                errors.append(f"alias cycle detected: {cycle}")
                break
            seen.append(current)
            current = by_name[current].get("canonical")
    return errors


__all__ = [
    "SCHEMA_VERSION",
    "VALID_DOMAINS",
    "VALID_LIFECYCLE_PHASES",
    "VALID_SOURCES",
    "VALID_STATUSES",
    "VALID_INVOCATIONS",
    "REQUIRED_SKILL_FIELDS",
    "DriftError",
    "Registry",
    "migrate_registry",
    "validate_registry",
]
