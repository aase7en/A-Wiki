#!/usr/bin/env python3
"""skill_learning.py — self-learning skill loop for A-Wiki.

A-Wiki's private journal (`log.md`, one `## [date] session | topic` header
per session) and hook telemetry (`.tmp/live-events.jsonl`, one JSON object
per hook check) both silently accumulate evidence of recurring work that has
no dedicated skill yet — the same kebab-named concept touched session after
session, or the same hook blocking the agent over and over. Nothing today
surfaces that evidence; a human has to notice the pattern by memory.

This module gives SessionStart a cheap, offline, read-only way to nudge:
"pattern X recurred in N sessions, no skill covers it — consider
`python scripts/new-skill.py X ...`". It never scaffolds anything itself —
human approval stays entirely manual (see docs/protocols/skill-learning-loop.md).

Design constraints (see docs/protocols/brain-improvement-gate.md — Level 0):
- Free, local-first, fully offline: reads only files already on disk
  (log.md, skills-registry.json, .tmp/live-events.jsonl). No network calls
  anywhere in this module.
- Throttled: a full check only runs if the cache (.tmp/skill-learning-
  cache.json) is missing or older than CHECK_EVERY_DAYS.
- Cached + logged: every real run writes a fresh
  .tmp/skill-suggestions.json (even when empty — it's a freshness marker)
  and updates the throttle cache.
- Fail-soft by construction: any failure (missing log.md, corrupt JSON,
  unwritable cache/suggestions dir, unexpected exception) degrades to
  "no notice" — check_skill_patterns() must never raise.
- Pure logic / injectable paths: every path check_skill_patterns() touches
  is a keyword arg with a real-repo default, so tests never touch the
  actual repo's log.md / skills-registry.json / .tmp/*.

Signal design (see extract_terms()): only lowercase kebab-compound tokens
(e.g. "compaction-suggest", "cost-tier") are treated as pattern candidates.
Single generic words and non-Latin text (including Thai) are deliberately
ignored — kebab compounds are the precise, low-noise signal this repo's
hook/skill/protocol names actually use; a general keyword extractor would
drown in noise (or need language-specific tokenization this module isn't
trying to solve).

Wired into scripts/hooks/session_start.py via run_skill_learning_watch()
(best-effort, wrapped so any exception there also degrades to silence).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Emoji/Thai text in notice lines crashes on non-UTF-8 consoles (Thai
# Windows = cp874). Degrade unencodable characters instead of dying — same
# pattern as scripts/lib/vendor_watch.py / scripts/regen-skill-surfaces.py.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except (AttributeError, ValueError):
        pass  # non-reconfigurable stream (pipes/tests) — already safe

REPO_ROOT = Path(__file__).resolve().parents[2]

CACHE_PATH = REPO_ROOT / ".tmp" / "skill-learning-cache.json"
SUGGESTIONS_PATH = REPO_ROOT / ".tmp" / "skill-suggestions.json"
LOG_PATH = REPO_ROOT / "log.md"
REGISTRY_PATH = REPO_ROOT / "skills-registry.json"
EVENTS_PATH = REPO_ROOT / ".tmp" / "live-events.jsonl"

CHECK_EVERY_DAYS = 7
MIN_SESSIONS = 3
HOOK_BLOCK_THRESHOLD = 5

MAX_NOTICES = 3

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LogSession:
    date: str
    topic: str
    body: str


@dataclass(frozen=True)
class Suggestion:
    pattern: str
    kind: str  # "log-pattern" | "hook-friction"
    sessions: tuple
    count: int
    hint: str


# ---------------------------------------------------------------------------
# log.md parsing
# ---------------------------------------------------------------------------

# `## [2026-07-12] session | topic`, `## [2026-07-11] session-2 | topic`,
# `## [2026-07-11 10:30] — topic` (tolerate an optional time suffix and the
# em-dash form used by some older entries).
_HEADER_RE = re.compile(r"^## \[(\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2})?)\](.*)$")
_GENERIC_H2_RE = re.compile(r"^## ")


def parse_log_sessions(text: str) -> list[LogSession]:
    """Split log.md-shaped text into per-session records.

    A session starts at a line matching `## [<date>]...` and its body runs
    until the next `## ` line (session header or not). Any text before the
    first session header (e.g. a symlink-target line some editors prepend)
    is preamble and is discarded, never raises.
    """
    sessions: list[LogSession] = []
    current: Optional[dict] = None

    def _flush() -> None:
        if current is not None:
            body = "\n".join(current["body_lines"]).strip()
            sessions.append(LogSession(date=current["date"], topic=current["topic"], body=body))

    try:
        for line in text.splitlines():
            m = _HEADER_RE.match(line)
            if m:
                _flush()
                date = m.group(1)
                rest = m.group(2)
                if "|" in rest:
                    topic = rest.split("|", 1)[1].strip()
                else:
                    topic = rest.strip()
                current = {"date": date, "topic": topic, "body_lines": []}
                continue

            if _GENERIC_H2_RE.match(line):
                # A non-session "## " heading ends the current session's
                # body without starting a new one.
                _flush()
                current = None
                continue

            if current is not None:
                current["body_lines"].append(line)
            # else: preamble before the first session header — ignored.

        _flush()
    except Exception:
        return []

    return sessions


# ---------------------------------------------------------------------------
# term extraction
# ---------------------------------------------------------------------------

# Kebab compounds only: >=2 hyphen-joined parts, each part >=2 chars. This
# intentionally excludes single words and non-Latin text (Thai included) —
# see module docstring for why.
_TERM_RE = re.compile(r"[a-z0-9]{2,}(?:-[a-z0-9]{2,})+")

STOPWORDS = frozenset(
    {
        "session-memory",
        "session-end",
        "work-pc",
        "claude-code",
        "a-wiki",
        "log-md",
        "read-only",
        "fail-soft",
    }
)


def extract_terms(session: LogSession) -> set[str]:
    """Extract lowercase kebab-compound terms from a session's topic+body.

    Only `[a-z0-9]{2,}(-[a-z0-9]{2,})+`-shaped tokens count — single generic
    words and non-Latin text (including Thai) never match this pattern and
    are silently skipped, by design (see module docstring).
    """
    try:
        text = f"{session.topic}\n{session.body}".lower()
        terms = set(_TERM_RE.findall(text))
        return terms - STOPWORDS
    except Exception:
        return set()


# ---------------------------------------------------------------------------
# registry coverage
# ---------------------------------------------------------------------------


def _segment_run_match(a: str, b: str) -> bool:
    """True when a's hyphen-segments appear as a contiguous run of b's.

    Segment-boundary matching, not plain substring: the real registry has
    short skill names (ck, pdf, seo, tdd, run...) and a bare `"ck" in
    "check-privacy"` would silently swallow valid suggestions.
    """
    sa, sb = a.split("-"), b.split("-")
    if len(sa) > len(sb):
        return False
    return any(sb[i : i + len(sa)] == sa for i in range(len(sb) - len(sa) + 1))


def registry_covered(pattern: str, registry: dict) -> bool:
    """True if `pattern` already has a skill covering it.

    Covered when `pattern`'s hyphen-segments match a contiguous segment run
    of any skill name or alias (either direction — see _segment_run_match),
    or `pattern` appears as a substring of a skill description — all
    comparisons casefolded.
    """
    try:
        skills = registry.get("skills") if isinstance(registry, dict) else None
        if not isinstance(skills, list):
            return False

        needle = pattern.casefold()

        def _matches(value: str) -> bool:
            v = value.casefold()
            return bool(v) and (
                _segment_run_match(v, needle) or _segment_run_match(needle, v)
            )

        for skill in skills:
            if not isinstance(skill, dict):
                continue
            if _matches(str(skill.get("name", ""))):
                return True
            aliases = skill.get("aliases")
            if isinstance(aliases, list):
                for alias in aliases:
                    if _matches(str(alias)):
                        return True
            description = str(skill.get("description", "")).casefold()
            if description and needle in description:
                return True

        return False
    except Exception:
        return False


# ---------------------------------------------------------------------------
# suggesters
# ---------------------------------------------------------------------------


def _new_skill_hint(pattern: str) -> str:
    return (
        f"python scripts/new-skill.py {pattern} --domain code --phase build"
        "  # ปรับ domain/phase ก่อนรัน"
    )


def suggest_from_log(
    sessions: list[LogSession], registry: dict, min_sessions: int
) -> list[Suggestion]:
    """Terms that recur in >= min_sessions distinct sessions and aren't
    already covered by a registered skill. A term repeated within a single
    session counts once (session identity = date+topic)."""
    try:
        term_sessions: dict[str, list[tuple[str, str]]] = {}
        for session in sessions:
            identity = (session.date, session.topic)
            for term in extract_terms(session):
                bucket = term_sessions.setdefault(term, [])
                if identity not in bucket:
                    bucket.append(identity)

        suggestions: list[Suggestion] = []
        for term, identities in term_sessions.items():
            count = len(identities)
            if count < min_sessions:
                continue
            if registry_covered(term, registry):
                continue
            dates = tuple(date for date, _topic in identities)
            suggestions.append(
                Suggestion(
                    pattern=term,
                    kind="log-pattern",
                    sessions=dates,
                    count=count,
                    hint=_new_skill_hint(term),
                )
            )

        suggestions.sort(key=lambda s: (-s.count, s.pattern))
        return suggestions
    except Exception:
        return []


def suggest_from_events(events_path: Path, threshold: int) -> list[Suggestion]:
    """Hooks that hit `result: "block"` >= threshold times in the jsonl
    telemetry log. Malformed lines and a missing file both degrade to []."""
    try:
        path = Path(events_path)
        if not path.exists():
            return []

        block_counts: dict[str, int] = {}
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except Exception:
                    continue
                if not isinstance(event, dict):
                    continue
                if event.get("type") != "hook_check" or event.get("result") != "block":
                    continue
                hook = event.get("hook")
                if not hook:
                    continue
                block_counts[hook] = block_counts.get(hook, 0) + 1

        suggestions = [
            Suggestion(
                pattern=hook,
                kind="hook-friction",
                sessions=(),
                count=count,
                hint=(
                    f"hook '{hook}' block บ่อย — พิจารณา skill/protocol ช่วยลด friction "
                    "หรือแก้ workflow ที่ต้นทาง"
                ),
            )
            for hook, count in block_counts.items()
            if count >= threshold
        ]
        suggestions.sort(key=lambda s: (-s.count, s.pattern))
        return suggestions
    except Exception:
        return []


# ---------------------------------------------------------------------------
# JSON helpers (never raise)
# ---------------------------------------------------------------------------


def _load_json(path: Path) -> Optional[dict]:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            data = json.load(f)
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _write_json(path: Path, data: dict) -> None:
    try:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True, ensure_ascii=False)
    except Exception:
        pass


def _parse_iso(value: str) -> Optional[datetime]:
    try:
        dt = datetime.fromisoformat(value)
    except Exception:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _resolve_min_sessions(min_sessions: Optional[int], env: dict) -> int:
    if min_sessions is not None:
        return min_sessions
    raw = env.get("AWIKI_SKILL_LOOP_MIN_SESSIONS")
    if raw:
        try:
            return max(1, int(raw))
        except (TypeError, ValueError):
            return MIN_SESSIONS
    return MIN_SESSIONS


def _read_text(path: Path) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception:
        return ""


def _format_notice(suggestion: Suggestion) -> str:
    if suggestion.kind == "hook-friction":
        return (
            f"\U0001f9e0 Skill loop: hook '{suggestion.pattern}' block "
            f"{suggestion.count} ครั้ง — friction สูง ควรมี skill/protocol ช่วย "
            "→ ดู .tmp/skill-suggestions.json"
        )
    return (
        f"\U0001f9e0 Skill loop: '{suggestion.pattern}' ซ้ำ {suggestion.count} sessions "
        "ยังไม่มี skill ครอบ → ดู .tmp/skill-suggestions.json"
    )


# ---------------------------------------------------------------------------
# SessionStart entry point
# ---------------------------------------------------------------------------


def check_skill_patterns(
    now: Optional[datetime] = None,
    log_path: Path = LOG_PATH,
    registry_path: Path = REGISTRY_PATH,
    events_path: Path = EVENTS_PATH,
    cache_path: Path = CACHE_PATH,
    suggestions_path: Path = SUGGESTIONS_PATH,
    min_sessions: Optional[int] = None,
    env: Optional[dict] = None,
) -> list[str]:
    """Throttled, fail-soft SessionStart entry point.

    Returns at most MAX_NOTICES one-line notices. Never raises: any failure
    anywhere in this pipeline (missing log.md, corrupt registry/cache JSON,
    unwritable .tmp/) degrades to returning [] or to skipping just the
    broken piece, never to an exception escaping this function.
    """
    try:
        env = env if env is not None else os.environ
        if env.get("AWIKI_SKILL_LOOP", "1") == "0":
            return []

        now = now or datetime.now(timezone.utc)
        min_sessions = _resolve_min_sessions(min_sessions, env)

        cache = _load_json(cache_path) or {}
        last_checked = cache.get("last_checked") if isinstance(cache, dict) else None
        if last_checked:
            checked_dt = _parse_iso(str(last_checked))
            if checked_dt is not None:
                age_days = (now - checked_dt).total_seconds() / 86400
                if age_days < CHECK_EVERY_DAYS:
                    return []

        sessions = parse_log_sessions(_read_text(Path(log_path)))
        registry = _load_json(Path(registry_path)) or {}

        log_suggestions = suggest_from_log(sessions, registry, min_sessions)
        event_suggestions = suggest_from_events(Path(events_path), HOOK_BLOCK_THRESHOLD)
        all_suggestions = log_suggestions + event_suggestions

        _write_json(
            Path(suggestions_path),
            {
                "generated_at": now.isoformat(),
                "suggestions": [asdict(s) for s in all_suggestions],
            },
        )
        _write_json(Path(cache_path), {"last_checked": now.isoformat()})

        return [_format_notice(s) for s in all_suggestions[:MAX_NOTICES]]
    except Exception:
        return []


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Self-learning skill loop — detect recurring work patterns "
        "with no covering skill (read-only, offline)."
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Force a full check ignoring the throttle cache; print every "
        "suggestion (not capped); never writes to disk.",
    )
    parser.add_argument(
        "--min-sessions",
        type=int,
        default=None,
        help=f"Override MIN_SESSIONS threshold (default {MIN_SESSIONS}).",
    )
    args = parser.parse_args()

    if args.report:
        try:
            sessions = parse_log_sessions(_read_text(LOG_PATH))
            registry = _load_json(REGISTRY_PATH) or {}
            min_sessions = args.min_sessions if args.min_sessions is not None else MIN_SESSIONS
            log_suggestions = suggest_from_log(sessions, registry, min_sessions)
            event_suggestions = suggest_from_events(EVENTS_PATH, HOOK_BLOCK_THRESHOLD)
            all_suggestions = log_suggestions + event_suggestions
        except Exception:
            all_suggestions = []

        if not all_suggestions:
            print("skill-learning --report: no recurring uncovered pattern found")
        for suggestion in all_suggestions:
            print(f"{_format_notice(suggestion)}\n  hint: {suggestion.hint}")
        return

    for notice in check_skill_patterns(min_sessions=args.min_sessions):
        print(notice)


if __name__ == "__main__":
    main()
