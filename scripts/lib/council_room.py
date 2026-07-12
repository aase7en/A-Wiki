#!/usr/bin/env python3
"""council_room.py — Brainstorm Council core: multi-model parallel fan-out.

The PRIMARY AGENT (top-tier model, running in-session) is the MODERATOR.
This module only does the cheap part: fan one question out to K free/cheap
models in PARALLEL via the EXISTING scripts/swarm/delegate.sh, collect their
answers into a transcript JSON, and emit Live Dashboard events. It never
calls a paid model for synthesis — synthesis text is written back by the
moderator afterward via add_synthesis() / `scripts/swarm/council.py
synthesize`.

Design constraints (see docs/protocols/brainstorm-council.md and
docs/protocols/brain-improvement-gate.md — Cost-First Pyramid):
- Cost-first: participants are chosen free-first (FREE_FIRST_ORDER), never a
  paid model unless nothing free/cheap is available.
- Zero delegate.sh changes: a specific engine is forced by disabling the
  other five via env (AWIKI_DISABLE_<ID>=1) — see force_engine_env().
- Fail-soft per participant: one engine failing (timeout, bad key, network)
  must never kill the round — see convene()/_run_one(). The round itself may
  still fail (no participants, or every participant failed); the CLI is
  allowed to exit non-zero in that case (unlike SessionStart modules, which
  must always degrade to silence).
- Every subprocess call that decodes text output must pin
  encoding="utf-8", errors="replace" (Thai Windows = cp874; a bare
  text=True blocked a git push on 2026-07-12 — see
  tests/test_hooks_subprocess_encoding.py).
- All paths/runners/emitters are injectable kwargs so tests never touch the
  real network, real delegate.sh, or anything outside tmp_path.

Wired manually: `scripts/swarm/council.py` (CLI) is the thin wrapper the
moderator drives. No SessionStart hook — this is an on-demand tool, not a
passive check.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

# Emoji/Thai text in CLI output crashes on non-UTF-8 consoles (Thai Windows
# = cp874). Degrade unencodable characters instead of dying — same pattern
# as scripts/lib/vendor_watch.py / scripts/lib/skill_learning.py.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass  # non-reconfigurable stream (pipes/tests) — already safe

REPO_ROOT = Path(__file__).resolve().parents[2]
COUNCIL_DIR = REPO_ROOT / ".tmp" / "council"
DELEGATE_SH = REPO_ROOT / "scripts" / "swarm" / "delegate.sh"
EVENT_LOGGER = REPO_ROOT / "scripts" / "live-dashboard" / "event_logger.py"

# Cost-first: free → subscription → pay-as-you-go. See
# docs/protocols/brainstorm-council.md and the Cost-First Decision Pyramid
# in CLAUDE.md. Never reordered per-call — capability ranking (like
# delegate.sh's _run_ranked) is out of scope for this module.
FREE_FIRST_ORDER: tuple[str, ...] = ("GEMINI", "OPENROUTER", "GROQ", "ZHIPU", "DEEPSEEK", "ANTHROPIC")

DEFAULT_PARTICIPANTS = 3
DEFAULT_TASK_TYPE = "reason"

# council-YYYYMMDD-HHMMSS-xxxx (4 hex chars) — see _generate_id().
COUNCIL_ID_RE = re.compile(r"^council-\d{8}-\d{6}-[0-9a-f]{4}$")

# Engine id -> API key env var. Used by plan_participants() to filter out
# engines with no key configured. Must stay in sync with delegate.sh's
# engine wrappers (try_gemini_direct, try_openrouter_model, try_groq_model,
# try_zhipu_direct, try_deepseek_direct, try_anthropic_haiku).
ENGINE_KEY_ENV: dict[str, str] = {
    "GEMINI": "GEMINI_API_KEY",
    "OPENROUTER": "OPENROUTER_API_KEY",
    "GROQ": "GROQ_API_KEY",
    "ZHIPU": "ZHIPU_API_KEY",
    "DEEPSEEK": "DEEPSEEK_API_KEY",
    "ANTHROPIC": "ANTHROPIC_API_KEY",
}

RunnerFn = Callable[[str, str, str, float, dict], "tuple[bool, str]"]
EmitFn = Callable[..., None]


# ---------------------------------------------------------------------------
# Participant planning
# ---------------------------------------------------------------------------


def plan_participants(n: int, env: dict) -> list[str]:
    """Pick up to `n` engine ids from FREE_FIRST_ORDER, cost-first.

    Skips an engine if `AWIKI_DISABLE_<ID>=1` is set in `env`, or if its API
    key env var (ENGINE_KEY_ENV) is missing/empty in `env`. Returns fewer
    than `n` (down to an empty list) if not enough engines are available —
    never raises, never pads with unavailable engines.
    """
    n = max(0, n)
    available: list[str] = []
    for engine in FREE_FIRST_ORDER:
        if str(env.get(f"AWIKI_DISABLE_{engine}", "")) == "1":
            continue
        key_var = ENGINE_KEY_ENV[engine]
        if not env.get(key_var):
            continue
        available.append(engine)
    return available[:n]


def force_engine_env(engine: str, base_env: dict) -> dict:
    """Return a COPY of base_env forcing delegate.sh to use only `engine`.

    delegate.sh's `_provider_enabled <ID>` reads `AWIKI_DISABLE_<ID>` — so
    forcing a specific engine (with zero delegate.sh changes) means
    disabling the five OTHER engine ids and making sure the chosen engine's
    own disable var is absent. `base_env` is never mutated; any unrelated
    key (e.g. AWIKI_DISABLE_DASHBOARD_AUTOSTART — a different namespace) is
    passed through untouched.
    """
    new_env = dict(base_env)
    for other in FREE_FIRST_ORDER:
        var = f"AWIKI_DISABLE_{other}"
        if other == engine:
            new_env.pop(var, None)
        else:
            new_env[var] = "1"
    return new_env


# ---------------------------------------------------------------------------
# Transport: delegate.sh runner + dashboard emitter
# ---------------------------------------------------------------------------


def default_runner(
    engine: str,
    question: str,
    task_type: str,
    timeout: float,
    env: dict,
) -> "tuple[bool, str]":
    """Run scripts/swarm/delegate.sh with `engine` forced via `env`.

    Never raises: subprocess.TimeoutExpired and any other exception (e.g.
    OSError when bash isn't on PATH) degrade to (False, reason) so one
    participant's transport failure can never take down the whole council
    round (see convene()/_run_one()).

    ok = returncode == 0 and non-empty stdout. On success returns
    (True, stdout). On failure returns (False, stderr-tail-or-fallback).
    """
    cmd = ["bash", str(DELEGATE_SH), task_type, question]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env=env,
        )
    except subprocess.TimeoutExpired:
        return False, f"timeout after {timeout}s"
    except Exception as exc:  # OSError (missing bash), etc. — never raise
        return False, f"runner error: {exc}"

    stdout = (result.stdout or "").strip()
    if result.returncode == 0 and stdout:
        return True, stdout

    stderr_tail = (result.stderr or "").strip()
    if stderr_tail:
        return False, stderr_tail[-500:]
    return False, f"exit {result.returncode}, empty stdout"


def default_emit(event_type: str, **fields) -> None:
    """Fire-and-forget dashboard event via scripts/live-dashboard/event_logger.py.

    Never raises — a dashboard that isn't running (or a missing python3)
    must never break a council round.
    """
    try:
        args = [sys.executable, str(EVENT_LOGGER), event_type]
        args += [f"{k}={v}" for k, v in fields.items()]
        subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# ID generation
# ---------------------------------------------------------------------------


def _generate_id(now: datetime) -> str:
    return f"council-{now.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:4]}"


# ---------------------------------------------------------------------------
# convene() — the core fan-out
# ---------------------------------------------------------------------------


def _run_one(
    engine: str,
    question: str,
    task_type: str,
    timeout: float,
    runner: RunnerFn,
    forced_env: dict,
) -> dict:
    """Run one participant, timing it, never letting an exception escape.

    A runner raising (rather than returning (False, reason)) is still
    contained here — fail-soft applies even to a badly-behaved injected
    runner in tests.
    """
    t0 = time.monotonic()
    try:
        ok, answer = runner(engine, question, task_type, timeout, forced_env)
    except Exception as exc:  # defensive: fail-soft even if runner misbehaves
        ok, answer = False, f"runner exception: {exc}"
    latency_s = round(time.monotonic() - t0, 3)
    return {
        "engine": engine,
        "status": "ok" if ok else "fail",
        "answer": answer,
        "latency_s": latency_s,
    }


def _write_transcript(council_dir: Path, council_id: str, transcript: dict) -> None:
    council_dir.mkdir(parents=True, exist_ok=True)
    path = council_dir / f"{council_id}.json"
    path.write_text(json.dumps(transcript, ensure_ascii=False, indent=2), encoding="utf-8")


def convene(
    question: str,
    n: int = DEFAULT_PARTICIPANTS,
    task_type: str = DEFAULT_TASK_TYPE,
    timeout: float = 90,
    runner: RunnerFn = default_runner,
    emit: EmitFn = default_emit,
    env: Optional[dict] = None,
    now: Optional[datetime] = None,
    council_dir: Optional[Path] = None,
) -> dict:
    """Fan `question` out to up to `n` free/cheap models in parallel.

    Plans participants cost-first (plan_participants), runs them
    concurrently (ThreadPoolExecutor, one worker per participant, each
    forced to a single engine via force_engine_env), and always writes a
    transcript to `<council_dir>/<id>.json` — even when there are zero
    participants or every participant fails. One participant failing never
    kills the round (see _run_one()); the returned/written transcript
    always reflects every attempted participant.

    Returns the transcript dict:
      {id, question, task_type, created_at, participants: [...],
       synthesis: None, status}
    where status is "no-participants" | "ok" (>=1 participant succeeded) |
    "all-failed" (>=1 participant attempted, none succeeded).
    """
    env = dict(env) if env is not None else dict(os.environ)
    now = now or datetime.now(timezone.utc)
    council_dir = Path(council_dir) if council_dir is not None else COUNCIL_DIR
    council_id = _generate_id(now)

    engines = plan_participants(n, env)

    emit("council_start", question=question[:120], n=len(engines))

    participants: list[dict] = []
    if engines:
        with ThreadPoolExecutor(max_workers=len(engines)) as executor:
            futures = {
                executor.submit(
                    _run_one, engine, question, task_type, timeout, runner, force_engine_env(engine, env)
                ): engine
                for engine in engines
            }
            results_by_engine = {futures[f]: f.result() for f in futures}
        # Preserve plan_participants()'s cost-first order in the transcript,
        # not thread-completion order.
        participants = [results_by_engine[engine] for engine in engines]

    for p in participants:
        emit("council_answer", engine=p["engine"], result=p["status"])

    if not engines:
        status = "no-participants"
    elif any(p["status"] == "ok" for p in participants):
        status = "ok"
    else:
        status = "all-failed"

    transcript = {
        "id": council_id,
        "question": question,
        "task_type": task_type,
        "created_at": now.isoformat(),
        "participants": participants,
        "synthesis": None,
        "status": status,
    }

    _write_transcript(council_dir, council_id, transcript)
    return transcript


# ---------------------------------------------------------------------------
# Synthesis + read-back (moderator-facing)
# ---------------------------------------------------------------------------


def _council_path(council_id: str, council_dir: Optional[Path]) -> Path:
    if not COUNCIL_ID_RE.match(council_id):
        raise ValueError(f"invalid council id: {council_id!r}")
    base = Path(council_dir) if council_dir is not None else COUNCIL_DIR
    return base / f"{council_id}.json"


def add_synthesis(
    council_id: str,
    text: str,
    author: str = "primary-agent",
    council_dir: Optional[Path] = None,
    emit: EmitFn = default_emit,
    now: Optional[datetime] = None,
) -> dict:
    """Record the moderator's synthesis onto an existing council transcript.

    Raises ValueError on a malformed/path-traversal id (validated against
    COUNCIL_ID_RE before any filesystem access) or an unknown council id —
    the CLI surfaces either as exit 1. Never calls a paid model itself: the
    synthesis text is supplied by the caller (the moderator), this function
    only persists it.
    """
    path = _council_path(council_id, council_dir)
    if not path.is_file():
        raise ValueError(f"council not found: {council_id}")

    transcript = json.loads(path.read_text(encoding="utf-8"))
    now = now or datetime.now(timezone.utc)
    transcript["synthesis"] = {"text": text, "author": author, "added_at": now.isoformat()}
    path.write_text(json.dumps(transcript, ensure_ascii=False, indent=2), encoding="utf-8")

    emit("council_synthesis", id=council_id, author=author)
    return transcript


def load_council(council_id: str, council_dir: Optional[Path] = None) -> dict:
    """Load a transcript by id. Raises ValueError on bad id or missing council."""
    path = _council_path(council_id, council_dir)
    if not path.is_file():
        raise ValueError(f"council not found: {council_id}")
    return json.loads(path.read_text(encoding="utf-8"))


def list_councils(council_dir: Optional[Path] = None) -> list[dict]:
    """List councils newest-first with a compact summary per council.

    A missing council_dir (nothing convened yet) degrades to []. A
    transcript file that fails to parse is skipped rather than raising —
    listing must never break because one file on disk is corrupt.
    """
    base = Path(council_dir) if council_dir is not None else COUNCIL_DIR
    if not base.is_dir():
        return []

    items: list[dict] = []
    for path in sorted(base.glob("council-*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        participants = data.get("participants") or []
        items.append(
            {
                "id": data.get("id"),
                "question": data.get("question"),
                "created_at": data.get("created_at"),
                "participants_ok": sum(1 for p in participants if p.get("status") == "ok"),
                "participants_total": len(participants),
                "has_synthesis": data.get("synthesis") is not None,
            }
        )

    items.sort(key=lambda x: x.get("created_at") or "", reverse=True)
    return items
