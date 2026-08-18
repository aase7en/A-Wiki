#!/usr/bin/env python3
"""Deterministic, offline awiki-project/v1 adapter validation (Phase 4).

Fail-closed validation of a project's `.awiki/project.yaml`:
  1. YAML parse (duplicate-key-safe loader reused from the integrations
     validator — one loading contract across the kernel).
  2. JSON-Schema validation (unknown fields rejected structurally).
  3. Semantic checks: no absolute/private machine paths in any string,
     no secret-shaped values (reuses the kernel's single security-pattern
     source), referenced local adapter files must exist, context.md present.

No network, no subprocesses, no side effects — safe in CI and any executor.
Exit 0 = valid; 1 = violations (printed).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_FILE = REPO_ROOT / "schemas" / "awiki-project" / "v1.schema.json"
sys.path.insert(0, str(REPO_ROOT / "scripts" / "health"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "hooks"))

from validate_integrations import UniqueKeyLoader  # noqa: E402 -- one loader contract
from _scan_staged_diff import PATTERNS, PLACEHOLDERS  # noqa: E402 -- one pattern source

# Absolute / private machine-path shapes (mirrors kernel privacy rules).
# (?<![A-Za-z]) keeps https://github.com (the "s:") from matching a drive letter.
ABSOLUTE_PATH_RE = re.compile(
    r"(?<![A-Za-z])[A-Za-z]:[\\/][^\s\"']*"
    r"|/(?:home|Users)/[^\s\"']*"
    r"|~/"
    r"|\.(?:gitnexus|kilo|hermes)/"
)


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def exit_code(self) -> int:
        return 1 if self.errors else 0


def _iter_strings(node, prefix=""):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from _iter_strings(v, f"{prefix}.{k}" if prefix else str(k))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _iter_strings(v, f"{prefix}[{i}]")
    elif isinstance(node, str):
        yield prefix, node


def validate(project_root: Path) -> ValidationResult:
    result = ValidationResult()
    aw = project_root / ".awiki"
    yml = aw / "project.yaml"

    if not yml.is_file():
        result.errors.append(f"missing adapter metadata: {yml}")
        return result

    try:
        data = yaml.load(yml.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)
    except yaml.YAMLError as e:
        result.errors.append(f"malformed project.yaml (fail closed): {str(e).splitlines()[0]}")
        return result

    # ── schema (unknown fields, required policy fields) ──
    try:
        import jsonschema  # type: ignore
    except ImportError:
        result.errors.append("jsonschema unavailable — schema validation impossible (fail closed)")
    else:
        schema = json.loads(SCHEMA_FILE.read_text(encoding="utf-8"))
        for err in sorted(jsonschema.Draft202012Validator(schema).iter_errors(data),
                          key=lambda e: list(e.absolute_path)):
            loc = "/".join(str(p) for p in err.absolute_path) or "<root>"
            result.errors.append(f"schema: {loc}: {err.message}")

    # ── secrets (single kernel pattern source; placeholders respected) ──
    for loc, value in _iter_strings(data):
        for name, regex, allowlist in PATTERNS:
            m = regex.search(value)
            if not m:
                continue
            window = value.lower()[max(0, m.start() - 40): m.end() + 40]
            if any(a in window for a in allowlist) or any(p in window for p in PLACEHOLDERS):
                continue
            result.errors.append(f"secret-shaped value at {loc}: [{name}]")
            break

    # ── absolute/private machine paths ──
    for loc, value in _iter_strings(data):
        if ABSOLUTE_PATH_RE.search(value):
            result.errors.append(f"absolute/private machine path at {loc}: {value[:60]!r}")

    # ── referenced local adapter files must exist (project-relative only) ──
    for ref in data.get("resources", []) if isinstance(data, dict) else []:
        if not isinstance(ref, str):
            continue
        if Path(ref).is_absolute() or ref.startswith(".."):
            result.errors.append(f"resource must be project-relative: {ref}")
        elif not (project_root / ref).exists():
            result.errors.append(f"referenced adapter file does not exist: {ref}")

    # ── context.md is part of the adapter contract ──
    if not (aw / "context.md").is_file():
        result.errors.append("missing adapter file: .awiki/context.md")

    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a project's awiki-project/v1 adapter (offline)")
    parser.add_argument("project_root", nargs="?", type=Path, default=Path("."))
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(argv)

    result = validate(args.project_root)
    if args.json:
        print(json.dumps({"valid": result.exit_code() == 0,
                          "errors": result.errors, "warnings": result.warnings},
                         ensure_ascii=False, indent=2))
    else:
        for e in result.errors:
            print(f"adapter: {e}")
        print(f"adapter: {len(result.errors)} error(s)")
    return result.exit_code()


if __name__ == "__main__":
    sys.exit(main())
