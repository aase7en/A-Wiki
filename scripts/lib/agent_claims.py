"""agent_claims.py — cross-agent work claims (A-Wiki mandatory coordination).

The problem this exists for
---------------------------
2026-07-27: two agents (Claude and ZCode) independently built the same intent
router and the same phase state machine, in the same repo, on the same branch,
during the same hours. Neither noticed until both had landed on main.

A-Wiki already had every primitive needed to prevent it — TaskBoard with TTL
leases, Blackboard with @mentions, a shared .tmp/ that every agent on the machine
reads. What it lacked was a GATE. Nothing forced an agent to say what it was
about to build, so nothing could tell it someone else already was.

check_cost_tier forces you to declare cost. check_skill_registry forces you to
register a skill. This forces you to declare WORK.

Design
------
* One JSON store at .tmp/agent-claims.json — shared by every agent on the machine.
* A claim is (agent, scope globs, goal, phase) with a TTL lease.
* Leases self-reap on read, so a crashed agent cannot lock the repo. No daemon.
* Atomic writes (temp + os.replace) — adopted from ZCode's a_flow_state.py, which
  got this right where the first version of my own focus store did not. A
  half-written store is indistinguishable from "no claims", which would silently
  disable the gate for everyone.
* Fails open everywhere: a corrupt or unreadable store must never wedge the repo.
"""
from __future__ import annotations

import fnmatch
import json
import os
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]


def _default_store() -> Path:
    """Env override exists so a hook SUBPROCESS can be pointed at a test store.
    Without it, tests that spawn the hook would mutate the machine's real claims."""
    env = os.environ.get("AWIKI_CLAIMS_STORE", "").strip()
    return Path(env) if env else REPO_ROOT / ".tmp" / "agent-claims.json"


_DEFAULT_STORE = _default_store()
_STORE: Path = _DEFAULT_STORE

#: Same spine as skills_registry.routing.A_PHASE_CHAIN. Duplicated as a literal
#: rather than imported because hooks import this on every Edit and must stay
#: cheap; a drift test in tests/test_agent_claims_hook.py keeps them in sync.
PHASES = ("ask", "design", "plan", "implement", "review", "debug", "test")

DEFAULT_LEASE_SECONDS = 3600  # 1h; heartbeat extends it


def set_store(path: Path | str | None) -> None:
    """Point the store elsewhere (tests). None restores the default."""
    global _STORE
    _STORE = Path(path) if path is not None else _DEFAULT_STORE


def store_path() -> Path:
    return _STORE


# --------------------------------------------------------------------------- IO

def _read() -> dict[str, Any]:
    try:
        data = json.loads(_STORE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"claims": []}
    if not isinstance(data, dict) or not isinstance(data.get("claims"), list):
        return {"claims": []}
    return data


def _write(data: dict[str, Any]) -> None:
    """Atomic: write a temp file in the same dir, then os.replace over the target."""
    try:
        _STORE.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=str(_STORE.parent), prefix=".agent-claims-", suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(tmp, _STORE)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
    except OSError:
        pass  # fail open — never block work because the store is unwritable


