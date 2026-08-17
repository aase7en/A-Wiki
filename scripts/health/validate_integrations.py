#!/usr/bin/env python3
"""Deterministic integration-registry validation (A-Wiki vNext Phase 3).

Validates config/integrations.yaml against the awiki-integrations/v1
contract WITHOUT network, subprocesses, or side effects — safe to run in
wiki_health, CI, or any executor. Enforces the D-CTX-005 invariants:

  - exact schema key
  - classification in core|module|pattern|reference|reject (or list of)
  - external modules must be default-off AND lazy
  - cache storage must never be committed
  - reference paths, when given, must exist in the repo
  - rejected entries must not be default-on

Exit 0 = valid; 1 = contract violations (also printed to stdout).
"""
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY = REPO_ROOT / "config" / "integrations.yaml"

SCHEMA_KEY = "awiki-integrations/v1"
CLASSIFICATIONS = {"core", "module", "pattern", "reference", "reject"}
EXTERNAL_CLASSIFICATIONS = {"module", "reference"}  # things that pull outside code/services
CACHE_STORAGE_TYPES = {"local-regenerable-cache"}


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    entries: int = 0

    def exit_code(self) -> int:
        return 1 if self.errors else 0


def _classify_ok(value) -> bool:
    if isinstance(value, str):
        return value in CLASSIFICATIONS
    if isinstance(value, list) and value:
        return all(v in CLASSIFICATIONS for v in value)
    return False


def validate(path: Path) -> ValidationResult:
    result = ValidationResult()
    if not path.exists():
        result.errors.append(f"registry not found: {path}")
        return result

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
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

    repo_root = path.resolve().parents[1] if path.parent.name == "config" else path.parent

    for name, entry in integrations.items():
        result.entries += 1
        if not isinstance(entry, dict):
            result.errors.append(f"{name}: entry must be a mapping")
            continue

        if not _classify_ok(entry.get("classification")):
            result.errors.append(
                f"{name}: classification must be one of {sorted(CLASSIFICATIONS)} "
                f"(got {entry.get('classification')!r})"
            )

        classification = entry.get("classification")
        classes = set(classification) if isinstance(classification, list) else {classification}
        is_external = bool(classes & EXTERNAL_CLASSIFICATIONS)
        default_on = entry.get("default") is True

        if is_external and default_on:
            result.errors.append(f"{name}: external module must be default-off (D-CTX-005)")

        if classes == {"reject"} and default_on:
            result.errors.append(f"{name}: rejected integration must not be default-on")

        if is_external and entry.get("lazy") is not True:
            result.errors.append(f"{name}: external module must be lazy")

        storage = entry.get("storage")
        if isinstance(storage, dict):
            if storage.get("type") in CACHE_STORAGE_TYPES and storage.get("commit") is not False:
                result.errors.append(f"{name}: cache storage must set commit: false")
            if storage.get("commit") is True:
                result.errors.append(f"{name}: storage commit must not be true")

        for key in ("provides", "requires", "implemented_by"):
            value = entry.get(key)
            if value is not None and not isinstance(value, list):
                result.errors.append(f"{name}: '{key}' must be a list")

        ref = entry.get("reference")
        if isinstance(ref, str) and ref and not (repo_root / ref).exists():
            result.errors.append(f"{name}: reference path does not exist: {ref}")

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
