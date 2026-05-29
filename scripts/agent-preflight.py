#!/usr/bin/env python3
"""
Portable preflight for every A-Wiki agent platform.

Run this at the start of a session when lifecycle hooks are missing or suspect:
    python scripts/agent-preflight.py
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from drive_path import get_drive_root


@dataclass(frozen=True)
class CheckResult:
    level: str
    name: str
    detail: str


EXPECTED_DRIVE_FOLDERS = [
    "raw",
    "waste-reports",
    "personal-tools",
    "ocr-feedback",
    "individual-tasks",
]

REQUIRED_HOOKS = [
    "check_bash_destructive_git.py",
    "check_bash_no_branch.py",
    "check_drive_link.py",
    "check_external_editor_drift.py",
    "check_raw_immutable.py",
    "check_secret_leak.py",
]

PREFLIGHT_DOCS = [
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    ".clinerules",
    ".cursorrules",
    ".windsurfrules",
    ".github/copilot-instructions.md",
]

HOOK_CONFIGS = [
    ".claude/settings.json",
    ".codex/hooks.json",
]


def run_git(args: list[str], timeout: int = 20) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        timeout=timeout,
    )


def run_python_script(args: list[str], timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        timeout=timeout,
    )


def line(result: CheckResult) -> str:
    return f"[{result.level}] {result.name} - {result.detail}"


def check_branch() -> CheckResult:
    proc = run_git(["branch", "--show-current"])
    branch = proc.stdout.strip() if proc.returncode == 0 else ""
    if branch == "main":
        return CheckResult("OK", "git branch", "main")
    return CheckResult("FAIL", "git branch", branch or "unknown; expected main")


def check_remote(skip_remote: bool = False) -> CheckResult:
    if skip_remote:
        return CheckResult("WARN", "origin/main reachability", "skipped by --skip-remote")
    proc = run_git(["ls-remote", "--exit-code", "origin", "refs/heads/main"], timeout=20)
    if proc.returncode == 0:
        return CheckResult("OK", "origin/main reachability", "reachable")
    detail = (proc.stderr or proc.stdout).strip().splitlines()
    return CheckResult("WARN", "origin/main reachability", detail[0] if detail else "unreachable")


def check_worktree() -> CheckResult:
    proc = run_git(["status", "--short"])
    if proc.returncode != 0:
        return CheckResult("FAIL", "working tree", "git status failed")
    lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
    if not lines:
        return CheckResult("OK", "working tree", "clean")
    return CheckResult("WARN", "working tree", f"{len(lines)} changed path(s)")


def check_external_data() -> CheckResult:
    drive_root = get_drive_root()
    missing = [name for name in EXPECTED_DRIVE_FOLDERS if not (drive_root / name).is_dir()]
    if missing:
        return CheckResult("FAIL", "A-Wiki-Data folders", f"missing: {', '.join(missing)} at {drive_root}")
    raw_count = sum(1 for item in (drive_root / "raw").rglob("*") if item.is_file())
    if raw_count <= 0:
        return CheckResult("FAIL", "A-Wiki-Data raw", f"no files at {drive_root / 'raw'}")
    secrets = drive_root / ".secrets"
    if not secrets.is_file():
        return CheckResult("FAIL", "Drive .secrets", f"missing at {secrets}")
    return CheckResult("OK", "A-Wiki-Data", f"{drive_root}; raw files={raw_count}; secrets present")


def check_generated_index() -> CheckResult:
    proc = run_python_script(["scripts/gen-index.py", "--check"], timeout=60)
    if proc.returncode == 0:
        return CheckResult("OK", "generated wiki context", "fresh")
    detail = (proc.stderr or proc.stdout).strip().splitlines()
    return CheckResult("FAIL", "generated wiki context", detail[0] if detail else "stale")


def check_hooks() -> CheckResult:
    missing = []
    for hook in REQUIRED_HOOKS:
        if not (REPO_ROOT / "scripts" / "hooks" / hook).is_file():
            missing.append(f"scripts/hooks/{hook}")
    if not (REPO_ROOT / "scripts" / "hooks_runner.py").is_file():
        missing.append("scripts/hooks_runner.py")
    if missing:
        return CheckResult("FAIL", "core hooks", "missing: " + ", ".join(missing))
    return CheckResult("OK", "core hooks", f"{len(REQUIRED_HOOKS)} required hook(s) present")


def collect_hook_commands(value) -> list[str]:
    commands: list[str] = []
    if isinstance(value, dict):
        command = value.get("command")
        if isinstance(command, str):
            commands.append(command)
        for child in value.values():
            commands.extend(collect_hook_commands(child))
    elif isinstance(value, list):
        for child in value:
            commands.extend(collect_hook_commands(child))
    return commands


def command_path_refs(command: str) -> list[str]:
    return re.findall(r"(?:scripts|\.claude|\.codex)[\\/][^'\"\s]+", command)


def check_hook_config_commands() -> CheckResult:
    issues: list[str] = []
    missing_configs: list[str] = []
    for rel in HOOK_CONFIGS:
        path = REPO_ROOT / rel
        if not path.is_file():
            missing_configs.append(rel)
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            issues.append(f"{rel} invalid JSON: {exc.msg}")
            continue
        for command in collect_hook_commands(data):
            if re.search(r"[A-Za-z]:[\\/]", command):
                issues.append(f"{rel} has non-portable absolute path: {command}")
            for ref in command_path_refs(command):
                cleaned = ref.strip("'\"").replace("\\", "/")
                if not (REPO_ROOT / cleaned).exists():
                    issues.append(f"{rel} points to missing path: {cleaned}")
    if issues:
        return CheckResult("FAIL", "hook command paths", "; ".join(issues[:5]))
    if missing_configs:
        return CheckResult("WARN", "hook command paths", "local config missing: " + ", ".join(missing_configs))
    return CheckResult("OK", "hook command paths", f"{len(HOOK_CONFIGS)} config file(s) resolve")


def check_instruction_drift() -> CheckResult:
    missing_files = []
    missing_preflight = []
    for rel in PREFLIGHT_DOCS:
        path = REPO_ROOT / rel
        if not path.is_file():
            missing_files.append(rel)
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if "scripts/agent-preflight.py" not in text:
            missing_preflight.append(rel)
    if missing_files or missing_preflight:
        parts = []
        if missing_files:
            parts.append("missing files: " + ", ".join(missing_files))
        if missing_preflight:
            parts.append("missing preflight line: " + ", ".join(missing_preflight))
        return CheckResult("FAIL", "platform instruction drift", "; ".join(parts))
    return CheckResult("OK", "platform instruction drift", "preflight documented across platform files")


def run_checks(skip_remote: bool = False) -> list[CheckResult]:
    return [
        check_branch(),
        check_remote(skip_remote=skip_remote),
        check_worktree(),
        check_external_data(),
        check_generated_index(),
        check_hooks(),
        check_hook_config_commands(),
        check_instruction_drift(),
    ]


def exit_code(results: list[CheckResult]) -> int:
    return 1 if any(result.level == "FAIL" for result in results) else 0


def print_mobile_checklist() -> None:
    print("")
    print("Mobile/manual fallback")
    print("- Confirm the repo is on main before editing.")
    print("- Pull latest origin/main before significant work.")
    print("- Confirm Google Drive A-Wiki-Data is mounted and raw/ is visible.")
    print("- Avoid editing raw/ and never paste secrets into chat, repo files, or commands.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run portable A-Wiki agent preflight checks.")
    parser.add_argument("--skip-remote", action="store_true", help="Skip network reachability check.")
    parser.add_argument("--mobile-checklist", action="store_true", help="Print only the manual fallback checklist.")
    args = parser.parse_args()

    if args.mobile_checklist:
        print_mobile_checklist()
        return 0

    results = run_checks(skip_remote=args.skip_remote)
    print("A-Wiki Agent Preflight")
    print("======================")
    for result in results:
        print(line(result))
    print_mobile_checklist()

    return exit_code(results)


if __name__ == "__main__":
    raise SystemExit(main())
