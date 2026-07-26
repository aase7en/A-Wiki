"""routing.py — A-Suite intent routing (the shared auto-pick brain).

One implementation, three consumers
-----------------------------------
Agent harnesses do not have comparable hook systems, so identical auto-pick
*mechanism* across agents is not achievable. What IS achievable is identical
auto-pick *data*: every substrate below reads the same ``triggers`` field from
skills-registry.json through the same matcher in this module.

  substrate      agents                                    entry point
  -------------  ----------------------------------------  ---------------------
  hook           Claude Code only (UserPromptSubmit)        scripts/hooks/check_a_route.py
  tool           Codex, ZCode, Gemini, Claude, any MCP      MCP ``skill_route``
  model-read     Cline, Windsurf, Cursor, Aider, Kilo, …    wiki/A-ROUTER.md

Never fork this logic into a consumer. A second copy is a second behaviour.

Why not ``\\b``
---------------
Python's ``\\b`` is Unicode-aware, so it treats Thai characters as word
characters — but Thai is written without inter-word spaces. That makes
``re.search(r"\\bแก้บั๊ก\\b", "ช่วยแก้บั๊กหน่อย")`` fail even though the trigger is
plainly present. Matching is therefore split by character class:

  * ASCII triggers  → prefix boundary, open suffix. ``error`` hits "errors" and
    "an error" but not "terror". The open suffix is deliberate: English
    morphology (plural / -ing / -ed) would otherwise produce false negatives.
  * Non-ASCII triggers → plain substring, which is the only correct option for
    a script with no word delimiters.

The 7-phase spine
-----------------
``A_PHASE_CHAIN`` is an ordered chain the router walks. It is deliberately NOT a
per-skill registry field: ``VALID_LIFECYCLE_PHASES`` is already load-bearing for
``gen_skill_index``, AGENTS.md and the Hermes lifecycle config, and adding
synonym phases (build/implement, verify/test) would require re-triaging the 358
skills currently tagged ``none``. Instead the spine lives here in code and maps
onto the existing lifecycle vocabulary.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any, Iterable, Sequence

# ---------------------------------------------------------------------------
# Phase spine
# ---------------------------------------------------------------------------

#: The A-Suite lifecycle, in order. ask → design → plan → implement → review → debug → test
A_PHASE_CHAIN: tuple[str, ...] = (
    "ask",
    "design",
    "plan",
    "implement",
    "review",
    "debug",
    "test",
)

#: Optional per-skill tag. "any" means the skill fits anywhere in the chain.
VALID_A_PHASES: frozenset[str] = frozenset(A_PHASE_CHAIN) | {"any"}

#: A-phase → the registry ``lifecycle_phase`` values that serve it. A filter
#: hint, not an identity: several A-phases legitimately share one lifecycle
#: phase (ask and design are both "define"; debug and test are both "verify").
A_PHASE_TO_LIFECYCLE: dict[str, frozenset[str]] = {
    "ask":       frozenset({"define"}),
    "design":    frozenset({"define"}),
    "plan":      frozenset({"plan"}),
    "implement": frozenset({"build"}),
    "review":    frozenset({"review"}),
    "debug":     frozenset({"verify"}),
    "test":      frozenset({"verify"}),
}


def next_phase(phase: str) -> str | None:
    """Return the phase after ``phase``, or None at the end of the chain."""
    if phase not in A_PHASE_CHAIN:
        raise ValueError(
            f"unknown A-phase {phase!r}; valid: {', '.join(A_PHASE_CHAIN)}"
        )
    idx = A_PHASE_CHAIN.index(phase)
    if idx + 1 >= len(A_PHASE_CHAIN):
        return None
    return A_PHASE_CHAIN[idx + 1]


# ---------------------------------------------------------------------------
# Trigger rules
# ---------------------------------------------------------------------------

#: Cap per skill. Also bounds the blast radius in gen_hermes, which dumps whole
#: registry records into an 8k-context device.
MAX_TRIGGERS = 8

MIN_ASCII_TRIGGER_LEN = 3
MIN_UNICODE_TRIGGER_LEN = 2

#: A trigger is treated as ASCII (word-boundary matched) when it looks like this.
ASCII_TRIGGER_RE = re.compile(r"^[a-z0-9][a-z0-9 _+-]*$")

#: Verbs so generic they appear in most prompts. Allowing them as triggers would
#: route nearly everything to whichever skill claimed them first.
STOP_TRIGGERS: frozenset[str] = frozenset({
    "do", "make", "fix", "new", "add", "run", "get", "use", "set",
    "ทำ", "ได้", "ใหม่", "แก้", "ช่วย", "หน่อย",
})

# Score weights by trigger length. A 6+ char phrase is a strong signal; a 4-5
# char domain term ("docx", "gsap") is strong enough to route alone; a 3-char
# token ("seo", "api") needs corroboration or it fires on noise.
_SCORE_STRONG = 3
_SCORE_NORMAL = 2
_SCORE_WEAK = 1

#: Minimum total score for a skill to be returned by :func:`route`.
DEFAULT_THRESHOLD = 2
DEFAULT_LIMIT = 3


def normalize(text: str) -> str:
    """NFC-normalise and casefold. Thai combining marks make NFC mandatory."""
    return unicodedata.normalize("NFC", text or "").casefold()


def _is_ascii_trigger(trigger: str) -> bool:
    return bool(ASCII_TRIGGER_RE.fullmatch(trigger))


def _weight(trigger: str) -> int:
    if len(trigger) >= 6:
        return _SCORE_STRONG
    if len(trigger) >= 4:
        return _SCORE_NORMAL
    return _SCORE_WEAK


def match_score(triggers: Sequence[str], text: str) -> int:
    """Total match score of ``triggers`` against ``text``. 0 means no match."""
    if not triggers:
        return 0
    haystack = normalize(text)
    if not haystack:
        return 0
    score = 0
    for raw in triggers:
        if not isinstance(raw, str) or not raw:
            continue
        trigger = normalize(raw)
        if _is_ascii_trigger(trigger):
            # Prefix boundary, open suffix — see module docstring.
            hit = re.search(rf"(?<![a-z0-9]){re.escape(trigger)}", haystack) is not None
        else:
            hit = trigger in haystack
        if hit:
            score += _weight(trigger)
    return score


def route(
    registry: Any,
    text: str,
    limit: int = DEFAULT_LIMIT,
    threshold: int = DEFAULT_THRESHOLD,
) -> list[tuple[str, int]]:
    """Rank canonical skills against ``text``.

    Returns ``[(skill_name, score), ...]`` sorted by score desc, then by shorter
    name (a shorter name is the more general entry point of a family). Returns
    ``[]`` when nothing clears ``threshold`` — callers fall back to ``a-think``
    rather than guessing.
    """
    scored: list[tuple[str, int]] = []
    for skill in getattr(registry, "skills", []) or []:
        if skill.get("status") != "canonical":
            continue
        triggers = skill.get("triggers")
        if not triggers:
            continue
        score = match_score(triggers, text)
        if score >= threshold:
            scored.append((skill["name"], score))
    scored.sort(key=lambda pair: (-pair[1], len(pair[0]), pair[0]))
    return scored[:limit]


def validate_triggers(triggers: Any, ctx: str) -> list[str]:
    """Validate a ``triggers`` value. Returns human-readable errors; [] = valid.

    Called from ``validate_registry`` so a bad trigger cannot reach the registry
    in the first place — a false-positive trigger is far more damaging than a
    missing one, because it misroutes every prompt that happens to contain it.
    """
    errors: list[str] = []
    if not isinstance(triggers, list):
        return [f"{ctx}: triggers must be a list, got {type(triggers).__name__}"]
    if len(triggers) > MAX_TRIGGERS:
        errors.append(
            f"{ctx}: at most {MAX_TRIGGERS} triggers allowed, got {len(triggers)}"
        )

    seen: set[str] = set()
    for t in triggers:
        if not isinstance(t, str):
            errors.append(f"{ctx}: trigger {t!r} must be a string")
            continue
        if not t.strip():
            errors.append(f"{ctx}: trigger must not be blank")
            continue
        if t != t.lower():
            errors.append(f"{ctx}: trigger {t!r} must be lowercase")
            continue
        if t in seen:
            errors.append(f"{ctx}: duplicate trigger {t!r}")
            continue
        seen.add(t)
        if t in STOP_TRIGGERS:
            errors.append(
                f"{ctx}: trigger {t!r} is too generic (stop-list) — it would "
                f"match most prompts"
            )
            continue
        min_len = (
            MIN_ASCII_TRIGGER_LEN if _is_ascii_trigger(t) else MIN_UNICODE_TRIGGER_LEN
        )
        if len(t) < min_len:
            errors.append(
                f"{ctx}: trigger {t!r} is too short (min {min_len} chars for "
                f"{'ascii' if _is_ascii_trigger(t) else 'non-ascii'})"
            )
    return errors


def skills_for_phase(registry: Any, phase: str) -> list[dict[str, Any]]:
    """Canonical skills that serve an A-phase.

    Prefers an explicit ``a_phase`` tag; falls back to the lifecycle_phase map so
    the ~400 untagged skills still participate without a mass re-triage.
    """
    if phase not in A_PHASE_CHAIN:
        raise ValueError(f"unknown A-phase {phase!r}")
    lifecycle = A_PHASE_TO_LIFECYCLE[phase]
    tagged: list[dict[str, Any]] = []
    inferred: list[dict[str, Any]] = []
    for skill in getattr(registry, "skills", []) or []:
        if skill.get("status") != "canonical":
            continue
        a_phase = skill.get("a_phase")
        if a_phase == phase or a_phase == "any":
            tagged.append(skill)
        elif a_phase is None and skill.get("lifecycle_phase") in lifecycle:
            inferred.append(skill)
    return tagged + inferred


__all__ = [
    "A_PHASE_CHAIN",
    "A_PHASE_TO_LIFECYCLE",
    "VALID_A_PHASES",
    "MAX_TRIGGERS",
    "STOP_TRIGGERS",
    "ASCII_TRIGGER_RE",
    "DEFAULT_LIMIT",
    "DEFAULT_THRESHOLD",
    "normalize",
    "match_score",
    "next_phase",
    "route",
    "skills_for_phase",
    "validate_triggers",
]
