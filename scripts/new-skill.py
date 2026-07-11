#!/usr/bin/env python3
"""
new-skill.py — scaffold + register a new A-Wiki skill (registry-first)
========================================================================

Creates a new ``SKILL.md`` under a skill directory AND registers it in
``skills-registry.json`` — in that order reversed for safety: the registry
entry is written BEFORE the ``SKILL.md`` file, because hook #15
(``check_skill_registry.py``) blocks any ``SKILL.md`` write that is not
already registered. Writing the registry first means a crash between the
two writes never leaves an unregistered ``SKILL.md`` sitting on disk that
the hook would then reject.

Usage
-----
::

    # Dry-run (default): validate + show the plan, touch nothing.
    python scripts/new-skill.py my-new-skill --domain code --phase build

    # Apply: write skills-registry.json, write SKILL.md, run regen (+ --check).
    python scripts/new-skill.py my-new-skill --domain code,debug --phase build \\
        --category awiki --description "Does the thing." --apply

Exit codes
----------
- 0 = success (dry-run plan shown, or applied + regen/--check both clean)
- 1 = validation error, runtime guard (duplicate name / existing SKILL.md),
      or regen/--check failure

See: docs/architecture/skill-architecture-plan.md
     scripts/skills_registry/__init__.py (canonical VALID_* taxonomy)
     scripts/regen-skill-surfaces.py (the orchestrator this script defers to)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

# Emoji/Thai text in status prints crash on non-UTF-8 consoles (Thai Windows =
# cp874). Degrade unencodable characters instead of dying — same pattern as
# scripts/regen-skill-surfaces.py.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass  # non-reconfigurable stream (pipes/tests) — already safe

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from skills_registry import VALID_DOMAINS, VALID_LIFECYCLE_PHASES  # noqa: E402

DEFAULT_PATH_ROOT = "skills/awiki"
DEFAULT_CATEGORY = "uncategorized"

_KEBAB_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


class ScaffoldError(Exception):
    """Raised for validation failures and runtime guards (never for I/O errors)."""


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_kebab_case(name: str) -> None:
    if not name or not _KEBAB_RE.match(name):
        raise ScaffoldError(
            f"invalid skill name {name!r}: must be kebab-case — lowercase "
            "letters/digits, single hyphens between segments, no leading, "
            "trailing, or doubled hyphens (e.g. 'my-new-skill')"
        )


def validate_domains(domains: Any) -> None:
    domains = list(domains)
    if not domains:
        raise ScaffoldError("at least one --domain is required")
    invalid = [d for d in domains if d not in VALID_DOMAINS]
    if invalid:
        raise ScaffoldError(
            f"invalid domain(s): {', '.join(invalid)}; "
            f"valid domains: {', '.join(sorted(VALID_DOMAINS))}"
        )


def validate_phase(phase: str) -> None:
    if phase not in VALID_LIFECYCLE_PHASES:
        raise ScaffoldError(
            f"invalid lifecycle_phase {phase!r}; "
            f"valid phases: {', '.join(sorted(VALID_LIFECYCLE_PHASES))}"
        )


# ---------------------------------------------------------------------------
# Config / plan / result
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ScaffoldConfig:
    name: str
    domain: tuple[str, ...]
    phase: str
    category: str = DEFAULT_CATEGORY
    description: str = ""
    path_root: str = DEFAULT_PATH_ROOT
    apply: bool = False


@dataclass
class ScaffoldResult:
    applied: bool
    entry: dict
    skill_md_path: Path
    regen_ok: Optional[bool] = None
    regen_check_ok: Optional[bool] = None


class StepRecorder:
    """Records the ordered sequence of apply-time side-effecting steps."""

    def __init__(self) -> None:
        self.steps: list[str] = []

    def record(self, step: str) -> None:
        self.steps.append(step)


# ---------------------------------------------------------------------------
# Entry / SKILL.md rendering
# ---------------------------------------------------------------------------

def build_entry(cfg: ScaffoldConfig) -> dict:
    """Build the skills-registry.json entry. Pure function of cfg — no I/O."""
    return {
        "name": cfg.name,
        "aliases": [],
        "domain": list(cfg.domain),
        "lifecycle_phase": cfg.phase,
        "category": cfg.category,
        "source": "repo",
        "path": f"{cfg.path_root}/{cfg.name}/SKILL.md",
        "agents": ["all"],
        "version": "1.0.0",
        "status": "canonical",
        "description": cfg.description,
    }


def render_skill_md(cfg: ScaffoldConfig) -> str:
    """Render the initial SKILL.md content. Pure function of cfg — no I/O."""
    domain_str = ", ".join(cfg.domain)
    return f"""---
