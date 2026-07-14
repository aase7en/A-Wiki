"""Agent detection from environment variables.

Shared logic used by:
  - scripts/hooks/session_start.py (SessionStart hook → passes ?agent= to dashboard)
  - scripts/detect-agent.sh → .vscode/tasks.json (folderOpen → dashboard with ?agent=)

Each CLI agent leaves a distinctive env fingerprint. We return a lowercase
agent name (claude, codex, zcode, gemini, cursor, windsurf, cline,
antigravity, hermes, kilo, copilot) or None.

Fail-soft: never raises. Returns None on any unexpected condition.
"""
from __future__ import annotations

import os
from typing import Mapping, Optional

# (env_key, agent_name) pairs. Keys ending in "_" trigger a prefix match.
# Order matters: more-specific first. First hit wins.
_CHECKS: list[tuple[str, str]] = [
    ("CLAUDE_PROJECT_DIR", "claude"),
    ("CLAUDECODE", "claude"),
    ("CODEX_HOME", "codex"),
    ("CODEX_AGENT", "codex"),
    ("ZCODE_SESSION", "zcode"),
    ("ZCODE_CLI", "zcode"),
    ("GEMINI_CLI", "gemini"),
    ("GEMINI_MODEL", "gemini"),
    ("CURSOR_TRACE_DIR", "cursor"),
    ("CURSOR_DEBUG", "cursor"),
    ("WINDSURF_USER_DATA_DIR", "windsurf"),
    ("WINDSURF_MACHINE_GUID", "windsurf"),
    ("CLINE_", "cline"),  # prefix check
    ("ANTIGRAVITY_", "antigravity"),
    ("HERMES_AGENT_HOME", "hermes"),
    ("HERMES_CONFIG", "hermes"),
    ("KILO_", "kilo"),
    ("COPILOT_INTEGRATION_ID", "copilot"),
    ("GITHUB_COPILOT_TOKEN", "copilot"),
]


def detect_agent(env: Optional[Mapping[str, str]] = None) -> Optional[str]:
    """Detect the calling agent from env fingerprints.

    Args:
        env: optional env dict (defaults to os.environ). Useful for tests.

    Returns:
        Lowercase agent name, or None if no fingerprint matched.
    """
    if env is None:
        env = os.environ
    try:
        for key, agent in _CHECKS:
            if key.endswith("_"):
                # Prefix match (CLINE_*, ANTIGRAVITY_*, KILO_*).
                if any(k.startswith(key) for k in env):
                    return agent
            elif key in env:
                return agent
    except Exception:
        # Fail-soft: never raise from detection. Unknown env shape → None.
        return None
    return None


__all__ = ["detect_agent"]
