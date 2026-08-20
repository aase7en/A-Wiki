#!/usr/bin/env python3
"""
Hook Runner — A-Wiki (canonical lifecycle dispatcher, Phase 6)
==============================================================
ONE canonical dispatch contract for every provider (Claude Code, Codex, …):

  provider event → thin provider normalization (scripts/hooks/providers.py)
      → this runner + scripts/hooks/registry.py (the classification authority)
      → normalized PASS / BLOCK / context result

Contract:
  - hooks may only execute through the runner if REGISTERED in
    scripts/hooks/registry.py — filenames are never a security authority;
  - classification, not filename behavior, decides semantics:
      hard  → enforcement: rc 0 passes; rc 2 blocks; timeout / exception /
              unexpected exit code / missing executable BLOCK (fail-closed —
              an unavailable registry or hook can never silently weaken a
              hard gate);
      soft  → observe-only: NEVER blocks, even if the child exits 2;
              timeout/exception stays non-blocking with sanitized diagnostics;
  - only 0 (pass / non-blocking) and 2 (block) ever leave this runner —
    arbitrary child exit codes are normalized, never leaked to providers;
  - contextual stdout is forwarded ONLY for hooks registered with
    allow_context_stdout=True; all other stdout is discarded deterministically;
  - diagnostics are sanitized (secrets → ***, absolute machine paths → <path>);
  - deterministic execution order comes from the registry (order, name),
    never from filesystem enumeration.

Usage:
  python3 scripts/hooks_runner.py <hook_name> [--event EVENT] < input.json
  python3 scripts/hooks_runner.py --event EVENT < input.json   # all hooks for event

  HOOK_SKIP=hook_name            skip one hook (compat)
  HOOK_TIMEOUT=5                 default per-hook timeout seconds
  AWIKI_HOOKS_DIR=<dir>          hooks dir override (tests/emergency)

The runner is police, not a manager: it never pushes, merges, rebases,
resets, or deploys — it only executes registered hook scripts and
normalizes their verdicts.

Back-compat: run_hook() remains the low-level single-file executor used by
legacy unit tests; registration/classification policy is enforced by
execute()/main().
"""

import sys
import json
import os
import re
import subprocess
import glob

# Windows consoles default to cp874/cp1252 — force UTF-8 for hook output this
# runner re-emits itself (e.g. a blocked hook's Thai stderr message,
# forwarded verbatim below). Same strong pattern as
# scripts/hooks/check_compaction_suggest.py:114-120.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

HOOKS_DIR = os.environ.get("AWIKI_HOOKS_DIR",
                           os.path.join(os.path.dirname(__file__), "hooks"))
_STARTUP_CONFIG_ERROR: str | None = None
try:
    HOOK_TIMEOUT = int(os.environ.get("HOOK_TIMEOUT", "5"))
    if HOOK_TIMEOUT <= 0:
        raise ValueError("timeout must be positive")
except (TypeError, ValueError):
    HOOK_TIMEOUT = 5
    _STARTUP_CONFIG_ERROR = "hook runner configuration invalid (fail closed)"

# ── Live Dashboard event logger ───────────────────────────────────────────────
_REPO_ROOT = os.path.dirname(os.path.abspath(__file__))  # scripts/
_LIVE_LOG = os.environ.get(
    "AWIKI_LIVE_LOG_PATH",
    os.path.join(_REPO_ROOT, "..", ".tmp", "live-events.jsonl"),
)

# Secrets are redacted with the SAME patterns as the memory ledger (one
# redaction contract); absolute machine paths collapse to <path>.
sys.path.insert(0, os.path.join(_REPO_ROOT, "lib"))
try:
    from memory_ledger import _redact as _redact_secrets
except Exception:  # pragma: no cover — sanitizer failure must suppress detail
    def _redact_secrets(_text: str) -> str:
        return "diagnostic suppressed"
_ABS_PATH_RE = re.compile(
    r"(?<![A-Za-z])[A-Za-z]:[\\/][^ \t\"']*|/(?:home|Users|root|private)/[^ \t\"']*")


