#!/usr/bin/env python3
"""Truthful wiki health validation (A-Wiki vNext Phase 2 / P2.2).

Replaces the retired fail-open daily-maintenance check
(`gen-index --check 2>/dev/null || echo OK`) with real validation.

Contract:
  HARD errors (exit 1)          ADVISORIES (exit 0)
  -------------------------     --------------------------
  broken wikilinks              orphan pages
  invalid frontmatter           duplicate aliases
  stale generated context       dangling graph edges
  skill-surface drift

  The integration-registry check is reported as SKIPPED until the registry
  exists (Phase 3 kernel contract).

Usage:
  python scripts/health/wiki_health.py            # human summary, exit 0/1
  python scripts/health/wiki_health.py --json     # also writes .tmp/wiki-health/report.json
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
from markdown_code import strip_markdown_code

WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")

try:
    import yaml  # type: ignore  # R-P2-005: probe once, report skip if missing
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False
FRONTMATTER_FENCE = "---"


@dataclass
class CheckResult:
    name: str
    severity: str = "ok"  # ok | advisory | hard
    errors: list[str] = field(default_factory=list)
    advisories: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


@dataclass
class HealthReport:
    hard_errors: list[str] = field(default_factory=list)
    advisories: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    baselined_hard: list[str] = field(default_factory=list)  # legacy debt (ratchet)

    def exit_code(self) -> int:
        return 1 if self.hard_errors else 0


EXCLUDED_PAGE_DIRS = {"templates"}  # placeholder links ([[page-name]]) live in templates


def _md_files(root: Path) -> list[Path]:
    return sorted(
        p for p in root.rglob("*.md")
        if p.is_file() and not any(part in EXCLUDED_PAGE_DIRS for part in p.parts)
    )


def _resolution_indexes(wiki_root: Path) -> tuple[dict[str, Path], set[str]]:
    """Indexes for wikilink resolution, repo-wide.

    The wiki uses several link forms: bare slug ([[esp32]]), wiki-relative
    path ([[entities/iot/esp32]]), repo-relative path ([[wiki/concepts/x]]),
    and links to files outside wiki/ ([[agent-skills/...]]). Resolution is
    anchored at the repo root (wiki_root.parent); vendored/upstream dirs are
    excluded.
    """
    repo_root = wiki_root.parent
    skip = {".git", "_upstream", "node_modules", ".gitnexus", "drive", "raw"}
    index: dict[str, Path] = {}
    paths: set[str] = set()
    files: list[Path] = []
    for p in repo_root.rglob("*.md"):
        if not p.is_file() or any(part in skip for part in p.parts):
            continue
        files.append(p)
        index.setdefault(p.stem, p)
        paths.add(p.relative_to(repo_root).as_posix()[:-len(".md")])
    # Skills are real link targets: [[monte-carlo-quant-analysis]] /
    # [[a-router]] / [[theme-factory]] referenced from entity pages and
    # generated reports resolve to their SKILL.md (registry is the SSoT;
    # fall back to skill dir names when the registry is unreadable).
    try:
        reg_path = repo_root / "skills-registry.json"
        reg = json.loads(reg_path.read_text(encoding="utf-8"))
        for entry in reg.get("skills", []):
            name = entry.get("name")
            skill_path = entry.get("path")
            if name and skill_path:
                sp = repo_root / skill_path
                if sp.is_file():
                    index.setdefault(name, sp)
    except Exception:
        pass
    skills_root = repo_root / "skills"
    if skills_root.is_dir():
        for sp in skills_root.rglob("SKILL.md"):
            parts = sp.relative_to(skills_root).parts[:-1]
            for name in parts:  # every ancestor dir is a valid target
                index.setdefault(name, sp)
    # Exact file targets (with extension) resolve when the file exists
    # repo-relative ([[CLAUDE.md]], [[profile.md]]).
    for p in files:
        paths.add(p.relative_to(repo_root).as_posix())
    return index, paths


def _resolves(target: str, index: dict[str, Path], paths: set[str]) -> bool:
    if target in index or target in paths:
        return True
    if target.startswith("wiki/"):
        stripped = target[len("wiki/"):]
        return stripped in paths or stripped in index
    # wiki-relative form: [[entities/iot/esp32]] -> wiki/entities/iot/esp32
    return f"wiki/{target}" in paths


def check_wikilinks(wiki_root: Path) -> CheckResult:
    """[[target]] / [[path/to/target]] / [[target#a]] / [[t|display]] must resolve."""
    result = CheckResult("wikilinks")
    index, known_paths = _resolution_indexes(wiki_root)
    for page in _md_files(wiki_root):
        text = page.read_text(encoding="utf-8", errors="replace")
        # Code examples are not real links; share the same scanner as graph build.
        text = strip_markdown_code(text)
        for m in WIKILINK_RE.finditer(text):
            target = m.group(1).strip()
            if not target or target.startswith("http"):
                continue
            if not _resolves(target, index, known_paths):
                result.errors.append(
                    f"{page.relative_to(wiki_root).as_posix()}: broken wikilink [[{target}]]"
                )
    if result.errors:
        result.severity = "hard"
    return result


def _parse_frontmatter(text: str) -> tuple[dict | None, str | None]:
    """Return (mapping, error). Files without fences -> (None, None)."""
    if not text.startswith(FRONTMATTER_FENCE):
        return None, None
    parts = text.split("\n---", 2)
    if len(parts) < 2:
        return None, "unterminated frontmatter fence"
    raw = parts[0][len(FRONTMATTER_FENCE):]
    if not _YAML_AVAILABLE:
        return None, "SKIP: PyYAML unavailable"
    try:
        data = yaml.safe_load(raw)
    except Exception as e:  # yaml.YAMLError
        return None, f"unparseable frontmatter: {e}"
    if data is None:
        return {}, None
    if not isinstance(data, dict):
        return None, "frontmatter is not a mapping"
    return data, None


def check_frontmatter(wiki_root: Path) -> CheckResult:
    result = CheckResult("frontmatter")
    if not _YAML_AVAILABLE:
        result.skipped.append("frontmatter validation — PyYAML unavailable (R-P2-005)")
        return result
    for page in _md_files(wiki_root):
        text = page.read_text(encoding="utf-8", errors="replace")
        _, err = _parse_frontmatter(text)
        if err:
            result.errors.append(f"{page.relative_to(wiki_root).as_posix()}: {err}")
    if result.errors:
        result.severity = "hard"
    return result


def check_duplicate_aliases(wiki_root: Path) -> CheckResult:
    result = CheckResult("duplicate-aliases")
    seen: dict[str, str] = {}
    for page in _md_files(wiki_root):
        text = page.read_text(encoding="utf-8", errors="replace")
        fm, _ = _parse_frontmatter(text)
        if not fm:
            continue
        aliases = fm.get("aliases", [])
        if isinstance(aliases, str):
            aliases = [aliases]
        for alias in aliases or []:
            key = str(alias).strip().lower()
            if not key:
                continue
            if key in seen and seen[key] != page.relative_to(wiki_root).as_posix():
                result.advisories.append(
                    f"alias '{alias}' used by both {seen[key]} and {page.relative_to(wiki_root).as_posix()}"
                )
            else:
                seen[key] = page.relative_to(wiki_root).as_posix()
    if result.advisories:
        result.severity = "advisory"
    return result


def check_graph_edges(wiki_root: Path, graph_path: Path) -> CheckResult:
    """Dangling graph edges are advisories (generated graph; regen self-heals).

    Real schema (.wiki-graph.json): nodes carry `path` (repo-relative);
    edges carry `from`/`to` + a `broken` flag. Disk is the authority — an
    endpoint whose file no longer exists, or an edge flagged broken by the
    generator, is reported.
    """
    result = CheckResult("graph-edges")
    if not graph_path.exists():
        return result
    try:
        data = json.loads(graph_path.read_text(encoding="utf-8"))
    except Exception as e:
        result.advisories.append(f"graph unreadable ({e}) — regen will rebuild it")
        result.severity = "advisory"
        return result
    repo_root = graph_path.parent
    for edge in data.get("edges", []):
        if not isinstance(edge, dict):
            continue
        if edge.get("broken"):
            result.advisories.append(
                f"graph flags broken link {edge.get('from')} -> {edge.get('to')}"
            )
            continue
        src = edge.get("from") or edge.get("source")
        dst = edge.get("to") or edge.get("target")
        for ref in (src, dst):
            if ref and not (repo_root / ref).exists():
                result.advisories.append(
                    f"dangling edge {edge.get('from')} -> {edge.get('to')} (missing {ref})"
                )
                break
    if result.advisories:
        result.severity = "advisory"
    return result


def check_orphans(wiki_root: Path) -> CheckResult:
    """Pages with no inbound wikilink are advisories (report-only by policy)."""
    result = CheckResult("orphans")
    pages = _md_files(wiki_root)
    linked: set[str] = set()
    for page in pages:
        text = page.read_text(encoding="utf-8", errors="replace")
        text = strip_markdown_code(text)
        for m in WIKILINK_RE.finditer(text):
            target = m.group(1).strip()
            if target and not target.startswith("http"):
                linked.add(target.removeprefix("wiki/"))
    for page in pages:
        rel = page.relative_to(wiki_root).as_posix()[:-len(".md")]
        if page.stem not in linked and rel not in linked:
            result.advisories.append(f"orphan page (no inbound wikilink): {page.relative_to(wiki_root).as_posix()}")
    if result.advisories:
        result.severity = "advisory"
    return result


def _subprocess_check(name: str, cmd: list[str], repo_root: Path) -> CheckResult:
    """Run an existing authoritative check; non-zero exit = hard error."""
    result = CheckResult(name)
    try:
        proc = subprocess.run(
            cmd, cwd=repo_root, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=300,
        )
    except Exception as e:
        result.errors.append(f"{name}: failed to run ({e})")
        result.severity = "hard"
        return result
    if proc.returncode != 0:
        tail = (proc.stdout + proc.stderr).strip().splitlines()[:30]
        result.errors.append(f"{name}: {' | '.join(tail) or 'non-zero exit'}")
        result.severity = "hard"
    return result


def check_generated_context(repo_root: Path) -> CheckResult:
    return _subprocess_check(
        "generated-context",
        [sys.executable, "scripts/gen-index.py", "--no-chain", "--check"],
        repo_root,
    )


def check_skill_surfaces(repo_root: Path) -> CheckResult:
    return _subprocess_check(
        "skill-surfaces",
        [sys.executable, "scripts/regen-skill-surfaces.py", "--check"],
        repo_root,
    )


def check_integrations(repo_root: Path) -> CheckResult:
    """Integration-registry references — SKIPPED until the registry exists (Phase 3)."""
    result = CheckResult("integrations")
    if not (repo_root / "config" / "integrations.yaml").exists():
        result.advisories = []
        return result
    return _subprocess_check(
        "integrations",
        [sys.executable, "scripts/health/validate_integrations.py"],
        repo_root,
    )


def _hard_key(error: str) -> str:
    """Stable, platform-independent ratchet identity: 'page::target'.

    Backslashes are normalized to forward slashes so Windows-generated
    baselines match Linux/macOS CI (R-P2-004).
    """
    error = error.replace("\\", "/")
    page, _, rest = error.partition(": ")
    target = rest.split("[[")[-1].rstrip("]") if "[[" in rest else rest
    return f"{page}::{target}"


def run_all(
    repo_root: Path,
    slow_checks: bool = True,
    json_path: Path | None = None,
    baseline_path: Path | None = None,
) -> HealthReport:
    wiki_root = repo_root / "wiki"
    report = HealthReport()

    checks: list[CheckResult] = [
        check_wikilinks(wiki_root),
        check_frontmatter(wiki_root),
        check_duplicate_aliases(wiki_root),
        check_graph_edges(wiki_root, repo_root / ".wiki-graph.json"),
        check_orphans(wiki_root),
    ]
    if slow_checks:
        checks.append(check_generated_context(repo_root))
        checks.append(check_skill_surfaces(repo_root))
    else:
        report.skipped.append("generated-context + skill-surfaces (slow checks disabled)")

    integ = check_integrations(repo_root)
    if integ.severity == "ok" and not (repo_root / "config" / "integrations.yaml").exists():
        report.skipped.append("integration registry check (registry arrives in Phase 3)")
    else:
        checks.append(integ)

    baseline_keys: set[str] = set()
    if baseline_path and baseline_path.exists():
        baseline_keys = {
            line.strip() for line in
            baseline_path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.startswith("#")
        }

    for c in checks:
        for s in c.skipped:
            report.skipped.append(s)
        for e in c.errors:
            full = f"[{c.name}] {e}"
            if baseline_keys and _hard_key(full) in baseline_keys:
                report.baselined_hard.append(full)
            else:
                report.hard_errors.append(full)
        for a in c.advisories:
            report.advisories.append(f"[{c.name}] {a}")

    if json_path:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps({
            "hard_errors": report.hard_errors,
            "baselined_hard": report.baselined_hard,
            "advisories": report.advisories,
            "skipped": report.skipped,
            "exit_code": report.exit_code(),
        }, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Truthful A-Wiki health check")
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--json", action="store_true",
                        help="write .tmp/wiki-health/report.json")
    parser.add_argument("--fast", action="store_true", help="skip slow subprocess checks")
    parser.add_argument("--baseline", type=Path, default=None,
                        help="file of known hard-error keys (legacy-debt ratchet)")
    args = parser.parse_args(argv)

    json_path = args.repo_root / ".tmp" / "wiki-health" / "report.json" if args.json else None
    report = run_all(
        args.repo_root, slow_checks=not args.fast,
        json_path=json_path, baseline_path=args.baseline,
    )

    for e in report.hard_errors:
        print(f"HARD: {e}")
    for e in report.baselined_hard:
        print(f"debt: {e}  (baseline)")
    for a in report.advisories:
        print(f"adv : {a}")
    for s in report.skipped:
        print(f"skip: {s}")
    print(f"wiki-health: {len(report.hard_errors)} hard error(s), "
          f"{len(report.baselined_hard)} baselined, {len(report.advisories)} advisory(ies)")
    return report.exit_code()


if __name__ == "__main__":
    sys.exit(main())
