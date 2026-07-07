#!/usr/bin/env python3
"""
telegram-command-router.py — map Telegram slash commands to A-Wiki scripts.
==========================================================================

Closes the C4 gap (docs/architecture/hermes-cross-agent-handoff.md §"C4 RESULTS"):
the live Pi5 Telegram bot replies ``Unknown command`` to ``/spec /plan /build
/review /ship /search /wiki``. The A-Wiki lifecycle skills exist on-device
(symlinks + manifest, reconciled in Chunk C3') but have NO Telegram command
trigger — there is no integration layer mapping ``/<cmd>`` → script invocation.

This router is that layer. It reads a route map
(``telegram-commands.json``, sibling file) and dispatches each ``/<cmd> <args>``
to the matching backing script:

  - ``/wiki <q>``, ``/search <q>``         → ``scripts/wiki/search-wiki.py``
  - ``/review``, ``/spec``, ``/plan``,
    ``/build``, ``/ship``  ``<task>``      → ``scripts/hermes/persona-orchestrator.py --task``

The command surface itself is realized by Skills-as-Commands: each of the seven
``skills/awiki/<cmd>/SKILL.md`` dirs is auto-exposed as ``/<cmd>`` on the
Telegram gateway (Hermes docs: "every installed skill is available as a slash
command on any messaging platform"). The skill body tells the LLM to extract
the query/task and call THIS router. This is the reliable path today; the
zero-LLM ``quick_commands type:exec`` optimization is blocked by upstream bug
#44718 (the ``{args}`` placeholder) and tracked as a future swap-in.

Design principles (mirror scripts/hermes/persona-orchestrator.py):
  - Map, do not execute by default — ``--apply`` is required to spawn anything;
    the default is ``--dry-run`` which prints the route as JSON (CI-safe).
  - Pure router, injectable executor — ``build_route``/``resolve_command``/
    ``load_command_map`` are pure (no subprocess, no I/O side effects);
    ``execute`` takes an injectable ``runner`` callable so tests stub it.
  - Fail soft on unknown command — return a formatted error string + exit 1;
    never raise. A misrouted message must not crash the gateway.

Usage
-----
::

    # Default: dry-run, print the route as JSON (CI-safe, no script call).
    python scripts/hermes/telegram-command-router.py --command wiki --message "/wiki mqtt broker"

    # Route from a full Telegram message (router parses the slash itself).
    python scripts/hermes/telegram-command-router.py --message "/review review the auth refactor"

    # Run for real (spawns the backing script).
    python scripts/hermes/telegram-command-router.py --command wiki --message "/wiki mqtt broker" --apply

    # Override the route map.
    python scripts/hermes/telegram-command-router.py --config /path/to/map.json --message "/wiki x"

Exit codes
----------
- 0 = success (route printed in dry-run, or script executed and returned)
- 1 = misconfiguration (unknown command, missing message/command, missing args)

See: docs/architecture/hermes-cross-agent-handoff.md §"Follow-up chunk proposal (chunk hermes-e)"
     docs/runbooks/hermes-raspberry-pi5.md §"Slash Commands"
     skills/awiki/{wiki,search,review,spec,plan,build,ship}/SKILL.md
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

# Sibling route map (mirror persona-orchestrator's lifecycle-config.json sibling
# convention). Edit scripts/hermes/telegram-commands.json to add a command.
DEFAULT_COMMAND_MAP_PATH = Path(__file__).parent / "telegram-commands.json"

# Backing scripts — kept as strings, never resolved via shutil.which in pure
# functions (mirrors persona-orchestrator's HERMES_CMD discipline).
SEARCH_SCRIPT = "scripts/wiki/search-wiki.py"
ORCHESTRATOR_SCRIPT = "scripts/hermes/persona-orchestrator.py"

# Telegram message conventions.
COMMAND_PREFIX = "/"

# Default result cap for /wiki /search (FTS5 --limit). 5 keeps the Telegram
# reply short enough to fit one message (~4096 char cap) while surfacing enough
# hits to be useful.
DEFAULT_SEARCH_LIMIT = 5

# Exit codes (persona-orchestrator convention: only 0/1, never 2 — 2 is
# reserved for hook blocks per tests/test_check_skill_registry.py).
SUCCESS_EXIT = 0
UNKNOWN_COMMAND_EXIT = 1


def resolve_command(text: str) -> tuple[str, str]:
    """Split a Telegram message into ``(command, args)``.

    A command is the first whitespace-delimited token that starts with ``/``.
    Everything after it (stripped) is the args. A plain message without a
    leading slash returns ``("", text)`` so callers can decide to hand it to
    the LLM instead of routing.

    Pure function: no I/O, no subprocess.
    """
    stripped = text.strip()
    if not stripped or not stripped.startswith(COMMAND_PREFIX):
        return ("", text.strip())
    # Drop the leading "/" and split on first whitespace.
    body = stripped[len(COMMAND_PREFIX):]
    parts = body.split(None, 1)
    command = parts[0]
    args = parts[1].strip() if len(parts) > 1 else ""
    return (command, args)


def load_command_map(config_path: Path | str) -> dict[str, dict[str, Any]]:
    """Read the ``/<cmd> → {script, kind, phase}`` route map from JSON.

    Returns an empty dict (not an error) when the file is missing or
    unreadable — callers decide whether an empty map is fatal (CLI does:
    exit 1 with a diagnostic). Mirrors ``persona-orchestrator.load_personas``.
    """
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}
    # Drop the _meta key (if present) so only real command entries remain.
    return {k: v for k, v in data.items() if not k.startswith("_")}


def build_route(
    command: str,
    args: str,
    limit: int = DEFAULT_SEARCH_LIMIT,
    command_map: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Construct a route dict for ``command`` WITHOUT running anything.

    The route carries everything ``execute`` and the dry-run printer need:
    ``command``, ``kind`` (``search`` | ``orchestrate`` | ``unknown``),
    ``phase`` (lifecycle phase or ``None``), ``target_script``, ``argv``
    (the full subprocess argv), and ``task_or_query`` (the user's args).

    Raises ``KeyError`` for an unknown command — callers (``main``) catch and
    surface exit 1. Pure function: no subprocess, no I/O (the command_map is
    passed in, not loaded here).
    """
    if command_map is None:
        command_map = load_command_map(DEFAULT_COMMAND_MAP_PATH)

    entry = command_map.get(command)
    if entry is None:
        raise KeyError(f"unknown command: /{command}")

    kind = entry.get("kind", "unknown")
    script = entry["script"]
    phase = entry.get("phase") if kind == "orchestrate" else None

    if kind == "search":
        # python3 scripts/wiki/search-wiki.py "<query>" --json --limit N
        argv = [
            sys.executable, script,
            args,
            "--json",
            "--limit", str(limit),
        ]
    elif kind == "orchestrate":
        # python3 scripts/hermes/persona-orchestrator.py --task "<task>"
        # The persona orchestrator is sequential; phase is advisory metadata
        # (which skill called it) — it does not change the orchestrator argv.
        # The skill body uses --personas to select the fan-out set per phase.
        argv = [
            sys.executable, script,
            "--task", args,
        ]
    else:
        # Unknown kind in the map — fail soft with an empty argv; execute()
        # turns this into a formatted error string.
        argv = []

    return {
        "command": command,
        "kind": kind,
        "phase": phase,
        "target_script": script,
        "argv": argv,
        "task_or_query": args,
        "limit": limit if kind == "search" else None,
    }


