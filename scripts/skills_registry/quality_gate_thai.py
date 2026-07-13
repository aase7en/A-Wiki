"""Quality gate for Thai skill metadata produced by LLM.

Parallel to scripts/batch/quality_gate.py (source-ingest), but validates
JSON output for skills-registry.json v2 fields:
    th_description, when_to_use, examples, process_steps, invocation

Returns (is_valid, reason, parsed_dict). When is_valid, parsed_dict is the
clean dict ready to merge into a registry skill. When invalid, parsed_dict
is {} and reason explains why.

Checks (in order):
  1. JSON parse succeeds (after stripping fences / preamble if present)
  2. Required keys present: th_description, when_to_use, examples
  3. th_description: 80-400 chars, ≥30% Thai chars (U+0E00-0E7F)
  4. when_to_use: 20-150 chars, ≥20% Thai chars
  5. examples: list of 1-2 dicts, each with 'scenario' and 'how'
  6. process_steps (if present): list of 3-6 non-empty strings, each ≤60 chars
  7. invocation (if present): one of {auto, manual, both}
  8. No secret/path leaks: /Users, C:\\Users, account names, API key patterns
"""
from __future__ import annotations

import json
import re
from typing import Any

REQUIRED_KEYS = ("th_description", "when_to_use", "examples")
OPTIONAL_KEYS = ("process_steps", "invocation", "invocation_hint")
VALID_INVOCATIONS = frozenset({"auto", "manual", "both"})

THAI_RANGE = range(0x0E00, 0x0E7F + 1)

# Patterns that signal leaked private data — must never enter the public registry.
SECRET_PATTERNS = [
    re.compile(r"/Users/[A-Za-z0-9_-]+", re.IGNORECASE),
    re.compile(r"C:\\Users\\[A-Za-z0-9_-]+", re.IGNORECASE),
    re.compile(r"/home/[A-Za-z0-9_-]+", re.IGNORECASE),
    # API key shapes (loose — match shape, not a real key)
    re.compile(r"(?:sk-|pk-|AIza|ghp_)[A-Za-z0-9_-]{16,}"),
    # Google Drive paths and the private junction
    re.compile(r"A-Wiki-Data/", re.IGNORECASE),
]


def _strip_fences(text: str) -> str:
    """Strip ```json ... ``` fences and surrounding whitespace/preamble.

    Some models emit fences despite the prompt forbidding them. We tolerate
    them rather than reject — the gate's job is to validate content, not
    punish formatting quirks.
    """
    text = text.strip()
    # Strip ```json ... ``` or ``` ... ```
    fence_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()
    # If there is text before '{', drop it.
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace >= 0 and last_brace > first_brace:
        text = text[first_brace : last_brace + 1]
    return text


def _thai_ratio(s: str) -> float:
    """Fraction of chars in Thai Unicode range. Empty string → 0.0."""
    if not s:
        return 0.0
    chars = [c for c in s if not c.isspace()]
    if not chars:
        return 0.0
    thai = sum(1 for c in chars if ord(c) in THAI_RANGE)
    return thai / len(chars)


def _has_secret(text: str) -> str | None:
    """Return matched secret pattern string if found, else None."""
    for pat in SECRET_PATTERNS:
        m = pat.search(text)
        if m:
            return m.group(0)
    return None


def validate(output: str, skill_name: str = "") -> tuple[bool, str, dict[str, Any]]:
    """Validate one LLM output blob.

    Returns (is_valid, reason, parsed_dict).
      is_valid=True  → parsed_dict is ready to merge into the registry
      is_valid=False → parsed_dict is {} and reason explains the failure
    """
    if not output or not output.strip():
        return False, "empty output", {}

    cleaned = _strip_fences(output)
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        return False, f"JSON parse failed: {e}", {}

    if not isinstance(data, dict):
        return False, "top-level JSON must be an object", {}

    prefix = f"[{skill_name}] " if skill_name else ""

    # Required keys
    missing = [k for k in REQUIRED_KEYS if k not in data]
    if missing:
        return False, f"{prefix}missing required keys: {', '.join(missing)}", {}

    # Reject unknown keys (defensive — prompt forbids extras, but enforce)
    allowed = set(REQUIRED_KEYS) | set(OPTIONAL_KEYS)
    extras = [k for k in data if k not in allowed]
    if extras:
        return False, f"{prefix}unknown keys: {', '.join(extras)}", {}

    # th_description
    th = data.get("th_description", "")
    if not isinstance(th, str):
        return False, f"{prefix}th_description must be a string", {}
    if not (80 <= len(th) <= 400):
        return False, f"{prefix}th_description length {len(th)} outside 80-400", {}
    if _thai_ratio(th) < 0.30:
        return False, f"{prefix}th_description Thai ratio {_thai_ratio(th):.0%} < 30%", {}

    # when_to_use
    wtu = data.get("when_to_use", "")
    if not isinstance(wtu, str):
        return False, f"{prefix}when_to_use must be a string", {}
    if not (20 <= len(wtu) <= 150):
        return False, f"{prefix}when_to_use length {len(wtu)} outside 20-150", {}
    if _thai_ratio(wtu) < 0.20:
        return False, f"{prefix}when_to_use Thai ratio {_thai_ratio(wtu):.0%} < 20%", {}

    # examples
    examples = data.get("examples")
    if not isinstance(examples, list) or not (1 <= len(examples) <= 2):
        return False, f"{prefix}examples must be a list of 1-2 entries", {}
    for i, ex in enumerate(examples):
        if not isinstance(ex, dict):
            return False, f"{prefix}examples[{i}] must be an object", {}
        if "scenario" not in ex or "how" not in ex:
            return False, f"{prefix}examples[{i}] must have scenario+how", {}
        if not isinstance(ex["scenario"], str) or not isinstance(ex["how"], str):
            return False, f"{prefix}examples[{i}].scenario/how must be strings", {}
        if not ex["scenario"].strip() or not ex["how"].strip():
            return False, f"{prefix}examples[{i}] scenario/how must be non-empty", {}

    # process_steps (optional)
    if "process_steps" in data:
        ps = data["process_steps"]
        if ps is None:
            data.pop("process_steps")  # tolerate null = absent
        else:
            if not isinstance(ps, list):
                return False, f"{prefix}process_steps must be a list", {}
            if not (3 <= len(ps) <= 6):
                return False, f"{prefix}process_steps length {len(ps)} outside 3-6", {}
            for i, step in enumerate(ps):
                if not isinstance(step, str) or not step.strip():
                    return False, f"{prefix}process_steps[{i}] must be non-empty string", {}
                # Thai has no inter-word spaces, so a single "step" is naturally
                # ~1.5× the char count of an equivalent English phrase. Cap of
                # 60 chars accommodates Thai compound words while still keeping
                # each step concise enough for the simulation station UI.
                if len(step) > 60:
                    return False, f"{prefix}process_steps[{i}] length {len(step)} > 60", {}

    # invocation (optional, default manual)
    inv = data.get("invocation", "manual")
    if inv not in VALID_INVOCATIONS:
        return False, f"{prefix}invocation {inv!r} not in {sorted(VALID_INVOCATIONS)}", {}
    data.setdefault("invocation", "manual")

    # Secret/path leak scan across all string values
    blob = json.dumps(data, ensure_ascii=False)
    leak = _has_secret(blob)
    if leak:
        return False, f"{prefix}leaked private data: {leak!r}", {}

    return True, "ok", data


__all__ = ["validate", "REQUIRED_KEYS", "OPTIONAL_KEYS", "VALID_INVOCATIONS"]
