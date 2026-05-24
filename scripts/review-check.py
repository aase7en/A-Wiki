#!/usr/bin/env python3
"""
review-check.py — Skeptical Reviewer Agent (Phase 5)

Runs 6 deterministic layers against the wiki + scripts tree and produces
wiki/context/review-report.md.

Usage:
    python3 scripts/review-check.py              # full review
    python3 scripts/review-check.py --layers L1,L3,L5  # selective
    python3 scripts/review-check.py --strict     # exit 1 on any failure
"""
from __future__ import annotations
import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
WIKI_DIR = REPO_ROOT / "wiki"
SKILLS_DIR = REPO_ROOT / "skills"
CONTEXT_DIR = WIKI_DIR / "context"
REPORT_PATH = CONTEXT_DIR / "review-report.md"

RESULT_ICONS = {"pass": "✓", "warn": "⚠", "fail": "❌"}


def check_script_guard(path: Path) -> bool:
    """L1: Check .py has `if __name__` guard or is import-only."""
    text = path.read_text(encoding="utf-8", errors="replace")
    if "__name__" in text and '"__main__"' in text.replace("'", '"'):
        return True
    # Allow tiny import-only files
    if len(text.strip().splitlines()) < 5 and "import" in text:
        return True
    return False


def check_frontmatter(path: Path) -> list[str]:
    """L2: Check frontmatter has title, type, tags."""
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---"):
        return ["no frontmatter (missing --- delimiter)"]
    end = text.find("\n---", 3)
    if end == -1:
        return ["unclosed frontmatter"]
    raw = text[3:end].strip()
    issues: list[str] = []
    for key in ("title", "type", "tags"):
        if f"{key}:" not in raw:
            issues.append(f"missing frontmatter key: {key}")
    return issues


def check_wiki_links(path: Path) -> list[str]:
    """L3: Validate [[wiki-links]] and relative markdown links resolve."""
    text = path.read_text(encoding="utf-8", errors="replace")
    issues: list[str] = []
    # [[link]] syntax
    for m in re.finditer(r'\[\[([^\]]+?)\]\]', text):
        target = m.group(1).strip()
        if target.startswith("http"):
            continue
        # Resolve: could be filename, path relative, or slug
        resolved = resolve_link_target(target, path)
        if resolved is None:
            issues.append(f"broken link: [[{target}]]")
    # [text](path) relative links (skip http/https/anchors)
    for m in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', text):
        href = m.group(2)
        if href.startswith(("http", "#", "mailto:")):
            continue
        resolved = resolve_link_target(href, path)
        if resolved is None:
            issues.append(f"broken link: [{m.group(1)}]({href})")
    return issues


def resolve_link_target(target: str, origin: Path) -> Path | None:
    """Try to resolve a wiki link to an existing file."""
    # Absolute from wiki root (slug)
    candidates: list[Path] = []
    # Try as slug anywhere under wiki/
    for md in WIKI_DIR.rglob("*.md"):
        if md.stem == target:
            candidates.append(md)
    # Try as relative path from origin
    relative = origin.parent / target
    relative_md = relative
    if not relative_md.suffix:
        relative_md = relative_md.with_suffix(".md")
    if relative_md.exists():
        candidates.append(relative_md)
    # Try as path from wiki root
    root_path = WIKI_DIR / target
    root_md = root_path
    if not root_md.suffix:
        root_md = root_md.with_suffix(".md")
    if root_md.exists():
        candidates.append(root_md)
    # Deduplicate
    seen = set()
    deduped: list[Path] = []
    for c in candidates:
        s = str(c.resolve())
        if s not in seen:
            seen.add(s)
            deduped.append(c)
    return deduped[0] if deduped else None


def check_orphan(path: Path) -> bool:
    """L4: Check if a wiki page is referenced by any other wiki page."""
    slug = path.stem
    if slug in ("index", "README", "Home"):
        return False  # root pages exempt
    for other in WIKI_DIR.rglob("*.md"):
        if other.resolve() == path.resolve():
            continue
        text = other.read_text(encoding="utf-8", errors="replace")
        if f"[[{slug}]]" in text or f"/{slug}" in text or f"{slug}.md" in text:
            return False
    return True


def check_skill_readme(path: Path) -> bool:
    """L5: Check skills/* subdirectories have a README.md."""
    return (path / "README.md").exists()


