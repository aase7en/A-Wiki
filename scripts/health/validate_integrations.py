#!/usr/bin/env python3
"""Deterministic integration-registry validation (A-Wiki vNext Phase 3).

One authoritative path (R-P3-002):
  1. YAML parse with duplicate-mapping-key detection (safe_load silently
     overwrites duplicates — a registry hazard).
  2. Full JSON-Schema validation against schemas/awiki-integrations/v1
     (additionalProperties:false rejects unknown/runtime fields structurally).
  3. Semantic checks the schema cannot express: external-module completeness,
     contradictory classifications, cache-commit rules, dangling references.

Fully deterministic and offline — safe in wiki_health, CI, any executor.
Exit 0 = valid; 1 = violations (also printed to stdout).
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY = REPO_ROOT / "config" / "integrations.yaml"
SCHEMA_FILE = REPO_ROOT / "schemas" / "awiki-integrations" / "v1.schema.json"

SCHEMA_KEY = "awiki-integrations/v1"
CLASSIFICATIONS = {"core", "module", "pattern", "reference", "reject"}
EXTERNAL_CLASSES = {"module", "reference"}
CACHE_STORAGE_TYPES = {"local-regenerable-cache"}


class _DuplicateKeyError(yaml.YAMLError):
    pass


class UniqueKeyLoader(yaml.SafeLoader):
    """SafeLoader that raises on duplicate mapping keys instead of silently
    overwriting them (last-key-wins is a registry integrity hazard)."""

    def construct_mapping(self, node, deep=False):
        seen = set()
        for key_node, _ in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                hashable = key in seen
            except TypeError:
                continue
            if hashable:
                mark = getattr(key_node, "start_mark", None)
                where = f" line {mark.line + 1}" if mark else ""
                raise _DuplicateKeyError(f"duplicate mapping key{where}: {key!r}")
            seen.add(key)
        return super().construct_mapping(node, deep=deep)


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    UniqueKeyLoader.construct_mapping,
)


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    entries: int = 0

    def exit_code(self) -> int:
        return 1 if self.errors else 0


def _classes_of(value) -> set:
    if isinstance(value, str):
        return {value}
    if isinstance(value, list):
        return set(value)
    return set()


def _semantic_checks(data: dict, repo_root: Path, result: ValidationResult) -> None:
    integrations = data["integrations"]
    for name, entry in integrations.items():
        if not isinstance(entry, dict):
            continue  # schema validation already reports the type error
        classes = _classes_of(entry.get("classification"))

        if "reject" in classes and len(classes) > 1:
            result.errors.append(f"{name}: classification 'reject' cannot combine with other classes")

        is_external = bool(classes & EXTERNAL_CLASSES)
        if is_external and entry.get("default") is True:
            result.errors.append(f"{name}: external module must be default-off (D-CTX-005)")
        if is_external and entry.get("lazy") is not True:
            result.errors.append(f"{name}: external module must be lazy")
        if classes == {"reject"} and entry.get("default") is True:
            result.errors.append(f"{name}: rejected integration must not be default-on")

        is_module = "module" in classes
        if is_module and "storage" not in entry:
            result.errors.append(f"{name}: module-classified entry must declare storage")
        if is_module and not entry.get("provides"):
            result.errors.append(f"{name}: module-classified entry must declare capabilities (provides)")

        storage = entry.get("storage")
        if isinstance(storage, dict):
            if storage.get("type") in CACHE_STORAGE_TYPES and storage.get("commit") is not False:
                result.errors.append(f"{name}: cache storage must set commit: false")
            if storage.get("commit") is True:
                result.errors.append(f"{name}: storage commit must not be true")

        ref = entry.get("reference")
        if isinstance(ref, str) and ref and not (repo_root / ref).exists():
            result.errors.append(f"{name}: reference path does not exist: {ref}")


def validate(path: Path) -> ValidationResult:
    result = ValidationResult()
    if not path.exists():
        result.errors.append(f"registry not found: {path}")
        return result

    try:
        data = yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)
    except _DuplicateKeyError as e:
        result.errors.append(f"duplicate yaml key: {e}")
        return result
    except yaml.YAMLError as e:
        result.errors.append(f"yaml parse error: {str(e).splitlines()[0]}")
        return result

    if not isinstance(data, dict):
        result.errors.append("registry must be a mapping")
        return result
    if data.get("schema") != SCHEMA_KEY:
        result.errors.append(f"schema key must be exactly '{SCHEMA_KEY}' (got {data.get('schema')!r})")

    integrations = data.get("integrations")
    if not isinstance(integrations, dict) or not integrations:
        result.errors.append("'integrations' must be a non-empty mapping")
        return result
    result.entries = len(integrations)

    # ── 2. authoritative schema validation (unknown/runtime fields etc.) ──
    try:
        import jsonschema  # type: ignore
    except ImportError:
        result.errors.append(
            "jsonschema unavailable — schema validation SKIPPED "
            "(install jsonschema; declared in requirements.txt)"
        )
    else:
        schema = json.loads(SCHEMA_FILE.read_text(encoding="utf-8"))
        validator = jsonschema.Draft202012Validator(schema)
        for err in sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path)):
            loc = "/".join(str(p) for p in err.absolute_path) or "<root>"
            result.errors.append(f"schema: {loc}: {err.message}")

    # ── 3. semantic checks ──
    repo_root = path.resolve().parents[1] if path.parent.name == "config" else path.parent
    _semantic_checks(data, repo_root, result)

    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Deterministic awiki-integrations/v1 registry validation")
    parser.add_argument("path", nargs="?", type=Path, default=DEFAULT_REGISTRY)
    args = parser.parse_args(argv)

    result = validate(args.path)
    for e in result.errors:
        print(f"integrations: {e}")
    print(f"integrations: {result.entries} entr{'y' if result.entries == 1 else 'ies'} checked, "
          f"{len(result.errors)} violation(s)")
    return result.exit_code()


if __name__ == "__main__":
    sys.exit(main())