def execute(
    route: dict[str, Any],
    runner: Callable[[list[str]], str] | None = None,
) -> str:
    """Run the route's backing script via ``runner`` and return its stdout.

    ``runner`` is a callable ``(argv) -> stdout_str``.  The default runner
    shells out via ``subprocess.run``; tests inject a stub that returns canned
    output without spawning anything.  Mirrors ``persona-orchestrator.run``.

    Fail-soft contract: a route with an empty ``argv`` (unknown command or
    unknown kind) returns a formatted ``[error: ...]`` string rather than
    raising.  A nonzero subprocess exit likewise surfaces as ``[error: ...]``
    so a misbehaving backing script never crashes the gateway.
    """
    if runner is None:
        runner = _default_runner

    argv = route.get("argv") or []
    if not argv:
        return f"[error: empty route for command /{route.get('command', '?')}]"

    return runner(argv)


def _default_runner(argv: list[str]) -> str:
    """Real runner: shell out to the backing script and capture stdout.

    Mirror of ``persona-orchestrator._default_runner``: ``check=False`` so a
    nonzero exit returns a formatted error string, never raises.
    """
    result = subprocess.run(argv, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return (
            f"[error: {argv[0] if argv else 'script'} exited {result.returncode}] "
            f"{result.stderr.strip()}"
        )
    return result.stdout.strip()


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__.splitlines()[1] if __doc__ else "Telegram command router.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument(
        "--message",
        help="Full Telegram message (e.g. '/wiki mqtt broker'). The router "
             "parses the slash command from it. Use this OR --command.",
    )
    ap.add_argument(
        "--command",
        help="Explicit command name (without the slash), e.g. 'wiki'. Use this "
             "OR --message. When given, --message supplies only the args.",
    )
    ap.add_argument(
        "--config",
        default=str(DEFAULT_COMMAND_MAP_PATH),
        help=f"Path to telegram-commands.json (default: {DEFAULT_COMMAND_MAP_PATH}).",
    )
    ap.add_argument(
        "--limit", type=int, default=DEFAULT_SEARCH_LIMIT,
        help=f"Result cap for /wiki /search (default: {DEFAULT_SEARCH_LIMIT}).",
    )
    ap.add_argument(
        "--apply", action="store_true",
        help="Run the backing script for real (default: dry-run, print route as JSON).",
    )
    ap.add_argument(
        "--json", action="store_true",
        help="In --apply mode, emit the route alongside the script output as JSON.",
    )
    a = ap.parse_args()

    if not a.message and not a.command:
        print(
            "🚨 Need --message or --command. Example: --message '/wiki mqtt broker'",
            file=sys.stderr,
        )
        return UNKNOWN_COMMAND_EXIT

    # Resolve command + args from the inputs.
    if a.command:
        command = a.command.lstrip(COMMAND_PREFIX)
        # If --message is also given alongside --command, treat it as args.
        args = a.message.strip() if a.message else ""
    else:
        command, args = resolve_command(a.message)
        if not command:
            print(
                f"🚨 Message has no slash command: {a.message!r}",
                file=sys.stderr,
            )
            return UNKNOWN_COMMAND_EXIT

    command_map = load_command_map(a.config)
    if not command_map:
        print(
            f"🚨 Command map empty or unreadable: {a.config}",
            file=sys.stderr,
        )
        return UNKNOWN_COMMAND_EXIT

    try:
        route = build_route(command, args, limit=a.limit, command_map=command_map)
    except KeyError:
        known = ", ".join(sorted(command_map.keys()))
        print(
            f"🚨 Unknown command /{command}. Known: {known}",
            file=sys.stderr,
        )
        return UNKNOWN_COMMAND_EXIT

    if not a.apply:
        # Dry-run: print the route, exit 0. No backing-script call.
        print(json.dumps(route, indent=2, ensure_ascii=False))
        print(
            f"\n[dry-run] route for /{command} → {route['target_script']}. "
            "Re-run with --apply to execute.",
            file=sys.stderr,
        )
        return SUCCESS_EXIT

    output = execute(route)
    if a.json:
        print(json.dumps({"route": route, "output": output}, indent=2, ensure_ascii=False))
    else:
        print(output)
    return SUCCESS_EXIT


if __name__ == "__main__":
    raise SystemExit(main())
