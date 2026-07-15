#!/usr/bin/env python3
"""
Hook: Subagent Observatory (PostToolUse, measure-only)
------------------------------------------------------
PostToolUse hook on the `Agent` tool. After every subagent invocation,
emits a `subagent_invoke` event to the live-dashboard log
(.tmp/live-events.jsonl) capturing:

    subagent_type, model, result (pass|fail), latency_ms,
    tokens_out (estimated), tokens_in (estimated)

This is the data backbone for the "🔬 Subagents" dashboard tab and the
`scripts/swarm/subagent-stats.py` CLI. The earlier heuristic `model:` field
choice in each subagent's frontmatter becomes data-driven once enough
samples accumulate.

Design choices:
  - NEVER BLOCKS (exit 0 always). This hook only measures; it cannot
    interfere with a successful tool result.
  - Pairs with `check_subagent_fanout.py` (PreToolUse on Agent), which
    stamps a start timestamp into .tmp/subagent_fanout_state.json. This
    hook reads that stamp to compute latency_ms. If no stamp is found
    (e.g. fanout hook skipped or state pruned), latency_ms = 0 and the
    event is still emitted (best-effort).
  - Reuses model + bucket resolution from check_subagent_fanout.py to
    stay DRY (imported, not duplicated).
  - Override: HOOK_SKIP=log_subagent_result

See:
  - docs/protocols/subagent-model-routing.md  (fan-out diversity)
  - scripts/live-dashboard/event_logger.py   (metrics sink)
"""
import sys
import json
import os
import re
import time
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
REPO_ROOT = HOOKS_DIR.parent.parent
LOG_FILE = REPO_ROOT / ".tmp" / "live-events.jsonl"
STATE_FILE = REPO_ROOT / ".tmp" / "subagent_fanout_state.json"
MAX_LOG_LINES = 2000

# Reuse the fanout guard's model + bucket resolvers (single source of truth).
sys.path.insert(0, str(HOOKS_DIR))
try:
    import check_subagent_fanout as fanout  # noqa: E402
    _load_subagent_model = fanout.load_subagent_model
    _provider_for_model = fanout.provider_for_model
except Exception:
    # Defensive: if the sibling module can't be imported, degrade gracefully
    # (we still emit events, just without model/bucket fields).
    def _load_subagent_model(_t: str) -> str:
        return ""

    def _provider_for_model(_m: str) -> str:
        return "unknown"


# R4: A/B experiment tagging (best-effort, zero-overhead when no experiment
# is active). Reads .tmp/ab-experiment-state.json + agents/ab-experiments.json.
# If anything fails, the event is emitted WITHOUT ab_phase (graceful degrade).
sys.path.insert(0, str(REPO_ROOT / "scripts" / "eval"))
try:
    import ab_routing  # noqa: E402
    _AB_OK = True
except Exception:
    _AB_OK = False


def _ab_tag(subagent_type: str) -> dict | None:
    """Return {ab_phase, ab_model} if an active A/B experiment targets this
    subagent, else None. Best-effort — never raises.
    """
    if not _AB_OK:
        return None
    try:
        experiments = ab_routing.load_experiments()
        if not experiments:
            return None
        state = ab_routing.load_state()
        return ab_routing.tag_for_event(subagent_type, experiments, state)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Error detection
# ---------------------------------------------------------------------------
_ERROR_KEYWORDS = (
    "rate limit",
    "rate-limit",
    "rate limited",
    "provider rate",
    "429",
    "quota exceeded",
    "internal server error",
    "service unavailable",
    "timeout",
    "timed out",
    "connection reset",
    "unauthorized",
    "invalid api key",
    "overloaded",
    "error:",        # explicit error-labeled failure (avoids "no errors found")
    "failed:",
    "exception:",
    "traceback",
)


def is_error_response(resp) -> bool:
    """Classify a tool_response as success or failure.

    Handles three shapes:
      - dict with `iserror: true` (Claude Code error envelope)
      - dict with `content[].text` containing error keywords
      - bare string containing error keywords
    """
    if resp is None:
        return False
    if isinstance(resp, dict):
        if resp.get("iserror"):
            return True
        # Walk content blocks for error text.
        content = resp.get("content")
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    txt = str(block.get("text", "")).lower()
                    if any(k in txt for k in _ERROR_KEYWORDS):
                        return True
        # Also check a top-level error string.
        err = str(resp.get("error", "")).lower()
        if err and any(k in err for k in _ERROR_KEYWORDS):
            return True
        return False
    if isinstance(resp, str):
        r = resp.lower()
        return any(k in r for k in _ERROR_KEYWORDS)
    return False