name: {cfg.name}
description: "{cfg.description}"
version: 1.0.0
domain: [{domain_str}]
lifecycle_phase: {cfg.phase}
category: {cfg.category}
agents: [all]
status: canonical
---

# {cfg.name}

TODO: describe what this skill does and when Claude should use it.

## When to use

- TODO

## What it does

- TODO

## Files

| File | Purpose |
|---|---|
| `{cfg.path_root}/{cfg.name}/SKILL.md` | This skill |
"""


# ---------------------------------------------------------------------------
# Scaffold — injectable fs/runner so this is testable without real I/O
# ---------------------------------------------------------------------------

def run_scaffold(
    cfg: ScaffoldConfig,
    *,
    fs: Any,
    runner: Any,
    recorder: StepRecorder,
    repo_root: Path,
) -> ScaffoldResult:
    """Validate cfg, then (if cfg.apply) write registry -> SKILL.md -> regen.

    ``fs`` must implement ``read_text(path)``, ``write_text(path, content)``,
    ``exists(path) -> bool``. ``runner`` must implement
    ``run(cmd, env, cwd) -> CompletedProcess-shaped (has .returncode)``.

    Dry-run (cfg.apply is False) never touches fs or runner — validation
    and plan-building only.
    """
    # Validation always runs first, and never touches fs/runner.
    validate_kebab_case(cfg.name)
    validate_domains(cfg.domain)
    validate_phase(cfg.phase)

    entry = build_entry(cfg)
    skill_md_path = repo_root / cfg.path_root / cfg.name / "SKILL.md"

    if not cfg.apply:
        return ScaffoldResult(applied=False, entry=entry, skill_md_path=skill_md_path)

    registry_path = repo_root / "skills-registry.json"

    # --- runtime guards (read-only; must not write anything before both pass) ---
    registry_data = json.loads(fs.read_text(registry_path))
    existing_names = {s.get("name") for s in registry_data.get("skills", [])}
    if cfg.name in existing_names:
        raise ScaffoldError(
            f"skill '{cfg.name}' is already registered in skills-registry.json"
        )

    if fs.exists(skill_md_path):
        raise ScaffoldError(f"SKILL.md already exists at {skill_md_path}")

    # --- write registry BEFORE SKILL.md (hook #15 requires the entry to exist
    #     before the file does) ---
    registry_data.setdefault("skills", []).append(entry)
    recorder.record("write_registry")
    fs.write_text(registry_path, json.dumps(registry_data, indent=2, ensure_ascii=False) + "\n")

    recorder.record("write_skill_md")
    fs.write_text(skill_md_path, render_skill_md(cfg))

    # --- regen surfaces, then verify no drift ---
    regen_script = repo_root / "scripts" / "regen-skill-surfaces.py"
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"

    regen_result = runner.run(
        [sys.executable, str(regen_script)], env=env, cwd=repo_root
    )
    check_result = runner.run(
        [sys.executable, str(regen_script), "--check"], env=env, cwd=repo_root
    )

    return ScaffoldResult(
        applied=True,
        entry=entry,
        skill_md_path=skill_md_path,
        regen_ok=(regen_result.returncode == 0),
        regen_check_ok=(check_result.returncode == 0),
    )


# ---------------------------------------------------------------------------
# Real fs/runner (used by main() — never used in tests)
# ---------------------------------------------------------------------------

class _RealFS:
    def read_text(self, path) -> str:
        return Path(path).read_text(encoding="utf-8")

    def write_text(self, path, content: str) -> None:
        # LF-only, always — .gitattributes pins *.json and *.md to `eol=lf`.
        # Path.write_text()'s default newline handling translates '\n' to
        # os.linesep (CRLF on Windows), which would fight git on every save.
        # Use open(..., newline="") for Python 3.9 compat (Path.write_text's
        # `newline=` kwarg only landed in 3.10).
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="") as f:
            f.write(content)

    def exists(self, path) -> bool:
        return Path(path).exists()


class _RealRunner:
    def run(self, cmd, env, cwd):
        # encoding/errors explicit: PYTHONIOENCODING in `env` only governs the
        # CHILD process's own stdout encoding. The parent-side decode of the
        # captured bytes still uses locale.getpreferredencoding() (cp874 on
        # Thai Windows) unless told otherwise here — same class of bug the
        # regen-skill-surfaces.py errors="replace" reconfigure guards against.
        return subprocess.run(
            cmd, env=env, cwd=cwd, capture_output=True,
            text=True, encoding="utf-8", errors="replace",
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        prog="new-skill.py",
        description="Scaffold + register a new A-Wiki skill (registry-first, hook #15 safe).",
    )
    ap.add_argument("name", help="Skill name in kebab-case, e.g. my-new-skill")
    ap.add_argument(
        "--domain", required=True,
        help="Comma-separated domain(s) from the canonical VALID_DOMAINS set, e.g. code,debug",
    )
    ap.add_argument(
        "--phase", required=True,
        help="Lifecycle phase from the canonical VALID_LIFECYCLE_PHASES set, e.g. build",
    )
    ap.add_argument(
        "--category", default=DEFAULT_CATEGORY,
        help=f"Registry category (default: {DEFAULT_CATEGORY})",
    )
    ap.add_argument(
        "--description", default=None,
        help="Skill description (default: TODO placeholder mentioning the skill name)",
    )
    ap.add_argument(
        "--path-root", dest="path_root", default=DEFAULT_PATH_ROOT,
        help=f"Root directory the skill is created under (default: {DEFAULT_PATH_ROOT})",
    )
    ap.add_argument(
        "--apply", action="store_true",
        help="Write registry + SKILL.md + run regen-skill-surfaces.py (default: dry-run)",
    )
    return ap.parse_args(argv)


def build_config(args: argparse.Namespace) -> ScaffoldConfig:
    validate_kebab_case(args.name)
    domain = tuple(d.strip() for d in args.domain.split(",") if d.strip())
    validate_domains(domain)
    validate_phase(args.phase)

    description = args.description or (
        f"TODO: describe what the '{args.name}' skill does and when to use it."
    )

    return ScaffoldConfig(
        name=args.name,
        domain=domain,
        phase=args.phase,
        category=args.category,
        description=description,
        path_root=args.path_root,
        apply=args.apply,
    )


def main(argv: Optional[list[str]] = None) -> int:
    try:
        args = parse_args(argv)
        cfg = build_config(args)
    except ScaffoldError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    fs = _RealFS()
    runner = _RealRunner()
    recorder = StepRecorder()

    try:
        result = run_scaffold(
            cfg, fs=fs, runner=runner, recorder=recorder, repo_root=REPO_ROOT
        )
    except ScaffoldError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if not result.applied:
        print(f"[dry-run] would scaffold '{cfg.name}' -> {result.skill_md_path}")
        print("[dry-run] registry entry:")
        print(json.dumps(result.entry, indent=2, ensure_ascii=False))
        print("[dry-run] pass --apply to write registry + SKILL.md + run regen-skill-surfaces.py")
        return 0

    print(f"applied: registered '{cfg.name}' in skills-registry.json")
    print(f"applied: wrote {result.skill_md_path}")
    print(f"regen:       {'ok' if result.regen_ok else 'FAILED'}")
    print(f"regen --check: {'ok' if result.regen_check_ok else 'FAILED (drift)'}")

    if not (result.regen_ok and result.regen_check_ok):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
