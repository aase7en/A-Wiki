#!/usr/bin/env python3
"""Generate a lightweight A-Wiki health digest for humans and CI artifacts."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class DigestCheck:
    level: str
    name: str
    detail: str


def run_cmd(args: list[str], timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        timeout=timeout,
    )


def file_age_days(path: Path) -> float | None:
    if not path.exists():
        return None
    return (time.time() - path.stat().st_mtime) / 86400


def count_markdown(root: Path) -> int:
    if not root.exists():
        return 0
    return sum(1 for path in root.rglob("*.md") if path.is_file())


def check_version_tracking() -> DigestCheck:
    version_path = REPO_ROOT / "VERSION"
    changelog = REPO_ROOT / "CHANGELOG.md"
    if not version_path.is_file():
        return DigestCheck("FAIL", "version tracking", "missing VERSION")
    version = version_path.read_text(encoding="utf-8").strip()
    if not version:
        return DigestCheck("FAIL", "version tracking", "VERSION is empty")
    if not changelog.is_file():
        return DigestCheck("FAIL", "version tracking", "missing CHANGELOG.md")
    if f"## {version}" not in changelog.read_text(encoding="utf-8", errors="replace"):
        return DigestCheck("WARN", "version tracking", f"{version} not found as a changelog heading")
    return DigestCheck("OK", "version tracking", version)


def check_context_freshness(max_age_days: int) -> DigestCheck:
    targets = [
        "wiki/context/wiki-overview.md",
        "wiki/context/knowledge-graph.md",
        "wiki/context/model-roster.conf",
    ]
    stale: list[str] = []
    missing: list[str] = []
    details: list[str] = []
    for rel in targets:
        path = REPO_ROOT / rel
        age = file_age_days(path)
        if age is None:
            missing.append(rel)
            continue
        details.append(f"{rel}={age:.1f}d")
        if age > max_age_days:
            stale.append(f"{rel} ({age:.1f}d)")
    if missing:
        return DigestCheck("FAIL", "context freshness", "missing: " + ", ".join(missing))
    if stale:
        return DigestCheck("WARN", "context freshness", "stale: " + ", ".join(stale))
    return DigestCheck("OK", "context freshness", ", ".join(details))


def check_privacy() -> DigestCheck:
    proc = run_cmd([sys.executable, "scripts/check-privacy.py"], timeout=60)
    if proc.returncode == 0:
        return DigestCheck("OK", "privacy scan", "no tracked personal data detected")
    detail = (proc.stdout or proc.stderr or "privacy scan failed").strip().splitlines()[-1]
    return DigestCheck("FAIL", "privacy scan", detail)


def check_todo_health() -> DigestCheck:
    proc = run_cmd([sys.executable, "scripts/todo-health.py", "--json"], timeout=30)
    if proc.returncode != 0:
        detail = (proc.stdout or proc.stderr or "todo-health failed").strip().splitlines()[-1]
        return DigestCheck("FAIL", "TODO health", detail)
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        return DigestCheck("FAIL", "TODO health", f"invalid JSON: {exc.msg}")
    summary = payload.get("summary", {})
    findings = payload.get("findings", [])
    fail = next((item for item in findings if item.get("level") == "FAIL"), None)
    if fail:
        return DigestCheck("FAIL", "TODO health", str(fail.get("message", "failed")))
    warns = sum(1 for item in findings if item.get("level") == "WARN")
    active = summary.get("active_open", 0)
    cap = summary.get("active_cap", 0)
    level = "WARN" if warns else "OK"
    return DigestCheck(level, "TODO health", f"{active}/{cap} active TODO(s), {warns} warning(s)")


def check_git_clean_tracked() -> DigestCheck:
    proc = run_cmd(["git", "status", "--short"], timeout=30)
    if proc.returncode != 0:
        return DigestCheck("WARN", "git status", "git status failed")
    lines = [line for line in proc.stdout.splitlines() if line.strip()]
    tracked = [line for line in lines if not line.startswith("?? ")]
    if tracked:
        return DigestCheck("WARN", "git status", f"{len(tracked)} tracked change(s) in workspace")
    return DigestCheck("OK", "git status", "no tracked workspace changes")


def wiki_stats() -> dict[str, int]:
    wiki = REPO_ROOT / "wiki"
    return {
        "wiki_markdown": count_markdown(wiki),
        "entities": count_markdown(wiki / "entities"),
        "concepts": count_markdown(wiki / "concepts"),
        "sources": count_markdown(wiki / "sources"),
        "synthesis": count_markdown(wiki / "synthesis"),
        "context": count_markdown(wiki / "context"),
    }


def collect(max_context_age_days: int) -> dict:
    checks = [
        check_version_tracking(),
        check_context_freshness(max_context_age_days),
        check_privacy(),
        check_todo_health(),
        check_git_clean_tracked(),
    ]
    stats = wiki_stats()
    summary = {
        "fail": sum(1 for check in checks if check.level == "FAIL"),
        "warn": sum(1 for check in checks if check.level == "WARN"),
        "ok": sum(1 for check in checks if check.level == "OK"),
    }
    return {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "version": (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()
        if (REPO_ROOT / "VERSION").is_file()
        else "",
        "summary": summary,
        "stats": stats,
        "checks": [check.__dict__ for check in checks],
    }


def render_markdown(payload: dict) -> str:
    lines = [
        "# A-Wiki Weekly Health Digest",
        "",
        f"- Generated: {payload['generated_at']}",
        f"- Version: {payload.get('version') or 'unknown'}",
        f"- Summary: {payload['summary']['ok']} OK, {payload['summary']['warn']} WARN, {payload['summary']['fail']} FAIL",
        "",
        "## Wiki stats",
        "",
        "| Metric | Count |",
        "|---|---:|",
    ]
    for key, value in payload["stats"].items():
        lines.append(f"| `{key}` | {value} |")
    lines.extend(["", "## Checks", "", "| Level | Check | Detail |", "|---|---|---|"])
    for check in payload["checks"]:
        detail = str(check["detail"]).replace("|", "\\|")
        lines.append(f"| {check['level']} | {check['name']} | {detail} |")
    lines.extend(
        [
            "",
            "## Operating rule",
            "",
            "This digest is evidence only. It must not auto-commit, edit `wiki/`, or touch real `drive/` secrets.",
        ]
    )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate A-Wiki health digest.")
    parser.add_argument("--out", help="Write Markdown digest to this path.")
    parser.add_argument("--json-out", help="Write JSON digest to this path.")
    parser.add_argument("--max-context-age-days", type=int, default=14)
    parser.add_argument("--fail-on-warn", action="store_true")
    parser.add_argument("--json", action="store_true", help="Print JSON to stdout instead of Markdown.")
    args = parser.parse_args()

    payload = collect(max_context_age_days=args.max_context_age_days)
    markdown = render_markdown(payload)

    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(markdown, encoding="utf-8")
    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(markdown, end="")

    if payload["summary"]["fail"]:
        return 1
    if args.fail_on_warn and payload["summary"]["warn"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