def _sanitize(text: str) -> str:
    """Redact diagnostics; suppress all detail if the sanitizer is unavailable."""
    if not text:
        return text
    try:
        return _ABS_PATH_RE.sub("<path>", _redact_secrets(text))
    except Exception:
        return "diagnostic suppressed"


def _log_event(event_type: str, **kwargs) -> None:
    """Write one JSON line to the live dashboard log (best-effort, never raises)."""
    try:
        os.makedirs(os.path.dirname(_LIVE_LOG), exist_ok=True)
        entry = {"ts": round(__import__("time").time(), 3), "type": event_type,
                 **{k: v for k, v in kwargs.items() if v is not None}}
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

# ── registry (the classification authority — fail CLOSED when broken) ────────
_REGISTRY_LOAD_ERROR: str | None = None
try:
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "hooks"))
    import registry as hook_registry  # noqa: E402
    import providers as hook_providers  # noqa: E402
    REGISTRY = hook_registry.load_registry(hooks_dir=HOOKS_DIR)
except Exception as _e:  # registry/provider authority unavailable → fail closed
    hook_registry = None
    hook_providers = None
    REGISTRY = {}
    _REGISTRY_LOAD_ERROR = "hook registry unavailable (fail closed)"


def get_hooks():
    """Registered hook scripts in deterministic (order, name) order —
    registry-driven, NOT filesystem enumeration (Phase 6)."""
    if _REGISTRY_LOAD_ERROR or not REGISTRY:
        return []
    return [f"{name}.py" for name in
            sorted(REGISTRY, key=lambda n: (REGISTRY[n]["order"], n))
            if f"{name}.py" not in HOOK_SKIP]


def run_event_hooks_order(event: str):
    """Deterministic hook-name order for one event (test surface)."""
    if _REGISTRY_LOAD_ERROR or hook_registry is None:
        return []
    return [n for n in hook_registry.hooks_for_event(event, REGISTRY)
            if f"{n}.py" not in HOOK_SKIP]