def _prune(data: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    now = time.time()
    kept = [c for c in data["claims"] if float(c.get("lease_until", 0)) > now]
    changed = len(kept) != len(data["claims"])
    data["claims"] = kept
    return data, changed


# ------------------------------------------------------------------- public API

def live() -> list[dict[str, Any]]:
    """All unexpired claims. Reaps expired ones as a side effect."""
    data, changed = _prune(_read())
    if changed:
        _write(data)
    return list(data["claims"])


def get(claim_id: str) -> dict[str, Any] | None:
    for c in live():
        if c["id"] == claim_id:
            return c
    return None


def acquire(*, agent: str, scope: list[str], goal: str,
            phase: str = "ask", session_id: str = "",
            lease_seconds: int = DEFAULT_LEASE_SECONDS) -> dict[str, Any]:
    """Register intent to work on `scope`. Returns the claim."""
    agent = (agent or "").strip()
    goal = (goal or "").strip()
    scope = [s.strip() for s in (scope or []) if s and s.strip()]
    if not agent:
        raise ValueError("claim requires an agent name")
    if not scope:
        raise ValueError("claim requires at least one scope glob")
    if not goal:
        raise ValueError("claim requires a goal — 'what done looks like', one line")
    if phase not in PHASES:
        raise ValueError(f"unknown phase {phase!r}; valid: {', '.join(PHASES)}")

    now = time.time()
    claim = {
        "id": uuid.uuid4().hex[:12],
        "agent": agent,
        "session_id": session_id,
        "scope": scope,
        "goal": goal,
        "phase": phase,
        "started_ts": int(now),
        "heartbeat_ts": int(now),
        "lease_until": now + lease_seconds,
    }
    data, _ = _prune(_read())
    data["claims"].append(claim)
    _write(data)
    return claim


def release(claim_id: str) -> bool:
    data, _ = _prune(_read())
    before = len(data["claims"])
    data["claims"] = [c for c in data["claims"] if c["id"] != claim_id]
    if len(data["claims"]) == before:
        return False
    _write(data)
    return True


def release_session(session_id: str) -> int:
    """Drop every claim held by a session (Stop hook)."""
    data, _ = _prune(_read())
    before = len(data["claims"])
    data["claims"] = [c for c in data["claims"] if c.get("session_id") != session_id]
    n = before - len(data["claims"])
    if n:
        _write(data)
    return n


def advance(claim_id: str, phase: str) -> dict[str, Any]:
    if phase not in PHASES:
        raise ValueError(f"unknown phase {phase!r}; valid: {', '.join(PHASES)}")
    data, _ = _prune(_read())
    for c in data["claims"]:
        if c["id"] == claim_id:
            c["phase"] = phase
            c["heartbeat_ts"] = int(time.time())
            c["lease_until"] = time.time() + DEFAULT_LEASE_SECONDS
            _write(data)
            return c
    raise ValueError(f"no live claim {claim_id!r}")


def heartbeat(claim_id: str, lease_seconds: int = DEFAULT_LEASE_SECONDS) -> dict[str, Any]:
    data, _ = _prune(_read())
    for c in data["claims"]:
        if c["id"] == claim_id:
            c["heartbeat_ts"] = int(time.time())
            c["lease_until"] = time.time() + lease_seconds
            _write(data)
            return c
    raise ValueError(f"no live claim {claim_id!r}")


def _rel(file_path: str) -> str:
    """Normalise a hook-supplied path to a repo-relative POSIX path."""
    p = (file_path or "").replace("\\", "/")
    try:
        cand = Path(file_path)
        if cand.is_absolute():
            p = str(cand.resolve()).replace("\\", "/")
            root = str(REPO_ROOT.resolve()).replace("\\", "/")
            if p.lower().startswith(root.lower() + "/"):
                p = p[len(root) + 1:]
    except (OSError, ValueError):
        pass
    return p.lstrip("./") if p.startswith("./") else p


def _matches(path: str, glob: str) -> bool:
    g = glob.replace("\\", "/")
    if fnmatch.fnmatch(path, g):
        return True
    # "skills/awiki/**" should cover skills/awiki/x/y.md; fnmatch's * spans '/'
    # already, but a trailing /** must also match the dir itself.
    if g.endswith("/**") and (path == g[:-3] or path.startswith(g[:-2])):
        return True
    return False


def collision(file_path: str, agent: str) -> dict[str, Any] | None:
    """Return ANOTHER agent's live claim covering `file_path`, else None."""
    path = _rel(file_path)
    if not path:
        return None
    for c in live():
        if c.get("agent") == agent:
            continue
        for g in c.get("scope") or []:
            if _matches(path, g):
                return c
    return None


def describe(claims: list[dict[str, Any]] | None = None) -> str:
    """One-line-per-claim human summary (SessionStart / claim_list)."""
    claims = live() if claims is None else claims
    if not claims:
        return "(no active claims)"
    now = time.time()
    out = []
    for c in claims:
        mins = max(0, int((c["lease_until"] - now) / 60))
        out.append(
            f"{c['agent']:<8} [{c['phase']:<9}] {c['goal'][:56]}"
            f"  scope={', '.join(c['scope'][:2])}  ({mins}m left)"
        )
    return "\n".join(out)


# ------------------------------------------------------------------ test helper

def _force_lease(claim_id: str, lease_until: float) -> None:
    """Test-only: set a lease directly so expiry can be exercised."""
    data = _read()
    for c in data["claims"]:
        if c["id"] == claim_id:
            c["lease_until"] = lease_until
    _write(data)
