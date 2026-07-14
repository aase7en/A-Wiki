#!/usr/bin/env python3
"""
Hook: Subagent Fan-out Diversity Guard (warn-only)
---------------------------------------------------
PreToolUse hook on the `Agent` tool. Inspects the `subagent_type` of each
Agent call in the *current message* and warns (stderr, exit 0) when >=3 calls
would resolve to the same provider/bucket — the exact condition that caused
the 2026-07-14 "Provider rate limited the model request" failures when 3
parallel Explore subagents all hit Gemini's free-tier single bucket.

Design choices:
  - WARN-ONLY (exit 0 always). Never blocks — the primary agent may
    intentionally override (e.g. a deliberate 3x scan against one model).
  - Override: HOOK_SKIP=check_subagent_fanout
  - Uses a per-message state file to count concurrent Agent calls, because
    each PreToolUse fires per-tool-call, not per-message.
  - Provider resolution: looks up the subagent's default model from its
    frontmatter (if available) or from a small built-in fallback table, then
    maps model -> provider bucket. Falls back to "unknown" (no warning) if
    it can't resolve — never false-positives on ambiguous cases.

See: docs/protocols/subagent-model-routing.md
"""
import sys
import json
import os
import re
import time
import glob as globlib
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
REPO_ROOT = HOOKS_DIR.parent.parent
STATE_FILE = REPO_ROOT / ".tmp" / "subagent_fanout_state.json"
WINDOW_SECONDS = 30  # calls within this window count as one "message"
MAX_PER_BUCKET = 2   # warn at >=3 against one bucket

# ---------------------------------------------------------------------------
# Provider bucket resolution
# ---------------------------------------------------------------------------
# Models are grouped by the rate-limit bucket they share (same API key).
# Free-tier buckets are tight; paid buckets are looser. The goal is to detect
# when N parallel calls would collide on ONE free-tier bucket.
BUCKET_BY_MODEL_PREFIX = {
    # Gemini (Google AI Studio free tier — tightest bucket)
    "gemini": "gemini-free",
    "gemini-3.5-flash": "gemini-free",
    # DeepSeek (paid, but cheap — separate bucket per key)
    "deepseek-v4-flash": "deepseek",
    "deepseek-v4-pro": "deepseek",
    "deepseek": "deepseek",
    # OpenRouter free
    "openrouter/free": "openrouter-free",
    "nemotron": "openrouter-free",
    # Z.ai GLM
    "glm-5": "glm",
    "glm-5.2": "glm",
    "glm-5-turbo": "glm",
    # Anthropic aliases (paid, looser)
    "sonnet": "anthropic",
    "opus": "anthropic",
    "haiku": "anthropic",
}


def provider_for_model(model_str: str) -> str:
    """Map a model string to a rate-limit bucket.

    Accepts both aliases ('sonnet') and custom provider refs
    ('custom:<provider-id>:<model>'). Returns 'unknown' if unmapped.
    """
    if not model_str:
        return "unknown"
    m = model_str.strip().lower()
    # custom:<provider-id>:<model>  -> use the model portion
    if m.startswith("custom:"):
        parts = m.split(":")
        if len(parts) >= 3:
            m = parts[-1]
    for prefix, bucket in BUCKET_BY_MODEL_PREFIX.items():
        if m.startswith(prefix):
            return bucket
    return "unknown"


# Subagent-type -> default model. Populated lazily from frontmatter files.
# Hardcoded fallbacks cover the built-ins so the hook works even before any
# custom agents exist.
SUBAGENT_DEFAULT_MODELS = {
    "Explore": "deepseek-v4-flash",   # post-SA1.2 override in agents-state.json
    "general-purpose": "sonnet",       # primary agent tier by default
    "free-ai-helper-100": "gemini-3.5-flash",
}


def load_subagent_model(subagent_type: str) -> str:
    """Resolve a subagent_type to its default model.

    1. Hardcoded fallback table.
    2. ~/.zcode/agents/<name>.md frontmatter `model:` field.
    3. repo agents/<name>.md frontmatter.
    Returns "" if unknown.
    """
    if subagent_type in SUBAGENT_DEFAULT_MODELS:
        return SUBAGENT_DEFAULT_MODELS[subagent_type]
    # Try to read frontmatter from agent definition files.
    candidates = []
    home = Path(os.path.expanduser("~"))
    candidates.append(home / ".zcode" / "agents" / f"{subagent_type}.md")
    candidates.append(REPO_ROOT / "agents" / f"{subagent_type}.md")
    candidates.append(REPO_ROOT / "agents" / "subagents" / f"{subagent_type}.md")
    for path in candidates:
        try:
            if path.exists():
                text = path.read_text(encoding="utf-8", errors="replace")
                # crude frontmatter parse: look for `model:` in the first --- block
                m = re.search(r"^model:\s*[\"']?([^\"'\n]+)[\"']?\s*$",
                              text, re.MULTILINE)
                if m:
                    return m.group(1).strip()
        except Exception:
            continue
    return ""


# ---------------------------------------------------------------------------
# Per-message state (count concurrent Agent calls within a time window)
# ---------------------------------------------------------------------------
def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"calls": []}


def save_state(state: dict) -> None:
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(state), encoding="utf-8")
    except Exception:
        pass


def prune_old_calls(state: dict, now: float) -> list:
    """Keep only calls within WINDOW_SECONDS; return the pruned list."""
    kept = [c for c in state.get("calls", []) if now - c.get("ts", 0) <= WINDOW_SECONDS]
    state["calls"] = kept
    return kept


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    if os.environ.get("HOOK_SKIP") == "check_subagent_fanout":
        return 0

    try:
        input_data = json.load(sys.stdin)
    except Exception:
        return 0

    tool_name = input_data.get("tool_name", "")
    if tool_name != "Agent":
        return 0

    tool_input = input_data.get("tool_input", {})
    subagent_type = (
        tool_input.get("subagent_type")
        or tool_input.get("subagentType")
        or ""
    )
    if not subagent_type:
        return 0

    model = load_subagent_model(subagent_type)
    bucket = provider_for_model(model)

    now = time.time()
    state = load_state()
    recent = prune_old_calls(state, now)

    # Record this call
    recent.append({
        "ts": now,
        "subagent_type": subagent_type,
        "model": model,
        "bucket": bucket,
    })
    state["calls"] = recent
    save_state(state)

    # Count per-bucket
    counts: dict[str, int] = {}
    for c in recent:
        if c["bucket"] != "unknown":
            counts[c["bucket"]] = counts.get(c["bucket"], 0) + 1

    warnings = []
    for bucket, n in counts.items():
        if n > MAX_PER_BUCKET:
            warnings.append(
                f"[subagent-fanout] {n} parallel Agent calls in the last "
                f"{WINDOW_SECONDS}s resolve to the '{bucket}' rate-limit "
                f"bucket (max recommended: {MAX_PER_BUCKET}). The 3rd+ call "
                f"may fail with 'Provider rate limited the model request'. "
                f"Spread subagents across providers, or use "
                f"scripts/swarm/subagent_fallback.sh. "
                f"See docs/protocols/subagent-model-routing.md."
            )

    if warnings:
        # Warn to stderr but DO NOT block (exit 0).
        sys.stderr.write("\n".join(warnings) + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
