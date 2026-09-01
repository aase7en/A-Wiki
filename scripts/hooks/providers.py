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
        # Native events verified against google-gemini/gemini-cli
        # docs/hooks/reference.md (2026-08-22). BeforeAgent is deliberately
        # NOT mapped to UserPromptSubmit: its exit-2 erases the user prompt —
        # no safe equivalent (routing stays on MCP skill_route).
        "event_map": {
            "BeforeTool": "PreToolUse",
            "AfterTool": "PostToolUse",
            "SessionStart": "SessionStart",
            "SessionEnd": "Stop",
        },
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
    # ZCode is a Claude Code workalike: same hook settings schema (matcher /
    # command blocks), same tool vocabulary (Edit/Write/MultiEdit/Bash/Agent),
    # Claude-shaped stdin payloads. Verified live 2026-08-22 — PreToolUse
    # hooks fire; previously .zcode/config.json simply never wired them
    # (docs/plans/2026-08-21-auto-skill-consolidation.md §4 defect #1).
    "zcode": {
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
}


class ProviderError(Exception):
    """Unknown provider/event — deterministic, never a silent fallback."""


# Distinct from every valid canonical dict, including {}. Lifecycle policy is
# applied by the canonical runner after event/classification is known.
MALFORMED_PAYLOAD = object()


# Provider-native tool names are normalized here so every registered policy
# hook receives the same Claude-shaped action vocabulary. Policy hooks must not
# grow their own provider-specific alias lists.
_TOOL_NAME_MAP = {
    "gemini": {
        "write_file": "Write",
        "replace": "Edit",
        "run_shell_command": "Bash",
    },
    "cline": {
        "write_to_file": "Write",
        "replace_in_file": "Edit",
        "execute_command": "Bash",
    },
}


def _canonicalize_tool_call(provider, tool_name, tool_input):
    """Normalize one provider-native tool call to the canonical hook schema."""
    canonical_name = _TOOL_NAME_MAP.get(provider, {}).get(tool_name, tool_name)
    if not isinstance(tool_input, dict):
        return canonical_name, tool_input

    canonical_input = dict(tool_input)
    if provider == "cline" and canonical_name in ("Write", "Edit", "MultiEdit"):
        # Cline file tools use `path`; canonical A-Wiki hooks use `file_path`.
        if "file_path" not in canonical_input and "path" in canonical_input:
            canonical_input["file_path"] = canonical_input["path"]
        canonical_input.pop("path", None)
    return canonical_name, canonical_input


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
        if provider != "gemini" or not data:
            return data
        result = dict(data)
        tool_name = result.get("tool_name")
        tool_input = result.get("tool_input")
        if tool_name is not None:
            if not isinstance(tool_name, str) or not isinstance(tool_input, dict):
                return MALFORMED_PAYLOAD
            tool_name, tool_input = _canonicalize_tool_call(
                provider, tool_name, tool_input
            )
            result["tool_name"] = tool_name
            result["tool_input"] = tool_input
        return result
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

    workspace_roots = data.get("workspaceRoots")
    if workspace_roots is not None:
        if not isinstance(workspace_roots, list) or any(
            not isinstance(root, str) or not root.strip()
            for root in workspace_roots
        ):
            return MALFORMED_PAYLOAD
    result = dict(inner)
    if workspace_roots:
        if event in ("PreToolUse", "PostToolUse") and len(workspace_roots) != 1:
            return MALFORMED_PAYLOAD
        if len(workspace_roots) == 1:
            result["cwd"] = workspace_roots[0].strip()
    if event in ("PreToolUse", "PostToolUse"):
        # Cline documentation has used both `toolName` and `tool` across hook
        # surfaces. Accept either, but conflicting values are malformed rather
        # than choosing a weaker policy path.
        tool_name = result.pop("toolName", None)
        tool_alias = result.pop("tool", None)
        if tool_name is not None and tool_alias is not None and tool_name != tool_alias:
            return MALFORMED_PAYLOAD
        if tool_name is None:
            tool_name = tool_alias

        parameters = result.pop("parameters", None)
        if tool_name is not None:
            if not isinstance(tool_name, str) or not isinstance(parameters, dict):
                return MALFORMED_PAYLOAD
            tool_name, parameters = _canonicalize_tool_call(
                provider, tool_name, parameters
            )
            result["tool_name"] = tool_name
            result["tool_input"] = parameters
        elif parameters is not None:
            # Parameters without an action cannot be safely classified.
            return MALFORMED_PAYLOAD
    return result