# ---------------------------------------------------------------------------
# Token estimation (rough — 4 chars ≈ 1 token for Latin/English)
# ---------------------------------------------------------------------------
def estimate_tokens(text) -> int:
    """Rough token count from text length. Floor at 1 (never 0)."""
    if not text:
        return 1
    if not isinstance(text, str):
        try:
            text = json.dumps(text, ensure_ascii=False)
        except Exception:
            text = str(text)
    # Thai/CJK chars are ~1 token each, Latin ~4 chars/token — average ~3.
    return max(1, len(text) // 3)


def _response_text(resp) -> str:
    """Extract the textual payload from a tool_response for token counting."""
    if resp is None:
        return ""
    if isinstance(resp, str):
        return resp
    if isinstance(resp, dict):
        content = resp.get("content")
        if isinstance(content, list):
            parts = []
            for block in content:
                if isinstance(block, dict) and "text" in block:
                    parts.append(str(block["text"]))
            return "\n".join(parts)
        if "text" in resp:
            return str(resp["text"])
    return ""


def extract_subagent_type(tool_input: dict) -> str:
    """Pull subagent_type (or subagentType) from the Agent tool input."""
    if not isinstance(tool_input, dict):
        return ""
    return tool_input.get("subagent_type") or tool_input.get("subagentType") or ""


# ---------------------------------------------------------------------------
# Latency via the PreToolUse fanout state
# ---------------------------------------------------------------------------
def _pop_start_ts(subagent_type: str) -> float:
    """Find + remove the earliest matching start stamp from the fanout state.

    Returns 0.0 if none found (best-effort latency).
    """
    try:
        if not STATE_FILE.exists():
            return 0.0
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return 0.0
    calls = state.get("calls", [])
    for i, c in enumerate(calls):
        if c.get("subagent_type") == subagent_type and "ts" in c:
            start = c["ts"]
            del calls[i]
            state["calls"] = calls
            try:
                STATE_FILE.write_text(json.dumps(state), encoding="utf-8")
            except Exception:
                pass
            return start
    return 0.0


# ---------------------------------------------------------------------------
# Event emission
# ---------------------------------------------------------------------------
def emit_event(**kwargs) -> None:
    """Append one JSON line to the live-events log (best-effort, never raises)."""
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        entry = {"ts": round(time.time(), 3), "type": "subagent_invoke",
                 **{k: v for k, v in kwargs.items() if v is not None}}
        line = json.dumps(entry, ensure_ascii=False) + "\n"
        # Cap the file size: keep last MAX_LOG_LINES lines.
        _append_capped(LOG_FILE, line, MAX_LOG_LINES)
    except Exception:
        pass


def _append_capped(path: Path, line: str, cap: int) -> None:
    """Append a line, trimming the head if the file exceeds `cap` lines."""
    mode = "a" if path.exists() else "w"
    with open(path, mode, encoding="utf-8") as f:
        f.write(line)
    if cap > 0 and path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                all_lines = f.readlines()
            if len(all_lines) > cap:
                with open(path, "w", encoding="utf-8") as f:
                    f.writelines(all_lines[-cap:])
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    if os.environ.get("HOOK_SKIP") == "log_subagent_result":
        return 0

    try:
        input_data = json.load(sys.stdin)
    except Exception:
        return 0

    tool_name = input_data.get("tool_name", "")
    if tool_name != "Agent":
        return 0  # only the Agent tool is observable here

    tool_input = input_data.get("tool_input", {})
    subagent_type = extract_subagent_type(tool_input)
    if not subagent_type:
        return 0

    resp = input_data.get("tool_response", input_data.get("tool_result"))
    result = "fail" if is_error_response(resp) else "pass"

    model = _load_subagent_model(subagent_type)
    bucket = _provider_for_model(model)

    start_ts = _pop_start_ts(subagent_type)
    latency_ms = int(round((time.time() - start_ts) * 1000)) if start_ts else 0

    text = _response_text(resp)
    tokens_out = estimate_tokens(text)
    # tokens_in: estimate from the prompt if present, else 0 (unknown).
    prompt = tool_input.get("prompt") or tool_input.get("description") or ""
    tokens_in = estimate_tokens(prompt) if prompt else 0

    emit_event(
        subagent_type=subagent_type,
        model=model or None,
        bucket=bucket if bucket != "unknown" else None,
        result=result,
        latency_ms=latency_ms,
        tokens_in=tokens_in or None,
        tokens_out=tokens_out,
        **(_ab_tag(subagent_type) or {}),  # R4: ab_phase + ab_model if active
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