def check_quality(path: Path) -> list[str]:
    """L6: Check entity/concept pages have meaningful content."""
    text = path.read_text(encoding="utf-8", errors="replace")
    issues: list[str] = []
    # Strip frontmatter
    body = text
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            body = text[end + 4:].strip()
    # Check body length
    body_text = re.sub(r'[#*>\[\]\-_`\n]', '', body).strip()
    if len(body_text) < 50:
        issues.append("body too short (<50 chars after stripping markup)")
    # Check for TL;DR line
    if re.search(r'TL;DR|tldr|บทสรุป', body, re.IGNORECASE) is None:
        issues.append("missing TL;DR line")
    return issues


def run_l1() -> tuple[list[str], list[str], list[str]]:
    """Script health guard check."""
    passed: list[str] = []
    warned: list[str] = []
    failed: list[str] = []
    for py in sorted(SCRIPTS_DIR.rglob("*.py")):
        # Skip __pycache__
        if "__pycache__" in py.parts:
            continue
        rel = str(py.relative_to(REPO_ROOT))
        # Cache files and __init__.py are exempt
        if py.name == "__init__.py":
            passed.append(f"{rel} (init)")
            continue
        if py.name.startswith("._") or py.name.startswith("."):
            continue
        ok = check_script_guard(py)
        if ok:
            passed.append(f"{rel} has `if __name__` guard")
        else:
            failed.append(f"{rel} missing `if __name__ == '__main__'` guard")
    return passed, warned, failed


def run_l2() -> tuple[list[str], list[str], list[str]]:
    """Frontmatter completeness."""
    passed: list[str] = []
    warned: list[str] = []
    failed: list[str] = []
    for md in sorted(WIKI_DIR.rglob("*.md")):
        if md.name == "README.md":
            continue
        rel = str(md.relative_to(REPO_ROOT))
        issues = check_frontmatter(md)
        if not issues:
            passed.append(f"{rel} complete")
        else:
            for i in issues:
                failed.append(f"{rel}: {i}")
    return passed, warned, failed


def run_l3() -> tuple[list[str], list[str], list[str]]:
    """Link integrity."""
    passed: list[str] = []
    warned: list[str] = []
    failed: list[str] = []
    for md in sorted(WIKI_DIR.rglob("*.md")):
        rel = str(md.relative_to(REPO_ROOT))
        issues = check_wiki_links(md)
        if not issues:
            passed.append(f"{rel} links OK")
        else:
            for i in issues:
                failed.append(f"{rel}: {i}")
    return passed, warned, failed


def run_l4() -> tuple[list[str], list[str], list[str]]:
    """Orphan detection (entity/concept pages only)."""
    passed: list[str] = []
    warned: list[str] = []
    failed: list[str] = []
    for md in sorted(WIKI_DIR.rglob("*.md")):
        parts = md.relative_to(WIKI_DIR).parts
        if len(parts) < 3:
            continue
        section = parts[0]
        if section not in ("entities", "concepts"):
            continue
        rel = str(md.relative_to(REPO_ROOT))
        if check_orphan(md):
            warned.append(f"{rel} appears orphaned (no incoming links)")
        else:
            passed.append(f"{rel} has incoming links")
    return passed, warned, failed


def run_l5() -> tuple[list[str], list[str], list[str]]:
    """Skill directory README check."""
    passed: list[str] = []
    warned: list[str] = []
    failed: list[str] = []
    if not SKILLS_DIR.exists():
        warned.append("skills/ directory does not exist")
        return passed, warned, failed
    for subdir in sorted(SKILLS_DIR.iterdir()):
        if not subdir.is_dir():
            continue
        rel = str(subdir.relative_to(REPO_ROOT))
        # Check up to 2 levels deep
        dirs_to_check = [subdir]
        for child in sorted(subdir.iterdir()):
            if child.is_dir():
                dirs_to_check.append(child)
        for d in dirs_to_check:
            rel_d = str(d.relative_to(REPO_ROOT))
            if check_skill_readme(d):
                passed.append(f"{rel_d}/ has README.md")
            else:
                failed.append(f"{rel_d}/ missing README.md")
    return passed, warned, failed


def run_l6() -> tuple[list[str], list[str], list[str]]:
    """Quality floor for entities + concepts."""
    passed: list[str] = []
    warned: list[str] = []
    failed: list[str] = []
    for md in sorted(WIKI_DIR.rglob("*.md")):
        parts = md.relative_to(WIKI_DIR).parts
        if len(parts) < 3:
            continue
        section = parts[0]
        if section not in ("entities", "concepts"):
            continue
        rel = str(md.relative_to(REPO_ROOT))
        issues = check_quality(md)
        if not issues:
            passed.append(f"{rel} meets quality floor")
        else:
            for i in issues:
                failed.append(f"{rel}: {i}")
    return passed, warned, failed


