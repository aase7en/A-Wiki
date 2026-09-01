"""setup-zcode-hooks.py — install the A-Wiki hook stack into ZCode (per machine).

Usage:  python scripts/setup_zcode_hooks.py [--dry-run] [--zcode-home DIR]

Why this exists (verified 2026-09-01, zcode.z.ai/en/docs/hooks): ZCode runs
user-level (~/.zcode/cli/config.json, hooks.enabled: true) and plugin hooks,
but IGNORES workspace .zcode/config.json hooks — so A-Wiki's repo-level hook
wiring never fires on ZCode. This installer is the supported path:

  1. copies scripts/hooks/zcode_hook_loader.py → ~/.zcode/hooks/awiki_hook_loader.py
  2. merges an idempotent hooks block into ~/.zcode/cli/config.json
     (backs up the existing config first; unrelated keys/hooks untouched)

Every entry is a `process` hook (argument vector, no shell) → Windows-safe.
The loader no-ops when the target script is absent, so non-A-Wiki projects
on the same machine stay completely unaffected. Hooks take effect in NEW
ZCode sessions (config is read at session start).

Wire-up (canonical A-Wiki stack, mirrors the repo's .zcode/config.json):
  SessionStart  → session_start.py + hooks_runner + a_loop_ssot (SSoT inject)
  UserPromptSubmit → hooks_runner (recall_on_prompt / check_a_route / …)
  PreToolUse    → hooks_runner (claim gate Iron Law #11 + hard gates)
  PostToolUse   → hooks_runner
  Stop          → hooks_runner + a_loop_continue (Loop Engineer continue ≤3)
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
LOADER_SRC = SCRIPTS_DIR / "hooks" / "zcode_hook_loader.py"
LOADER_DST_NAME = "awiki_hook_loader.py"
DEFAULT_TIMEOUT_MS = 30000

# (event, matcher, repo-relative target, extra args)
HOOK_WIRING = [
    ("SessionStart", "startup|resume|clear|compact",
     "scripts/hooks/session_start.py", []),
    ("SessionStart", "startup|resume|clear|compact",
     "scripts/hooks_runner.py", ["--provider", "zcode", "--event", "SessionStart"]),
    ("SessionStart", "startup|resume|clear|compact",
     "scripts/hooks/a_loop_ssot.py", []),
    ("UserPromptSubmit", "",
     "scripts/hooks_runner.py", ["--provider", "zcode", "--event", "UserPromptSubmit"]),
    ("PreToolUse", "Edit|Write|MultiEdit",
     "scripts/hooks_runner.py", ["--provider", "zcode", "--event", "PreToolUse"]),
    ("PreToolUse", "Bash",
     "scripts/hooks_runner.py", ["--provider", "zcode", "--event", "PreToolUse"]),
    ("PreToolUse", "Agent",
     "scripts/hooks_runner.py", ["--provider", "zcode", "--event", "PreToolUse"]),
    ("PostToolUse", "Edit|Write|MultiEdit",
     "scripts/hooks_runner.py", ["--provider", "zcode", "--event", "PostToolUse"]),
    ("PostToolUse", "Bash",
     "scripts/hooks_runner.py", ["--provider", "zcode", "--event", "PostToolUse"]),
    ("Stop", "",
     "scripts/hooks_runner.py", ["--provider", "zcode", "--event", "Stop"]),
    ("Stop", "",
     "scripts/hooks/a_loop_continue.py", []),
]


def _hook_entry(python_exe: str, loader_path: str, target: str, extra: list) -> dict:
    return {
        "type": "process",
        "command": python_exe,
        "args": [loader_path, f"${{ZCODE_PROJECT_DIR}}/{target}", *extra],
        "timeoutMs": DEFAULT_TIMEOUT_MS,
        "statusMessage": f"A-Wiki: {Path(target).name}",
    }


def build_hooks_block(python_exe: str, loader_path: str) -> dict:
    """Build the ZCode-schema hooks block for the full A-Wiki stack."""
    events: dict[str, list] = {}
    for event, matcher, target, extra in HOOK_WIRING:
        entry = _hook_entry(python_exe, loader_path, target, extra)
        for group in events.setdefault(event, []):
            if group["matcher"] == matcher:
                group["hooks"].append(entry)
                break
        else:
            events[event].append({"matcher": matcher, "hooks": [entry]})
    return {"enabled": True, "timeoutMs": DEFAULT_TIMEOUT_MS, "events": events}


def _loader_path_of(block: dict) -> str | None:
    for groups in block.get("events", {}).values():
        for group in groups:
            for hook in group.get("hooks", []):
                args = hook.get("args") or []
                if args:
                    return args[0]
    return None


def _is_ours(hook: dict, loader_path: str) -> bool:
    args = hook.get("args") or []
    return bool(args) and args[0] == loader_path


def merge_hooks_config(config: dict, block: dict) -> dict:
    """Idempotent upsert: replace our loader-referencing entries, keep the rest."""
    import copy
    merged = copy.deepcopy(config)
    loader_path = _loader_path_of(block)
    hooks = merged.setdefault("hooks", {})
    hooks["enabled"] = True
    hooks.setdefault("timeoutMs", block.get("timeoutMs", DEFAULT_TIMEOUT_MS))
    events = hooks.setdefault("events", {})
    for event, new_groups in block.get("events", {}).items():
        existing = events.get(event, [])
        if loader_path:
            stripped = []
            for group in existing:
                kept = [h for h in group.get("hooks", [])
                        if not _is_ours(h, loader_path)]
                if kept:
                    stripped.append({**group, "hooks": kept})
                # groups left empty were entirely ours → drop
            existing = stripped
        existing.extend(copy.deepcopy(new_groups))
        events[event] = existing
    return merged


def install(repo_root: Path, zcode_home: Path, python_exe: str | None = None,
            dry_run: bool = False) -> dict:
    """Install loader + merge config. Returns a report dict."""
    repo_root = Path(repo_root)
    zcode_home = Path(zcode_home)
    python_exe = python_exe or sys.executable
    loader_dst = zcode_home / "hooks" / LOADER_DST_NAME
    cfg_path = zcode_home / "cli" / "config.json"
    block = build_hooks_block(python_exe, str(loader_dst))
    report = {"dry_run": dry_run, "loader_installed": False,
              "config_updated": False, "loader_path": str(loader_dst),
              "config_path": str(cfg_path), "hooks_block": block}
    if dry_run:
        return report
    if not LOADER_SRC.is_file():
        report["error"] = f"loader source missing: {LOADER_SRC}"
        return report
    (zcode_home / "hooks").mkdir(parents=True, exist_ok=True)
    shutil.copyfile(LOADER_SRC, loader_dst)
    report["loader_installed"] = True
    (zcode_home / "cli").mkdir(parents=True, exist_ok=True)
    if cfg_path.exists():
        config = json.loads(cfg_path.read_text(encoding="utf-8"))
        backup = cfg_path.with_name(
            f"config.json.bak-{time.strftime('%Y%m%d-%H%M%S')}")
        shutil.copyfile(cfg_path, backup)
        report["backup"] = str(backup)
    else:
        config = {}
    merged = merge_hooks_config(config, block)
    tmp = cfg_path.with_name(cfg_path.name + ".tmp")
    tmp.write_text(json.dumps(merged, indent=2, ensure_ascii=False),
                   encoding="utf-8")
    tmp.replace(cfg_path)
    report["config_updated"] = True
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dry-run", action="store_true",
                        help="show the planned block without writing anything")
    parser.add_argument("--zcode-home", default=str(Path.home() / ".zcode"),
                        help="ZCode home (default: ~/.zcode)")
    parser.add_argument("--python-exe", default=sys.executable,
                        help="python executable for hook entries (default: this python)")
    args = parser.parse_args(argv)
    repo_root = Path(__file__).resolve().parent.parent
    report = install(repo_root=repo_root, zcode_home=Path(args.zcode_home),
                     python_exe=args.python_exe, dry_run=args.dry_run)
    status = "DRY-RUN" if args.dry_run else (
        "OK" if report.get("config_updated") else "FAILED")
    print(f"[setup-zcode-hooks] {status}")
    print(f"  loader : {report['loader_path']}"
          + (" (installed)" if report["loader_installed"] else ""))
    print(f"  config : {report['config_path']}"
          + (f" (backup: {report['backup']})" if report.get("backup") else ""))
    if report.get("error"):
        print(f"  ERROR  : {report['error']}")
        return 1
    n = sum(len(g["hooks"]) for groups in report["hooks_block"]["events"].values()
            for g in groups)
    print(f"  entries: {n} process hooks across "
          f"{len(report['hooks_block']['events'])} events")
    if not args.dry_run:
        print("Next: เปิด ZCode session ใหม่ → hooks ทำงาน (config อ่านตอน session start)")
        print("Verify: session ใหม่ใน repo ที่มี goal active ต้องเห็น '[a-loop SSoT]' "
              "+ Stop hook ของ /A-Loop จะสั่งทำต่อ ≤3 รอบ")
    return 0 if (args.dry_run or report.get("config_updated")) else 1


if __name__ == "__main__":
    sys.exit(main())
