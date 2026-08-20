#!/usr/bin/env python3
"""providers.py — thin provider normalization for the canonical lifecycle
runner (Phase 6).

Provider adapters translate provider payload/event shapes into the ONE
canonical A-Wiki lifecycle contract (scripts/hooks_runner.py +
scripts/hooks/registry.py). Canonical policy lives ONLY behind the shared
boundary — adapters can never bypass hard gates.

Truthful limitations (do not simulate parity):
  - Codex wiring (scripts/setup-codex-config.py) supports 5 lifecycle
    events and has NO UserPromptSubmit — normalize_event raises for it.
"""
from __future__ import annotations

import json

PROVIDERS: dict[str, dict] = {
    "claude": {
        "event_map": {
            "SessionStart": "SessionStart",
            "UserPromptSubmit": "UserPromptSubmit",
            "PreToolUse": "PreToolUse",
            "PostToolUse": "PostToolUse",
            "Stop": "Stop",
            "PostCompact": "PostCompact",
        },
        "payload_shape": "canonical",
    },
    "codex": {
        "event_map": {
            "SessionStart": "SessionStart",
            "PreToolUse": "PreToolUse",
            "PostToolUse": "PostToolUse",
            "Stop": "Stop",
            "PostCompact": "PostCompact",
        },
        "payload_shape": "canonical",
    },
    "gemini": {
        "event_map": {"BeforeTool": "PreToolUse"},
        "payload_shape": "canonical",
    },
    "cline": {
        "event_map": {
            "PreToolUse": "PreToolUse",
            "PostToolUse": "PostToolUse",
            "TaskStart": "SessionStart",
            "TaskComplete": "Stop",
        },
        "payload_shape": "cline",
    },
}


class ProviderError(Exception):
    """Unknown provider/event — deterministic, never a silent fallback."""


# Distinct from every valid canonical dict, including {}. Lifecycle policy is
# applied by the canonical runner after event/classification is known.
MALFORMED_PAYLOAD = object()


def supported_events(provider: str) -> list[str]:
    try:
        return list(PROVIDERS[provider]["event_map"])
    except KeyError as e:
        raise ProviderError(f"unknown provider: {provider!r} "
                            f"(known: {sorted(PROVIDERS)})") from e


def normalize_event(provider: str, event: str) -> str:
    """Map a provider-native event to the canonical lifecycle event."""
    try:
        event_map = PROVIDERS[provider]["event_map"]
    except KeyError as e:
        raise ProviderError(f"unknown provider: {provider!r} "
                            f"(known: {sorted(PROVIDERS)})") from e
    try:
        return event_map[event]
    except KeyError as e:
        raise ProviderError(
            f"provider {provider!r} does not support lifecycle event {event!r} "
            f"(supports: {list(event_map)})") from e


def normalize_payload(provider: str, raw, *, event: str | None = None):
    """Return a canonical dict or MALFORMED_PAYLOAD for invalid input.

    Valid `{}` remains distinct from malformed provider data. Cline's nested
    payload is flattened only after successful JSON/shape validation; its
    `parameters` object becomes canonical `tool_input`.
    """
    try:
        shape = PROVIDERS[provider]["payload_shape"]
    except KeyError as e:
        raise ProviderError(f"unknown provider: {provider!r} "
                            f"(known: {sorted(PROVIDERS)})") from e

    try:
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        data = json.loads(raw) if isinstance(raw, str) else raw
    except (json.JSONDecodeError, UnicodeDecodeError, TypeError):
        return MALFORMED_PAYLOAD
    if not isinstance(data, dict):
        return MALFORMED_PAYLOAD

    if shape == "canonical":
        return data
    if shape != "cline":
        raise ProviderError(f"unsupported payload shape for {provider!r}: {shape!r}")

    # `{}` is a valid empty payload and must not be collapsed into malformed.
    if not data:
        return {}
    if event is None:
        return MALFORMED_PAYLOAD

    wrapper_by_event = {
        "PreToolUse": "preToolUse",
        "PostToolUse": "postToolUse",
        "TaskStart": "taskStart",
        "TaskComplete": "taskComplete",
    }
    wrapper = wrapper_by_event.get(event)
    if wrapper is None:
        return MALFORMED_PAYLOAD
    inner = data.get(wrapper)
    if not isinstance(inner, dict):
        return MALFORMED_PAYLOAD

    result = dict(inner)
    if event in ("PreToolUse", "PostToolUse"):
        tool_name = result.pop("toolName", None)
        parameters = result.pop("parameters", None)
        if tool_name is not None:
            result["tool_name"] = tool_name
        if parameters is not None:
            if not isinstance(parameters, dict):
                return MALFORMED_PAYLOAD
            result["tool_input"] = parameters
    return result
