#!/usr/bin/env python3
"""
Hook Runner — A-Wiki
====================
Orchestrates all Claude Code hooks from scripts/hooks/.

Usage:
  python3 scripts/hooks_runner.py < input.json              # Run ALL hooks
  python3 scripts/hooks_runner.py check_secret_leak < input.json  # Run specific hook

Each hook is a script in scripts/hooks/ that receives the full input JSON
on stdin and exits 0 (pass) or 2 (block). Non-zero exit codes are reported
but do NOT block unless exit code is 2.

Hook execution order is alphabetical by filename when running ALL.

Configuration:
  - HOOK_SKIP: comma-separated list of hook filenames to skip
  - HOOK_TIMEOUT: seconds per hook (default 5)

Source: Inspired by InW-Wiki hook architecture
"""

import sys
import json
import os
import subprocess
import time
import glob

HOOKS_DIR = os.path.join(os.path.dirname(__file__), "hooks")
HOOK_TIMEOUT = int(os.environ.get("HOOK_TIMEOUT", "5"))

# ── Live Dashboard event logger ───────────────────────────────────────────────
_REPO_ROOT = os.path.dirname(os.path.abspath(__file__))  # scripts/
_LIVE_LOG = os.path.join(_REPO_ROOT, "..", ".tmp", "live-events.jsonl")


def _log_event(event_type: str, **kwargs) -> None:
    """Write one JSON line to the live dashboard log (best-effort, never raises)."""
    try:
        os.makedirs(os.path.dirname(_LIVE_LOG), exist_ok=True)
        entry = {"ts": round(time.time(), 3), "type": event_type, **{k: v for k, v in kwargs.items() if v is not None}}
        with open(_LIVE_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass
def _norm_skip(name: str) -> str:
    """Normalize a skip entry: accept dashes/underscores, with/without .py."""
    name = name.strip().replace("-", "_")
    if name and not name.endswith(".py"):
        name = name + ".py"
    return name


HOOK_SKIP = set(
    _norm_skip(h)
    for h in os.environ.get("HOOK_SKIP", "").split(",")
    if h.strip()
)


def get_hooks():
    """Return sorted list of hook scripts."""
    if not os.path.isdir(HOOKS_DIR):
        return []
    hooks = sorted(
        f for f in os.listdir(HOOKS_DIR)
        if f.endswith(".py") and f != "__init__.py" and f not in HOOK_SKIP
    )
    return hooks


def run_hook(hook_name, input_data):
    """Run a single hook and return (passed: bool, message: str)."""
    hook_path = os.path.join(HOOKS_DIR, hook_name)
    if not os.path.isfile(hook_path):
        return True, ""

    try:
        proc = subprocess.run(
            [sys.executable, hook_path],
            input=json.dumps(input_data),
            capture_output=True,
            text=True, encoding="utf-8", errors="replace",
            timeout=HOOK_TIMEOUT,
        )
        passed = proc.returncode != 2
        if proc.returncode == 2:
            _emit_hook_event(hook_name, input_data, "block")
            return False, proc.stderr.strip()
        if proc.returncode != 0:
            sys.stderr.write(
                f"⚠️ Hook {hook_name} exited with code {proc.returncode}: {proc.stderr.strip()}\n"
            )
        _emit_hook_event(hook_name, input_data, "pass")
        return True, ""
    except subprocess.TimeoutExpired:
        sys.stderr.write(f"⚠️ Hook {hook_name} timed out after {HOOK_TIMEOUT}s\n")
        return True, ""
    except Exception as e:
        sys.stderr.write(f"⚠️ Hook {hook_name} error: {e}\n")
        return True, ""


def _emit_hook_event(hook_name: str, input_data: dict, result: str) -> None:
    """Emit a hook_check event to the live dashboard."""
    base = hook_name.replace(".py", "")
    tool = input_data.get("tool_name") or input_data.get("tool", "")
    kwargs: dict = {"hook": base, "tool": tool or None, "result": result}
    # For cost-tier pass: include declared tier
    if "cost_tier" in base and result == "pass":
        try:
            today = time.strftime("%Y-%m-%d")
            files = glob.glob(os.path.join(_REPO_ROOT, "..", ".tmp", f"cost-tier-{today}.txt"))
            if files:
                tier = open(files[0]).read().strip().split("|")[0].strip()
                if tier:
                    kwargs["tier"] = tier
        except Exception:
            pass
    _log_event("hook_check", **kwargs)


def main():
    # Support: hooks_runner.py <hook_name> (w/ or w/o .py suffix, dashes or underscores)
    # If no hook_name given, run ALL hooks
    specific_hook = None
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        specific_hook = sys.argv[1]
        if not specific_hook.endswith(".py"):
            specific_hook = specific_hook + ".py"
        # Normalize: settings.json may invoke with dashes (check-foo-bar)
        # while filenames use underscores (check_foo_bar.py). Try the
        # underscored form when the dashed file doesn't exist.
        if not os.path.isfile(os.path.join(HOOKS_DIR, specific_hook)):
            alt = specific_hook.replace("-", "_")
            if os.path.isfile(os.path.join(HOOKS_DIR, alt)):
                specific_hook = alt

    try:
        input_data = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    if specific_hook:
        passed, message = run_hook(specific_hook, input_data)
        if not passed:
            sys.stderr.write(message + "\n")
            sys.exit(2)
        sys.exit(0)

    # Run ALL hooks
    hooks = get_hooks()
    if not hooks:
        sys.exit(0)

    any_failed = False
    for hook_name in hooks:
        passed, message = run_hook(hook_name, input_data)
        if not passed:
            any_failed = True
            sys.stderr.write(message + "\n")

    if any_failed:
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()