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
import hashlib
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

from skills_registry import (  # noqa: E402
    VALID_DOMAINS, VALID_INVOCATIONS, VALID_LIFECYCLE_PHASES, VALID_STATUSES,
)
from skills_registry.scan import parse_frontmatter  # noqa: E402

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
    version: str = "1.0.0"
    agents: tuple[str, ...] = ("all",)
    status: str = "canonical"
    invocation: str = "manual"
    skill_md: Optional[str] = None
    artifact_sha256: Optional[str] = None


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
    """Build the skills-registry.json entry. Pure function of cfg — no I/O.

    Emits the full v2 key set so a scaffolded entry is shape-identical to a
    hand-written sibling. The five v2 fields below (invocation, th_description,
    when_to_use, examples, invocation_hint) were missing, so every scaffolded
    skill landed with a narrower shape than the registry it joined — invisible
    in the dashboard Skills view and in gen_hermes, which dump whole records.
    Defaults are valid-but-obviously-provisional; the author refines them.
    """
    return {
        "name": cfg.name,
        "aliases": [],
        "domain": list(cfg.domain),
        "lifecycle_phase": cfg.phase,
        "category": cfg.category,
        "source": "repo",
        "path": f"{cfg.path_root}/{cfg.name}/SKILL.md",
        "agents": list(cfg.agents),
        "version": cfg.version,
        "status": cfg.status,
        "description": cfg.description,
        "invocation": cfg.invocation,
        "th_description": cfg.description,
        "when_to_use": cfg.description,
        "examples": [],
        "invocation_hint": f"/{cfg.name}",
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


def _validate_exact_artifact(cfg: ScaffoldConfig) -> None:
    """Fail closed if exact-mode content/hash/frontmatter disagree with cfg."""
    if cfg.skill_md is None:
        if cfg.artifact_sha256 is not None:
            raise ScaffoldError("artifact sha256 requires exact skill_md content")
        return
    if not cfg.artifact_sha256:
        raise ScaffoldError("exact skill artifact requires expected sha256")
    actual = hashlib.sha256(cfg.skill_md.encode("utf-8")).hexdigest()
    if actual.lower() != cfg.artifact_sha256.lower():
        raise ScaffoldError(
            f"skill artifact sha256 mismatch: expected {cfg.artifact_sha256}, got {actual}")

    fm = parse_frontmatter(cfg.skill_md)
    expected = {
        "name": cfg.name,
        "description": cfg.description,
        "version": cfg.version,
        "domain": list(cfg.domain),
        "lifecycle_phase": cfg.phase,
        "category": cfg.category,
        "agents": list(cfg.agents),
        "status": cfg.status,
        "invocation": cfg.invocation,
    }
    for key, value in expected.items():
        if fm.get(key) != value:
            raise ScaffoldError(
                f"exact skill frontmatter {key!r} mismatch: expected {value!r}, got {fm.get(key)!r}")


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
    _validate_exact_artifact(cfg)

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
    fs.write_text(skill_md_path, cfg.skill_md if cfg.skill_md is not None else render_skill_md(cfg))

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
        "--domain", default=None,
        help="Comma-separated domain(s); required for scaffold mode, derived from --skill-file in exact mode",
    )
    ap.add_argument(
        "--phase", default=None,
        help="Lifecycle phase; required for scaffold mode, derived from --skill-file in exact mode",
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
        "--skill-file", dest="skill_file", default=None,
        help="Install this exact evaluated SKILL.md instead of rendering a scaffold",
    )
    ap.add_argument(
        "--expected-sha256", dest="expected_sha256", default=None,
        help="Required with --skill-file; content address that must match before any write",
    )
    ap.add_argument(
        "--apply", action="store_true",
        help="Write registry + SKILL.md + run regen-skill-surfaces.py (default: dry-run)",
    )
    return ap.parse_args(argv)


def _tuple_field(value: Any, field: str) -> tuple[str, ...]:
    if isinstance(value, list):
        items = tuple(str(v).strip() for v in value if str(v).strip())
    elif isinstance(value, str) and value.strip():
        items = (value.strip(),)
    else:
        items = ()
    if not items:
        raise ScaffoldError(f"exact skill frontmatter requires non-empty {field}")
    return items


