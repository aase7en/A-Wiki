"""adapters/skill_registry — production + mock SkillRegistry(Port) adapters.

ADR-0012 slice A3 (2026-08-03). The skill registry has two distinct I/O
surfaces that became two ports:

  - SkillRegistryPort (read):  `Registry.load(REGISTRY_FILE)` + `reg.get()`
  - SkillRegistryWriterPort:   the atomic temp→validate→os.replace dance in
                                `update_skill_field`

Two adapters per port prove each is a real seam (Cockburn: 'two adapters =
a real seam') and satisfy ADR-0012 acceptance rule R10 (contract suite
catches prod/mock divergence).

Security invariants preserved EXACTLY (a-council security-auditor 2026-08-03):
  - EDITABLE_FIELDS allowlist unchanged
  - _EDIT_MAX_LEN unchanged
  - _BOOL_FIELDS unchanged, strict bool parse
  - validate-then-rollback on the prod path
  - atomic os.replace on the prod path
  - mtime cache bust after write
"""
from __future__ import annotations

from pathlib import Path
import importlib.util
import sys

# skills_service.py lives in scripts/live-dashboard/ (a flat file, not a
# package) and depends on scripts/skills_registry/. Load it lazily by path so
# this adapter does not pollute sys.path on import — only when a method runs.
# Path from this file: skill_registry/__init__.py → adapters/ → lib/ → scripts/ → repo
# i.e. parents[4] to reach REPO_ROOT.
REPO_ROOT = Path(__file__).resolve().parents[4]
_SKILLS_SERVICE_PATH = REPO_ROOT / "scripts" / "live-dashboard" / "skills_service.py"


def _load_skills_service():
    """Import skills_service.py by path. Cached on the module object."""
    cached = sys.modules.get("skills_service_adapters_a3")
    if cached is not None:
        return cached
    # Make scripts/ importable for skills_registry (skills_service's dep)
    if str(REPO_ROOT / "scripts") not in sys.path:
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location(
        "skills_service_adapters_a3", _SKILLS_SERVICE_PATH,
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    sys.modules["skills_service_adapters_a3"] = mod
    return mod


# ── Production read adapter ─────────────────────────────────────────────
class FileSkillRegistryAdapter:
    """Prod SkillRegistryPort backed by skills_service._load_registry().

    Thin wrapper: the prod primitive already does mtime-checked caching
    (the `_cache` global), so this adapter just delegates. The point of
    the indirection is that the APPLICATION no longer calls
    `Registry.load(REGISTRY_FILE)` directly — it goes through the port,
    so a future swap (in-memory, sqlite, remote) touches only this file."""

    def load(self):
        return _load_skills_service()._load_registry()

    def get(self, name: str) -> dict | None:
        reg = self.load()
        return reg.get(name)


# ── Mock read adapter (headless tests + composition-root swap) ──────────
class InMemorySkillRegistryAdapter:
    """Mock SkillRegistryPort over an in-memory dict of skill dicts.

    For headless tests of skill_service functions that consume the registry
    (skill_health_score, agent_skill_matrix, etc.) without touching disk.
    `load()` returns an object with a `.get(name)` method like the real
    Registry — here, a trivial shim."""

    def __init__(self, skills: list[dict] | None = None) -> None:
        self._skills: dict[str, dict] = {}
        for s in skills or []:
            self._skills[s.get("name", "")] = s

    def load(self):
        # Return a lightweight stand-in that quacks like Registry for `.get`.
        adapter = self

        class _Shim:
            def get(self, name: str) -> dict | None:
                # Honour canonical-name + alias resolution the real Registry
                # does, minimally: try exact, then alias match.
                if name in adapter._skills:
                    return adapter._skills[name]
                for s in adapter._skills.values():
                    if name in (s.get("aliases") or []):
                        return s
                return None

            def all_skills(self) -> list[dict]:
                return list(adapter._skills.values())

        return _Shim()

    def get(self, name: str) -> dict | None:
        return self.load().get(name)


# ── Production write adapter ────────────────────────────────────────────
class AtomicSkillRegistryWriterAdapter:
    """Prod SkillRegistryWriterPort — delegates to skills_service.update_skill_field.

    Preserves the entire security invariant chain (allowlist, max-len, bool
    parse, validate-rollback, atomic replace, cache bust) by NOT re-
    implementing it. The adapter's only job is to be the swap point: a test
    or a future sqlite-backed writer replaces THIS class, not the 80-line
    prod dance."""

    def update_field(self, name: str, field: str, value: str) -> dict:
        return _load_skills_service().update_skill_field(name, field, value)


# ── Mock write adapter ──────────────────────────────────────────────────
class InMemorySkillRegistryWriterAdapter:
    """Mock SkillRegistryWriterPort over an in-memory dict.

    Mirrors the prod VALIDATION rules (EDITABLE_FIELDS, _EDIT_MAX_LEN,
    _BOOL_FIELDS) so the contract suite can catch divergence — but applies
    them to the in-memory store, never touching the real REGISTRY_FILE.
    Returns the SAME `{ok, ...}` dict shape so callers are byte-for-byte
    compatible with the prod path.

    The allowlist/max-len/bool constants are read from skills_service on
    first use (lazy), so this adapter does not import skills_service at
    module-load time."""

    def __init__(self, store: InMemorySkillRegistryAdapter) -> None:
        self._store = store
        # Lazy: read validation constants from the prod module on first use.
        ss = _load_skills_service()
        self._EDITABLE_FIELDS = ss.EDITABLE_FIELDS
        self._EDIT_MAX_LEN = ss._EDIT_MAX_LEN
        self._BOOL_FIELDS = ss._BOOL_FIELDS

    def update_field(self, name: str, field: str, value: str) -> dict:
        # Mirror prod validation EXACTLY (Liskov substitute).
        if field not in self._EDITABLE_FIELDS:
            return {"ok": False,
                    "error": f"field '{field}' not in editable allowlist "
                             f"{sorted(self._EDITABLE_FIELDS)}"}
        if field in self._BOOL_FIELDS:
            if isinstance(value, bool):
                typed = value
            elif isinstance(value, str) and value.strip().lower() in ("true", "1"):
                typed = True
            elif isinstance(value, str) and value.strip().lower() in ("false", "0"):
                typed = False
            else:
                return {"ok": False,
                        "error": f"field '{field}' requires a bool (true/false), got: {value!r}"}
        else:
            if not isinstance(value, str):
                return {"ok": False, "error": "value must be a string"}
            if len(value) > self._EDIT_MAX_LEN:
                return {"ok": False,
                        "error": f"value too long ({len(value)} > {self._EDIT_MAX_LEN})"}
            typed = value

        skill = self._store.get(name)
        if not skill:
            return {"ok": False, "error": f"skill '{name}' not found"}
        # Council 2026-08-03 Liskov fix: prod returns the canonical
        # (alias-resolved) name, not the raw input — mirror that exactly
        # so a caller writing via an alias gets the same `name` back from
        # both adapters. Without this the contract suite cannot detect
        # the divergence (R10).
        canonical_name = skill.get("name", name)
        skill[field] = typed
        return {"ok": True, "field": field, "name": canonical_name, "length": len(str(value))}
