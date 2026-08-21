#!/usr/bin/env python3
"""
Portable preflight for every A-Wiki agent platform.

Run this at the start of a session when lifecycle hooks are missing or suspect:
    python scripts/agent-preflight.py
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


def _expected_drive_folders():
    """Drive layout per LAYOUT.md (restructure 2026-08-06): waste-reports
    lives under the hospital dir (AWIKI_HOSPITAL_DIR), not at the root."""
    import os
    hospital = os.environ.get("AWIKI_HOSPITAL_DIR", "")
    if not hospital:
        # Machines keep this in drive/.env (private layer). Read ONLY this
        # key — never load or print the rest of that file.
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            from drive_path import get_drive_root
            env_file = get_drive_root() / ".env"
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if line.startswith("AWIKI_HOSPITAL_DIR="):
                    hospital = line.split("=", 1)[1].strip()
                    break
        except Exception:
            pass
    hospital = hospital or "hospital-main"
    return [
        "raw",
        f"{hospital}/waste-reports",
        "personal-tools",
        "ocr-feedback",
        "individual-tasks",
    ]


EXPECTED_DRIVE_FOLDERS = _expected_drive_folders()

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
    # GitHub Actions checks out a detached HEAD; the real branch lives in
    # GITHUB_REF_NAME. Detached-at-main on CI satisfies the main-only policy.
    # A "N/merge" ref is a pull_request event's merge commit — the candidate
    # main state under review — so PR CI is a legitimate main-policy context.
    # Any other branch still fails.
    if not branch and os.environ.get("GITHUB_ACTIONS") == "true":
        ref = os.environ.get("GITHUB_REF_NAME", "")
        if ref == "main":
            return CheckResult("OK", "git branch", "detached HEAD on CI (GITHUB_REF_NAME=main)")
        if re.fullmatch(r"\d+/merge", ref or ""):
            return CheckResult("OK", "git branch", f"PR merge ref on CI ({ref}) — candidate main under review")
        return CheckResult("FAIL", "git branch", f"CI ref {ref or 'unknown'}; expected main")
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


def check_session_handoff() -> CheckResult:
    return CheckResult(
        "WARN",
        "cross-device handoff",
        "close old AI/Obsidian sessions before editing on another device; run python3 scripts/sync.py --now first",
    )


def check_external_data() -> CheckResult:
    drive_root = get_drive_root()
    # The drive layer is OPTIONAL (CI / fresh clones have none). Only a
    # PROVEN drive (has raw/ or .secrets content) can FAIL on layout —
    # an auto-created fallback dir is a WARN, not a defect.
    import os as _os
    if _os.environ.get("CI") == "true":
        return CheckResult("WARN", "A-Wiki-Data",
                           "CI runner — private drive layer not applicable")
    has_real_drive = (drive_root / "raw").is_dir() or (drive_root / ".secrets").is_file()
    if not has_real_drive:
        return CheckResult("WARN", "A-Wiki-Data",
                           f"no populated drive (fallback {drive_root}) — optional layer")
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


def check_hooks(hooks_dir=None) -> CheckResult:
    """P6-RR06: hook presence is validated against the REGISTRY authority
    (scripts/hooks/registry.py), not a frozen filename list — every
    registered executable must exist and the registry must validate."""
    if not (REPO_ROOT / "scripts" / "hooks_runner.py").is_file():
        return CheckResult("FAIL", "core hooks", "missing: scripts/hooks_runner.py")
    import sys
    hooks_root = Path(hooks_dir) if hooks_dir else REPO_ROOT / "scripts" / "hooks"
    sys.path.insert(0, str(REPO_ROOT / "scripts" / "hooks"))
    import registry as hook_registry
    # registry validation is STRUCTURAL by approved contract; executable
    # presence is this check's own responsibility (P6-RR06)
    errors = hook_registry.validate_registry(skip_executable_check=True)
    if errors:
        return CheckResult("FAIL", "core hooks",
                           "registry invalid: " + "; ".join(errors[:5]))
    missing = [n for n in hook_registry.HOOK_REGISTRY
               if not (hooks_root / f"{n}.py").is_file()]
    if missing:
        return CheckResult("FAIL", "core hooks",
                           "registered executables missing: " + ", ".join(missing[:8]))
    n = len(hook_registry.HOOK_REGISTRY)
    hard = sum(1 for v in hook_registry.HOOK_REGISTRY.values()
               if v["classification"] == "hard")
    return CheckResult("OK", "core hooks",
                       f"{n} registered hook(s) valid via registry authority ({hard} hard)")


def check_guardrail_coverage() -> CheckResult:
    """P6-RR06: coverage is derived from the REGISTRY's hard PreToolUse
    gates, not a frozen name list. A config satisfies a gate either by a
    named per-hook runner invocation or structurally via an event-sweep
    command (the runner applies registry matchers internally)."""
    import json as _json
    import sys
    sys.path.insert(0, str(REPO_ROOT / "scripts" / "hooks"))
    import registry as hook_registry
    hard_gates = {n for n, e in hook_registry.HOOK_REGISTRY.items()
                  if "PreToolUse" in e["events"] and e["classification"] == "hard"}
    missing_by_config: dict[str, list[str]] = {}
    for rel in HOOK_CONFIGS:
        path = REPO_ROOT / rel
        if not path.is_file():
            continue
        try:
            raw = path.read_text(encoding="utf-8")
            cfg = _json.loads(raw)
        except Exception:
            continue
        commands = collect_hook_commands(cfg)
        has_sweep = any("--event" in c and "hooks_runner.py" in c for c in commands)
        if has_sweep:
            continue  # sweep dispatch covers all registry gates by construction
        dashed = {c.replace("-", "_") for c in commands}
        missing = [g for g in sorted(hard_gates) if g not in dashed]
        if missing:
            missing_by_config[rel] = missing
    if missing_by_config:
        parts = [f"{cfg}: {m}" for cfg, m in missing_by_config.items()]
        return CheckResult("FAIL", "guardrail coverage", "; ".join(parts))
    return CheckResult("OK", "guardrail coverage",
                       f"{len(hard_gates)} hard PreToolUse registry gate(s) wired in all configs")


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


def _read_platform_doc(rel: str) -> str | None:
    """Read a platform instruction doc, accepting either a file or a
    Cline-style directory (`.clinerules/` with `rules.md` inside).

    Returns the doc text, or None if no readable file is found. Cline moved
    from a single `.clinerules` file to a `.clinerules/` directory containing
    `rules.md` + `hooks/` subdirs; the preflight must accept both shapes.
    """
    path = REPO_ROOT / rel
    if path.is_file():
        return path.read_text(encoding="utf-8", errors="replace")
    rules_md = path / "rules.md"
    if rules_md.is_file():
        return rules_md.read_text(encoding="utf-8", errors="replace")
    return None


def check_instruction_drift() -> CheckResult:
    missing_files = []
    missing_preflight = []
    missing_brain_gate = []
    for rel in PREFLIGHT_DOCS:
        text = _read_platform_doc(rel)
        if text is None:
            missing_files.append(rel)
            continue
        if "scripts/agent-preflight.py" not in text:
            missing_preflight.append(rel)
        if "brain-improvement-gate" not in text:
            missing_brain_gate.append(rel)
    if missing_files or missing_preflight or missing_brain_gate:
        parts = []
        if missing_files:
            parts.append("missing files: " + ", ".join(missing_files))
        if missing_preflight:
            parts.append("missing preflight line: " + ", ".join(missing_preflight))
        if missing_brain_gate:
            parts.append("missing brain gate line: " + ", ".join(missing_brain_gate))
        return CheckResult("FAIL", "platform instruction drift", "; ".join(parts))
    return CheckResult("OK", "platform instruction drift", "preflight + brain gate documented across platform files")


def run_checks(skip_remote: bool = False) -> list[CheckResult]:
    return [
        check_branch(),
        check_remote(skip_remote=skip_remote),
        check_worktree(),
        check_session_handoff(),
        check_external_data(),
        check_generated_index(),
        check_hooks(),
        check_hook_config_commands(),
        check_guardrail_coverage(),
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