def build_config(
    args: argparse.Namespace, *,
    skill_md: Optional[str] = None,
    artifact_sha256: Optional[str] = None,
) -> ScaffoldConfig:
    validate_kebab_case(args.name)

    if skill_md is not None:
        expected = args.expected_sha256
        if not expected or not re.fullmatch(r"[0-9A-Fa-f]{64}", expected):
            raise ScaffoldError("--skill-file requires a valid --expected-sha256")
        if not artifact_sha256 or artifact_sha256.lower() != expected.lower():
            raise ScaffoldError(
                f"skill artifact sha256 mismatch: expected {expected}, got {artifact_sha256}")
        fm = parse_frontmatter(skill_md)
        if fm.get("name") != args.name:
            raise ScaffoldError(
                f"exact skill frontmatter name mismatch: expected {args.name!r}, got {fm.get('name')!r}")
        domain = _tuple_field(fm.get("domain"), "domain")
        phase = str(fm.get("lifecycle_phase") or "")
        validate_domains(domain)
        validate_phase(phase)
        if args.domain:
            requested = tuple(d.strip() for d in args.domain.split(",") if d.strip())
            if requested != domain:
                raise ScaffoldError(f"--domain {requested!r} disagrees with exact artifact {domain!r}")
        if args.phase and args.phase != phase:
            raise ScaffoldError(f"--phase {args.phase!r} disagrees with exact artifact {phase!r}")

        description = fm.get("description")
        version = fm.get("version")
        category = fm.get("category")
        agents = _tuple_field(fm.get("agents"), "agents")
        status = fm.get("status")
        invocation = fm.get("invocation", "manual")
        for field, value in (("description", description), ("version", version),
                             ("category", category), ("status", status)):
            if not isinstance(value, str) or not value:
                raise ScaffoldError(f"exact skill frontmatter requires {field}")
        if status not in VALID_STATUSES:
            raise ScaffoldError(f"invalid skill status {status!r}")
        if invocation not in VALID_INVOCATIONS:
            raise ScaffoldError(f"invalid skill invocation {invocation!r}")
        if args.description and args.description != description:
            raise ScaffoldError("--description disagrees with exact artifact frontmatter")
        if args.category != DEFAULT_CATEGORY and args.category != category:
            raise ScaffoldError("--category disagrees with exact artifact frontmatter")

        return ScaffoldConfig(
            name=args.name, domain=domain, phase=phase, category=category,
            description=description, path_root=args.path_root, apply=args.apply,
            version=version, agents=agents, status=status, invocation=invocation,
            skill_md=skill_md, artifact_sha256=artifact_sha256.lower(),
        )

    if args.skill_file:
        raise ScaffoldError("--skill-file content was not loaded")
    if args.expected_sha256:
        raise ScaffoldError("--expected-sha256 requires --skill-file")
    if not args.domain or not args.phase:
        raise ScaffoldError("scaffold mode requires --domain and --phase")
    domain = tuple(d.strip() for d in args.domain.split(",") if d.strip())
    validate_domains(domain)
    validate_phase(args.phase)

    description = args.description or (
        f"TODO: describe what the '{args.name}' skill does and when to use it."
    )

    return ScaffoldConfig(
        name=args.name, domain=domain, phase=args.phase, category=args.category,
        description=description, path_root=args.path_root, apply=args.apply,
    )


def main(argv: Optional[list[str]] = None) -> int:
    try:
        args = parse_args(argv)
        skill_md = None
        artifact_sha256 = None
        if args.skill_file:
            try:
                raw = Path(args.skill_file).read_bytes()
                skill_md = raw.decode("utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                raise ScaffoldError(f"cannot read exact skill artifact: {exc}") from exc
            artifact_sha256 = hashlib.sha256(raw).hexdigest()
        cfg = build_config(args, skill_md=skill_md, artifact_sha256=artifact_sha256)
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