def run_hook(hook_name, input_data):
    """LOW-LEVEL single-file executor (legacy unit-test surface).

    Policy (registration/classification) lives in execute()/main() — this
    function only runs a file that exists and reports (passed, message).
    """
    hook_path = os.path.join(HOOKS_DIR, hook_name)
    if not os.path.isfile(hook_path):
        return True, ""

    try:
        proc = subprocess.run(
            [sys.executable, hook_path],
            input=json.dumps(input_data),
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=HOOK_TIMEOUT,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        if proc.returncode == 2:
            return False, proc.stderr.strip()
        if proc.returncode != 0:
            sys.stderr.write(
                f"⚠️ Hook {hook_name} exited with code {proc.returncode}: "
                f"{_sanitize(proc.stderr.strip())}\n")
        return True, ""
    except subprocess.TimeoutExpired:
        sys.stderr.write(f"⚠️ Hook {hook_name} timed out after {HOOK_TIMEOUT}s\n")
        return True, ""
    except Exception as e:
        sys.stderr.write(f"⚠️ Hook {hook_name} error: {e}\n")
        return True, ""


def execute(name: str, input_data: dict, event: str | None = None) -> dict:
    """Canonical classified execution of ONE registered hook.

    Returns {"decision": "pass"|"block", "reason": str,
             "context_stdout": str, "hook": name}.
    Hard hooks fail CLOSED on timeout/exception/odd exit/missing executable;
    soft hooks can never block.
    """
    name = name.replace("-", "_")
    if _STARTUP_CONFIG_ERROR:
        return {"decision": "block",
                "reason": "hook runner configuration invalid (fail closed)",
                "context_stdout": "", "hook": name}
    if _REGISTRY_LOAD_ERROR:
        return {"decision": "block",
                "reason": "hook registry unavailable (fail closed)",
                "context_stdout": "", "hook": name}
    entry = REGISTRY.get(name)
    if entry is None:
        return {"decision": "block",
                "reason": f"hook not registered: {name} — register it in "
                          f"scripts/hooks/registry.py (refusing fail-open)",
                "context_stdout": "", "hook": name}
    if event is not None and event not in entry["events"]:
        return {"decision": "block",
                "reason": f"hook {name} is not registered for event {event!r} "
                          f"(events: {entry['events']})",
                "context_stdout": "", "hook": name}

    classification = entry["classification"]
    timeout = entry.get("timeout_s") or HOOK_TIMEOUT
    hook_path = os.path.join(HOOKS_DIR, f"{name}.py")

    def _pass(reason: str = "", stdout_text: str = "") -> dict:
        return {"decision": "pass", "reason": reason,
                "context_stdout": stdout_text, "hook": name}

    def _block(reason: str) -> dict:
        return {"decision": "block", "reason": reason,
                "context_stdout": "", "hook": name}

    if not os.path.isfile(hook_path):
        # Missing executable: hard → block; soft → non-blocking diagnostic.
        msg = f"hook executable missing: {name}"
        if classification == "hard":
            return _block(msg + " (fail closed)")
        sys.stderr.write(_sanitize(f"⚠️ {msg} (soft — non-blocking)\n"))
        return _pass()

    try:
        proc = subprocess.run(
            [sys.executable, hook_path],
            input=json.dumps(input_data),
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=timeout,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
    except subprocess.TimeoutExpired:
        if classification == "hard":
            return _block(f"hard hook {name} timed out after {timeout}s "
                          f"(fail closed)")
        sys.stderr.write(_sanitize(f"⚠️ soft hook {name} timed out "
                                   f"after {timeout}s (non-blocking)\n"))
        return _pass()
    except Exception as e:
        if classification == "hard":
            return _block(f"hard hook {name} error (fail closed): {e}")
        sys.stderr.write(_sanitize(f"⚠️ soft hook {name} error "
                                   f"(non-blocking): {e}\n"))
        return _pass()

    stderr_msg = _sanitize(proc.stderr.strip())
    stdout_text = proc.stdout or ""
    if entry.get("allow_context_stdout"):
        stdout_text = _sanitize(stdout_text)
    else:
        stdout_text = ""  # non-context hooks: stdout is discarded deterministically

    if proc.returncode == 2:
        if classification == "hard":
            _log_event("hook_check", hook=name,
                       tool=(input_data.get("tool_name") or ""), result="block")
            return _block(stderr_msg or f"hard hook {name} blocked")
        # soft hook exiting 2 → normalized to non-blocking
        sys.stderr.write(_sanitize(
            f"ℹ️ soft hook {name} requested block — normalized to "
            f"non-blocking: {stderr_msg}\n"))
        return _pass()
    if proc.returncode != 0:
        if classification == "hard":
            return _block(f"hard hook {name} exited with code "
                          f"{proc.returncode} (normalized to block): {stderr_msg}")
        sys.stderr.write(_sanitize(
            f"⚠️ soft hook {name} exited with code {proc.returncode} "
            f"(non-blocking): {stderr_msg}\n"))
        return _pass()

    _log_event("hook_check", hook=name,
               tool=(input_data.get("tool_name") or ""), result="pass")
    if stderr_msg:  # advisory stderr from a passing hook (e.g. self_audit)
        sys.stderr.write(stderr_msg + "\n")
    return _pass(stdout_text=stdout_text)


def _emit_hook_event(hook_name: str, input_data: dict, result: str) -> None:
    """Emit a hook_check event to the live dashboard (legacy surface)."""
    base = hook_name.replace(".py", "")
    tool = input_data.get("tool_name") or input_data.get("tool", "")
    kwargs: dict = {"hook": base, "tool": tool or None, "result": result}
    if "cost_tier" in base and result == "pass":
        try:
            today = __import__("time").strftime("%Y-%m-%d")
            files = glob.glob(os.path.join(_REPO_ROOT, "..", ".tmp",
                                           f"cost-tier-{today}.txt"))
            if files:
                tier = open(files[0]).read().strip().split("|")[0].strip()
                if tier:
                    kwargs["tier"] = tier
        except Exception:
            pass
    _log_event("hook_check", **kwargs)


def main():
    args = [a for a in sys.argv[1:]]
    event = None
    provider = None
    if "--event" in args:
        i = args.index("--event")
        if i + 1 >= len(args):
            sys.stderr.write("usage: --event requires a lifecycle event name\n")
            sys.exit(2)
        event = args[i + 1]
        del args[i:i + 2]
    if "--provider" in args:
        i = args.index("--provider")
        if i + 1 >= len(args):
            sys.stderr.write("usage: --provider requires a provider name\n")
            sys.exit(2)
        provider = args[i + 1]
        del args[i:i + 2]
    specific_hook = args[0] if args else None

    if _STARTUP_CONFIG_ERROR:
        sys.stderr.write("hook runner configuration invalid (fail closed)\n")
        sys.exit(2)
    if _REGISTRY_LOAD_ERROR:
        sys.stderr.write("hook registry unavailable (fail closed)\n")
        sys.exit(2)

    malformed_payload = object()
    raw_input = sys.stdin.read()
    if provider is not None:
        if event is None:
            sys.stderr.write("provider dispatch requires --event\n")
            sys.exit(2)
        provider_event = event
        try:
            event = hook_providers.normalize_event(provider, provider_event)
            normalized = hook_providers.normalize_payload(
                provider, raw_input, event=provider_event
            )
        except hook_providers.ProviderError:
            sys.stderr.write("provider normalization failed\n")
            sys.exit(2)
        input_data = (
            malformed_payload
            if normalized is hook_providers.MALFORMED_PAYLOAD
            else normalized
        )
    else:
        try:
            parsed_input = json.loads(raw_input)
            input_data = parsed_input if isinstance(parsed_input, dict) else malformed_payload
        except Exception:
            input_data = malformed_payload

    if event is not None and event not in hook_registry.KNOWN_EVENTS:
        sys.stderr.write(f"unknown lifecycle event: {event!r} "
                         f"(known: {list(hook_registry.KNOWN_EVENTS)})\n")
        sys.exit(2)

    if specific_hook:
        name = specific_hook.replace("-", "_")
        if not name.endswith(".py"):
            name = name + ".py"
        name = name[:-3]

        if input_data is malformed_payload:
            entry = REGISTRY.get(name)
            sys.stderr.write("malformed hook payload suppressed\n")
            if entry is None:
                sys.exit(2)
            if event is not None and event not in entry["events"]:
                sys.exit(2)
            sys.exit(2 if entry["classification"] == "hard" else 0)

        if f"{name}.py" in HOOK_SKIP:
            sys.exit(0)
        res = execute(name, input_data, event=event)
        if res["decision"] == "block":
            sys.stderr.write(_sanitize(res["reason"]) + "\n")
            sys.exit(2)
        if res["context_stdout"]:
            sys.stdout.write(res["context_stdout"])
        sys.exit(0)

    # Run ALL registered hooks for one event (requires --event: running
    # Stop hooks on a PreToolUse payload is meaningless and was never
    # wired anywhere).
    if event is None:
        sys.stderr.write(
            "run-all requires --event <lifecycle event> (registry-driven; "
            "running every hook on any payload is not a valid lifecycle)\n")
        sys.exit(2)

    if input_data is malformed_payload:
        names = run_event_hooks_order(event)
        has_hard_gate = any(
            REGISTRY[name]["classification"] == "hard"
            for name in names
            if name in REGISTRY
        )
        sys.stderr.write("malformed hook payload suppressed\n")
        sys.exit(2 if has_hard_gate else 0)

    any_block = False
    for name in run_event_hooks_order(event):
        res = execute(name, input_data, event=event)
        if res["decision"] == "block":
            any_block = True
            sys.stderr.write(_sanitize(res["reason"]) + "\n")
        elif res["context_stdout"]:
            sys.stdout.write(res["context_stdout"])
    sys.exit(2 if any_block else 0)


if __name__ == "__main__":
    main()
