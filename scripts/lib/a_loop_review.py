"""a_loop_review.py — A-Loop v2 (Phase 9): connect the A-Loop execute
phase to the review-bus state machine.

The A-Loop never marks a task complete on its own tests alone anymore:
completion requires the task's review cycle to be READY (verdict PASS,
no open blockers, retest green at the CURRENT head, CI green). A fix
commit lands as a new head, which invalidates the previous approval and
sends the loop back around — that cycling IS the v2 improvement loop.

Pure adapter: resolves the exact git HEAD via bounded git plumbing
(`git rev-parse HEAD` — worktree/detached/packed-refs safe; WO-REVIEW-BUS
RB-1), never mutates goal/task stores, owns just one small task→cycle
map beside the review-bus state.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import review_bus as rb

_SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")


class ALoopReview:
    def __init__(self, bus: rb.ReviewBus, git_dir: Path | str | None = None):
        self.bus = bus
        self._git_dir = Path(git_dir) if git_dir else None

    # ── git head via bounded plumbing ────────────────────────────────
    def _resolve_git_dir(self) -> Path:
        """Return the real git dir behind `.git` for BOTH shapes:
        a normal checkout (directory) and a linked worktree (gitfile
        pointer whose single line is `gitdir: <path>`)."""
        git = self._git_dir
        if git is None:
            raise rb.ReviewBusError("git_dir not configured")
        if git.is_dir():
            return git
        if git.is_file():
            line = git.read_text(encoding="utf-8").strip()
            prefix = "gitdir:"
            if line.startswith(prefix):
                raw_pointer = line[len(prefix):].strip()
                if not raw_pointer:
                    raise rb.ReviewBusError(
                        f"unrecognized gitfile at {git}: empty 'gitdir:' pointer")
                target = Path(raw_pointer)
                if not target.is_absolute():
                    target = (git.parent / target).resolve(strict=False)
                return target
            raise rb.ReviewBusError(
                f"unrecognized gitfile at {git}: missing 'gitdir:' pointer")
        raise rb.ReviewBusError(f"git metadata not found at {git}")

    def head_sha(self) -> str:
        git_dir = self._resolve_git_dir()
        try:
            out = subprocess.run(
                ["git", "--git-dir", str(git_dir), "rev-parse", "HEAD"],
                capture_output=True, text=True, timeout=15)
        except (OSError, subprocess.TimeoutExpired) as e:
            raise rb.ReviewBusError(f"git rev-parse HEAD failed: {e!r}") from e
        sha = out.stdout.strip()
        if out.returncode != 0 or not _SHA_RE.fullmatch(sha):
            detail = out.stderr.strip()[:200] or "no SHA on stdout"
            raise rb.ReviewBusError(
                f"git rev-parse HEAD failed (rc={out.returncode}): {detail}")
        return sha

    # ── task ↔ cycle map ─────────────────────────────────────────────
    def _map_path(self, task_id: str) -> Path:
        return self.bus.dir / f"task-{task_id}.json"

    def open_review_for_task(self, task_id: str,
                             required_tests: list[str]) -> str:
        doc = self.bus.publish(head_sha=self.head_sha(),
                               executor=f"a-loop:{task_id}",
                               required_tests=required_tests)
        cid = f"{doc['phase']}-c{doc['cycle']}"
        self._map_path(task_id).write_text(
            json.dumps({"cycle": cid}), encoding="utf-8")
        return cid

    def task_gate(self, task_id: str) -> dict:
        """Completion gate for one loop task.

        allow_complete=True ONLY at READY. Everything else reports the
        loop-relevant state + open blockers so the executor knows what
        to fix and re-review.
        """
        path = self._map_path(task_id)
        if not path.is_file():
            return {"allow_complete": False, "status": "NO_REVIEW",
                    "blockers": [], "cycle": None}
        cid = json.loads(path.read_text(encoding="utf-8"))["cycle"]
        # Evaluate readiness HERE — the gate is the single source of truth;
        # callers must not have to remember a separate readiness() call.
        verdict = self.bus.readiness(cid)
        doc = self.bus.load(cid)
        blockers = [f["id"] for f in doc.get("findings", [])
                    if f["state"] == "open" and f["severity"] == "blocker"]
        ready = verdict["ready"]
        return {"allow_complete": ready, "status": doc.get("status"),
                "blockers": blockers, "cycle": cid,
                "reasons": verdict["reasons"]}
