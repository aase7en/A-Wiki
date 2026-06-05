#!/usr/bin/env python3
"""One-command readiness verifier for a cloned A-Wiki workspace.

This is broader than `agent-preflight.py`: it checks whether the repo is ready
for actual A-Wiki work after setup-local has run.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class ReadyCheck:
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


def line(check: ReadyCheck) -> str:
    return f"[{check.level}] {check.name} - {check.detail}"


def exit_code(results: list[ReadyCheck]) -> int:
    return 1 if any(result.level == "FAIL" for result in results) else 0


def tail_detail(proc: subprocess.CompletedProcess[str]) -> str:
    text = (proc.stderr or proc.stdout or "").strip()
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines[-1] if lines else f"exit {proc.returncode}"


def check_agent_preflight(skip_remote: bool = False) -> ReadyCheck:
    args = [sys.executable, "scripts/agent-preflight.py"]
    if skip_remote:
        args.append("--skip-remote")
    proc = run_cmd(args, timeout=90)
    if proc.returncode == 0:
        return ReadyCheck("OK", "agent preflight", "passed")
    return ReadyCheck("FAIL", "agent preflight", tail_detail(proc))


def check_model_router_policy() -> ReadyCheck:
    proc = run_cmd([sys.executable, "scripts/model-router-policy.py", "--json"], timeout=30)
    if proc.returncode != 0:
        return ReadyCheck("FAIL", "model router policy", tail_detail(proc))
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        return ReadyCheck("FAIL", "model router policy", f"invalid JSON: {exc.msg}")
    policy_path = Path(payload.get("policy_path", ""))
    if not policy_path.is_file():
        return ReadyCheck("FAIL", "model router policy", f"missing output: {policy_path}")
    intel = "intel" if payload.get("intel_available") else "no intel cache"
    return ReadyCheck("OK", "model router policy", f"{policy_path} ({intel})")


def check_skill_evals() -> ReadyCheck:
    proc = run_cmd(["bash", "scripts/skillopt/run-awiki-evals.sh"], timeout=60)
    if proc.returncode == 0:
        passed = sum(1 for line in proc.stdout.splitlines() if line.startswith("PASS "))
        return ReadyCheck("OK", "skill evals", f"{passed} suite(s) passed")
    return ReadyCheck("FAIL", "skill evals", tail_detail(proc))


def check_skill_quality() -> ReadyCheck:
    proc = run_cmd([sys.executable, "scripts/skill-quality-report.py", "--json"], timeout=60)
    if proc.returncode != 0:
        return ReadyCheck("FAIL", "skill quality", tail_detail(proc))
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        return ReadyCheck("FAIL", "skill quality", f"invalid JSON: {exc.msg}")
    summary = payload.get("summary", {})
    fail = int(summary.get("FAIL", 0))
    warn = int(summary.get("WARN", 0))
    ok = int(summary.get("OK", 0))
    total = int(summary.get("total", 0))
    if fail:
        return ReadyCheck("FAIL", "skill quality", f"{fail} fail / {warn} warn / {ok} ok")
    detail = f"{total} skill(s): {ok} OK, {warn} WARN, 0 FAIL"
    return ReadyCheck("OK", "skill quality", detail)


def check_todo_hygiene() -> ReadyCheck:
    proc = run_cmd([sys.executable, "scripts/todo-health.py", "--json"], timeout=30)
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        return ReadyCheck("FAIL", "TODO hygiene", f"invalid JSON: {exc.msg}")
    findings = payload.get("findings", [])
    summary = payload.get("summary", {})
    first_fail = next((item for item in findings if item.get("level") == "FAIL"), None)
    if proc.returncode != 0 or first_fail:
        detail = first_fail.get("message", tail_detail(proc)) if first_fail else tail_detail(proc)
        return ReadyCheck("FAIL", "TODO hygiene", detail)
    warnings = sum(1 for item in findings if item.get("level") == "WARN")
    active = summary.get("active_open", 0)
    cap = summary.get("active_cap", 0)
    return ReadyCheck("OK", "TODO hygiene", f"{active}/{cap} active TODO(s), {warnings} warning(s)")


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


def check_codex_hooks_relative() -> ReadyCheck:
    path = REPO_ROOT / ".codex" / "hooks.json"
    if not path.is_file():
        return ReadyCheck("FAIL", "Codex hooks", ".codex/hooks.json missing; run bash scripts/setup-codex-hooks.sh")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return ReadyCheck("FAIL", "Codex hooks", f"invalid JSON: {exc.msg}")

    issues: list[str] = []
    commands = collect_hook_commands(data)
    for command in commands:
        if re.search(r"(^|\s)/(Users|home|Volumes|mnt)/", command) or re.search(r"[A-Za-z]:[\\/]", command):
            issues.append(f"absolute path: {command}")
    if issues:
        return ReadyCheck("FAIL", "Codex hooks", issues[0])
    return ReadyCheck("OK", "Codex hooks", f"{len(commands)} relative command(s)")


def check_wiki_index_db() -> ReadyCheck:
    db = REPO_ROOT / ".wiki-index.db"
    if not db.is_file():
        return ReadyCheck("FAIL", "wiki SQLite index", "missing .wiki-index.db; run python3 scripts/gen-index.py")
    if db.stat().st_size <= 0:
        return ReadyCheck("FAIL", "wiki SQLite index", ".wiki-index.db is empty")
    return ReadyCheck("OK", "wiki SQLite index", f"{db.stat().st_size} bytes")


def check_heavy_paths_ignored() -> ReadyCheck:
    gitignore = REPO_ROOT / ".gitignore"
    if not gitignore.is_file():
        return ReadyCheck("FAIL", "heavy/private path ignore", ".gitignore missing")
    text = gitignore.read_text(encoding="utf-8", errors="replace")
    required = ["raw", "raw/", "drive", ".tmp/", ".venv-*", "*.db-shm", "*.db-wal"]
    missing = [item for item in required if item not in text]
    if missing:
        return ReadyCheck("FAIL", "heavy/private path ignore", "missing: " + ", ".join(missing))
    return ReadyCheck("OK", "heavy/private path ignore", "raw/ drive/ .tmp/ .venv-* SQLite sidecars ignored")


def run_checks(skip_remote: bool = False, skip_evals: bool = False) -> list[ReadyCheck]:
    checks = [
        check_agent_preflight(skip_remote=skip_remote),
        check_wiki_index_db(),
        check_codex_hooks_relative(),
        check_model_router_policy(),
        check_heavy_paths_ignored(),
        check_todo_hygiene(),
        check_skill_quality(),
    ]
    if not skip_evals:
        checks.append(check_skill_evals())
    else:
        checks.append(ReadyCheck("WARN", "skill evals", "skipped by --skip-evals"))
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify this A-Wiki clone is ready for real work.")
    parser.add_argument("--skip-remote", action="store_true", help="Skip network reachability inside preflight.")
    parser.add_argument("--skip-evals", action="store_true", help="Skip deterministic skill eval suites.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args()

    results = run_checks(skip_remote=args.skip_remote, skip_evals=args.skip_evals)
    if args.json:
        print(json.dumps([check.__dict__ for check in results], ensure_ascii=False, indent=2))
    else:
        print("A-Wiki Readiness")
        print("================")
        for check in results:
            print(line(check))
    return exit_code(results)


if __name__ == "__main__":
    raise SystemExit(main())
