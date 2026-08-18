#!/usr/bin/env python3
"""Deterministic, offline awiki-project/v1 adapter validation (Phase 4).

Fail-closed validation of a project's `.awiki/project.yaml` + canonical
attachment surface:
  1. YAML parse (duplicate-key-safe loader reused from the integrations
     validator — one loading contract across the kernel).
  2. JSON-Schema validation (unknown fields rejected structurally).
  3. Semantic checks:
     - no absolute/private machine paths in ANY string (Windows drive/UNC/
       extended, Unix absolute/private, tilde) — host-OS independent
     - no secret-shaped values (kernel's single security-pattern source)
     - resources are containment-safe: resolved target must stay under the
       resolved project root (nested `..` and symlink escapes rejected)
     - integrations.allowed ids must exist in the canonical registry
     - canonical surface: AGENTS.md with the adapter marker + context.md +
       state/ present

No network, no subprocesses, no side effects. Exit 0 = valid; 1 = violations.
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
REGISTRY_FILE = REPO_ROOT / "config" / "integrations.yaml"
sys.path.insert(0, str(REPO_ROOT / "scripts" / "health"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "hooks"))

from validate_integrations import UniqueKeyLoader  # noqa: E402 -- one loader contract
from _scan_staged_diff import PATTERNS, PLACEHOLDERS  # noqa: E402 -- one pattern source

AGENTS_MARKER = "awiki-project-adapter"

# Absolute/private machine-path shapes, host-OS independent (R-P4-001).
# - drive letters guarded by (?<![A-Za-z]) so https:// never matches
# - UNC \\\\server\\share and Windows extended \\\\?\\ / \\??\\ device paths
# - Unix absolute-private roots incl. general /etc,/tmp,/var,/opt,/root
# - ~ home references
ABSOLUTE_PATH_RE = re.compile(
    r"(?<![A-Za-z])[A-Za-z]:[\\/][^\s\"']*"
    r"|\\\\[^\s\"']*"                        # UNC \\server\share + extended \\?\ device paths
    r"|/(?:home|Users|etc|tmp|var|opt|root|private)(?:/[^\s\"']*)?"
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


def _contains(project_root: Path, candidate: Path) -> bool:
    """True iff candidate (resolved) is project_root (resolved) or beneath it.
    Resolves symlinks — a link pointing outside escapes containment (R-P4-001)."""
    try:
        root_resolved = project_root.resolve()
        target_resolved = candidate.resolve()
    except OSError:
        return False
    try:
        target_resolved.relative_to(root_resolved)
        return True
    except ValueError:
        return False


def _known_integration_ids() -> set[str] | None:
    """Ids from the canonical registry; None if the registry itself is broken
    (caller fails closed — validating against a corrupt registry is worse)."""
    try:
        data = yaml.load(REGISTRY_FILE.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)
        return set((data.get("integrations") or {}).keys())
    except Exception:
        return None


def validate(project_root: Path) -> ValidationResult:
    result = ValidationResult()
    project_root = project_root.resolve()
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

    # ── absolute/private machine paths (any string field) ──
    for loc, value in _iter_strings(data):
        if ABSOLUTE_PATH_RE.search(value):
            result.errors.append(f"absolute/private machine path at {loc}: {value[:60]!r}")

    if isinstance(data, dict):
        # ── resources: containment-safe local references ──
        for ref in data.get("resources", []) or []:
            if not isinstance(ref, str):
                continue
            candidate = project_root / ref
            if Path(ref).is_absolute() or ref.startswith("..") or not ref:
                result.errors.append(f"resource must be project-relative: {ref}")
            elif not candidate.exists():
                result.errors.append(f"referenced adapter file does not exist: {ref}")
            elif not _contains(project_root, candidate):
                result.errors.append(
                    f"resource escapes the project root (nested .. or symlink): {ref}")

        # ── integration allowlist vs canonical registry (offline) ──
        allowed = (data.get("integrations") or {}).get("allowed") or []
        known = _known_integration_ids()
        if known is None:
            result.errors.append("canonical integration registry unreadable — cannot verify allowlist (fail closed)")
        else:
            for iid in allowed:
                if iid not in known:
                    result.errors.append(f"unknown integration id (not in config/integrations.yaml): {iid}")

    # ── canonical attachment surface (R-P4-006) ──
    agents = project_root / "AGENTS.md"
    if not agents.is_file():
        result.errors.append("missing discovery surface: AGENTS.md")
    elif AGENTS_MARKER not in agents.read_text(encoding="utf-8", errors="replace"):
        result.errors.append(f"AGENTS.md lacks the adapter marker ({AGENTS_MARKER}) — not attached")
    if not (aw / "context.md").is_file():
        result.errors.append("missing adapter file: .awiki/context.md")
    if not (aw / "state").is_dir():
        result.errors.append("missing adapter dir: .awiki/state/")

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