LAYER_REGISTRY = {
    "L1": ("Script Health (if __name__ guard)", run_l1),
    "L2": ("Frontmatter Completeness (title, type, tags)", run_l2),
    "L3": ("Link Integrity (wiki links resolve)", run_l3),
    "L4": ("Orphan Detection (entity/concept incoming links)", run_l4),
    "L5": ("Skill README Check (README.md present)", run_l5),
    "L6": ("Quality Floor (body length, TL;DR)", run_l6),
}


def write_report(
    layer_results: dict[str, tuple[list[str], list[str], list[str]]],
    layer_names: dict[str, str],
) -> str:
    """Write review-report.md and return it as a string."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines: list[str] = [
        f"# Review Report — {now}",
        "",
    ]
    total_pass = sum(len(p) for p, w, f in layer_results.values())
    total_warn = sum(len(w) for p, w, f in layer_results.values())
    total_fail = sum(len(f) for p, w, f in layer_results.values())
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- {RESULT_ICONS['pass']} Passed: {total_pass}")
    lines.append(f"- {RESULT_ICONS['warn']} Warnings: {total_warn}")
    lines.append(f"- {RESULT_ICONS['fail']} Failures: {total_fail}")
    lines.append("")

    # Failures first
    has_content = False
    for lid in sorted(layer_results):
        p, w, f = layer_results[lid]
        if f:
            has_content = True
            lines.append("---")
            lines.append("")
            lines.append(f"## ❌ {lid}: {layer_names[lid]} — Failures")
            lines.append("")
            for item in f:
                lines.append(f"- {item}")
            lines.append("")

    # Warnings next
    for lid in sorted(layer_results):
        p, w, f = layer_results[lid]
        if w:
            has_content = True
            lines.append("---")
            lines.append("")
            lines.append(f"## ⚠ {lid}: {layer_names[lid]} — Warnings")
            lines.append("")
            for item in w:
                lines.append(f"- {item}")
            lines.append("")

    # Passed (compact)
    if total_pass > 0:
        has_content = True
        lines.append("---")
        lines.append("")
        lines.append(f"## ✓ Passed Checks ({total_pass} total)")
        lines.append("")
        for lid in sorted(layer_results):
            p, w, f = layer_results[lid]
            if p:
                line_count = len(p)
                lines.append(f"- **{lid}**: {line_count} passed")
        lines.append("")

    if not has_content:
        lines.append("*No checks were run.*")
        lines.append("")

    lines.append("---")
    lines.append("*Auto-generated by `scripts/review-check.py`*")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Skeptical Reviewer — deterministic wiki health checks")
    ap.add_argument("--layers", type=str, default="",
                    help="Comma-separated layer IDs to run (default: all). E.g. L1,L3,L5")
    ap.add_argument("--strict", action="store_true",
                    help="Exit 1 if any failure is found")
    args = ap.parse_args()

    selected_layers = sorted(LAYER_REGISTRY.keys())
    if args.layers:
        requested = [x.strip().upper() for x in args.layers.split(",")]
        selected_layers = [l for l in selected_layers if l in requested]
        if not selected_layers:
            print(f"❌ No valid layers in --layers. Available: {', '.join(LAYER_REGISTRY.keys())}")
            return 1

    CONTEXT_DIR.mkdir(parents=True, exist_ok=True)

    results: dict[str, tuple[list[str], list[str], list[str]]] = {}
    layer_names: dict[str, str] = {}
    for lid in selected_layers:
        name, func = LAYER_REGISTRY[lid]
        layer_names[lid] = name
        print(f"  🔍 Running {lid}: {name}...")
        p, w, f = func()
        results[lid] = (p, w, f)
        icon = RESULT_ICONS["fail"] if f else (RESULT_ICONS["warn"] if w else RESULT_ICONS["pass"])
        print(f"    {icon} {len(p)} passed, {len(w)} warned, {len(f)} failed")

    report = write_report(results, layer_names)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"\n📄 Report written: {REPORT_PATH.relative_to(REPO_ROOT)}")
    print(report)

    total_fail = sum(len(f) for p, w, f in results.values())
    if args.strict and total_fail > 0:
        print(f"\n❌ --strict: {total_fail} failures found, exiting 1")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())