"""Unified read-only status: COLLAB claims + git branches + hard-gate count.

The conductor never mutates anything through this module — status is a
snapshot others (gate/CLI) reason over.
"""
from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path

SCHEMA = "awiki-conductor/v1"


def parse_claims(collab: Path) -> list[dict]:
    """Parse the in-progress claim table from COLLAB.md (tolerant, read-only)."""
    if not collab.is_file():
        return []
    claims: list[dict] = []
    in_table = False
    for line in collab.read_text(encoding="utf-8").splitlines():
        # anchor ONLY on the claims header — COLLAB has other tables (Lanes)
        if line.startswith("|") and "chunk/wo" in line.lower():
            in_table = True
            continue
        if in_table and line.startswith("|") and "chunk/wo" not in line.lower()                 and set(line.replace("|", "").replace("-", "").strip()) <= set(": "):
            continue  # separator row of the claims table
        if not in_table:
            continue
        if not line.strip():
            # Formatting-only blank lines are tolerated inside the claims
            # section; a non-table prose line still terminates the section.
            continue
        if not line.strip().startswith("|"):
            in_table = False
            continue
        if line.lower().startswith("| lane"):
            in_table = False  # a different table starts
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4 or cells[0].startswith("_"):
            continue
        claims.append({
            "chunk": cells[0],
            "agent": cells[1] if len(cells) > 1 else "",
            "claimed": cells[2] if len(cells) > 2 else "",
            "scope": cells[3] if len(cells) > 3 else "",
            "branch": cells[4] if len(cells) > 4 else "",
        })
    return claims


class ClaimLookupError(ValueError):
    """Canonical durable claim cannot be resolved exactly and safely."""


def parse_claims_strict(collab: Path) -> list[dict]:
    """Read the claims region, rejecting every row/header width mismatch.

    UTF-8 BOM and CRLF checkouts are supported explicitly. Unlike parse_claims,
    unreadable files and malformed rows raise ClaimLookupError, even when the
    offending row is unrelated to the requested task or is a placeholder.
    """
    try:
        text = collab.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        raise ClaimLookupError(f"CLAIM_TABLE_UNAVAILABLE: {exc}") from None
    claims: list[dict] = []
    width = 0
    lines = text.splitlines()
    for number, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
        if not line.startswith("|"):
            width = 0
            continue
        # Remove only the outer delimiters; preserve empty edge cells.
        body = line[1:-1] if line.endswith("|") else line[1:]
        cells = [cell.strip() for cell in body.split("|")]
        if cells[0].lower() == "chunk/wo":
            if len(cells) < 4 or (width and len(cells) != width):
                raise ClaimLookupError(f"CLAIM_TABLE_MALFORMED: header at line {number}")
            width = len(cells)
            continue
        if cells[0].lower() == "lane":
            # A different table needs a matching separator, not just a Lane cell.
            separator = lines[number].strip() if number < len(lines) else ""
            if separator.startswith("|") and separator.endswith("|"):
                separator_cells = [cell.strip() for cell in separator[1:-1].split("|")]
                if len(separator_cells) == len(cells) and all(
                        re.fullmatch(r":?-+:?", cell) for cell in separator_cells):
                    width = 0
                    continue
        if not width:
            continue
        if len(cells) != width:
            raise ClaimLookupError(
                f"CLAIM_TABLE_MALFORMED: line {number}, expected {width} cells, got {len(cells)}")
        if all(re.fullmatch(r":?-+:?", cell) for cell in cells):
            continue
        if cells[0].startswith("_"):
            continue
        claims.append({
            "chunk": cells[0], "agent": cells[1], "claimed": cells[2],
            "scope": cells[3], "branch": cells[4] if width > 4 else "",
        })
    return claims


def _scope_items(raw: str) -> list[str]:
    return [part.strip() for part in re.split(r"[;,]", raw) if part.strip()]


def _git(repo_root: Path, *args: str) -> str:
    try:
        proc = subprocess.run(
            ["git", *args], cwd=str(repo_root), capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=15,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise ClaimLookupError(f"GIT_UNAVAILABLE: {exc}") from None
    if proc.returncode != 0:
        raise ClaimLookupError(
            f"GIT_UNAVAILABLE: {(proc.stderr or proc.stdout).strip()[:160]}")
    return proc.stdout.strip()


def require_complete_claim_history(repo_root: Path | str) -> None:
    """Fail closed when Git history is intentionally incomplete.

    Durable claim generation is derived from COLLAB history. A shallow clone
    cannot prove prior generations, so it must never mint a canonical
    generation/claim id or persist a new durable claim from partial history.
    """
    root = Path(repo_root)
    try:
        shallow = _git(root, "rev-parse", "--is-shallow-repository").strip().lower()
    except ClaimLookupError:
        # Preserve legacy behavior for non-Git/test roots; callers that require
        # Git identity still fail at their existing branch/history checks.
        return
    if shallow == "true":
        raise ClaimLookupError(
            "GIT_HISTORY_SHALLOW: fetch full history before resolving durable claim generation"
        )


def claim_generation(repo_root: Path, task_id: str) -> int:
    """Return the current durable COLLAB generation for one exact task id.

    Every committed claim-row addition/replacement advances generation. The
    current uncommitted claim-row addition/replacement also counts so a newly
    reacquired task rotates generation *before* the mandatory claim commit.
    """
    require_complete_claim_history(repo_root)
    escaped = re.escape(task_id.strip())
    if not escaped:
        raise ClaimLookupError("TASK_ID_REQUIRED")
    row = re.compile(rf"^\+\|\s*{escaped}\s*\|", re.MULTILINE)

    committed = 0
    try:
        patch = _git(repo_root, "log", "--format=", "--patch", "--", "COLLAB.md")
        committed = len(row.findall(patch))
    except ClaimLookupError:
        pass

    pending = 0
    try:
        # HEAD comparison includes both staged and unstaged changes.
        working = _git(repo_root, "diff", "HEAD", "--", "COLLAB.md")
        pending = len(row.findall(working))
    except ClaimLookupError:
        pass

    return max(1, committed + pending)


def claim_generation_strict(repo_root: Path, task_id: str) -> int:
    """Derive generation only after successful full-history, log and diff reads.

    Every Git failure propagates as ClaimLookupError (GIT_UNAVAILABLE); shallow
    history raises GIT_HISTORY_SHALLOW. No legacy best-effort fallback is used.
    """
    escaped = re.escape(task_id.strip())
    if not escaped:
        raise ClaimLookupError("TASK_ID_REQUIRED")
    shallow = _git(repo_root, "rev-parse", "--is-shallow-repository").lower()
    if shallow == "true":
        raise ClaimLookupError(
            "GIT_HISTORY_SHALLOW: fetch full history before resolving durable claim generation")
    if shallow != "false":
        raise ClaimLookupError("GIT_UNAVAILABLE: invalid shallow-history response")
    row = re.compile(rf"^\+\|\s*{escaped}\s*\|", re.MULTILINE)
    patch = _git(repo_root, "log", "--format=", "--patch", "--", "COLLAB.md")
    working = _git(repo_root, "diff", "HEAD", "--", "COLLAB.md")
    return max(1, len(row.findall(patch)) + len(row.findall(working)))


def _repo_identity(repo_root: Path) -> str:
    try:
        remote = _git(repo_root, "remote", "get-url", "origin")
    except ClaimLookupError:
        return repo_root.name
    match = re.search(r"github\.com[/:]([^/]+/[^/]+?)(?:\.git)?$", remote)
    return match.group(1) if match else repo_root.name


def _validate_branch_name(repo_root: Path, branch: str) -> str:
    branch = (branch or "").strip()
    if not branch or branch.startswith("<"):
        raise ClaimLookupError("BRANCH_UNBOUND")
    try:
        _git(repo_root, "check-ref-format", "--branch", branch)
    except ClaimLookupError:
        raise ClaimLookupError(f"BRANCH_INVALID: {branch}") from None
    return branch


def _branch_head(repo_root: Path, branch: str) -> str:
    branch = _validate_branch_name(repo_root, branch)
    # Resolve only literal branch refs. `show-ref --verify` does not interpret
    # reflog/revision expressions, so values like main@{1} cannot masquerade
    # as durable branch identity.
    for ref in (f"refs/remotes/origin/{branch}", f"refs/heads/{branch}"):
        try:
            sha = _git(repo_root, "show-ref", "--verify", "--hash", ref)
        except ClaimLookupError:
            continue
        if not re.fullmatch(r"[0-9a-f]{40}", sha):
            continue
        try:
            commit = _git(repo_root, "rev-parse", "--verify", f"{sha}^{{commit}}")
        except ClaimLookupError:
            continue
        if re.fullmatch(r"[0-9a-f]{40}", commit):
            return commit
    raise ClaimLookupError(f"BRANCH_HEAD_UNRESOLVED: {branch}")


def _public_scope_items(raw: str) -> list[str]:
    items = _scope_items(raw)
    if not items:
        raise ClaimLookupError("SCOPE_UNSAFE: empty scope")
    for item in items:
        normalized = item.replace("\\", "/")
        if ("|" in item or any(ch in item for ch in "\r\n") or
                any(ord(ch) < 32 for ch in item) or
                item.startswith(("/", "\\", "~")) or
                re.match(r"^[A-Za-z]:[\\/]", item) or
                any(part == ".." for part in normalized.split("/"))):
            raise ClaimLookupError(f"SCOPE_UNSAFE: {item!r}")
    return items


def read_canonical_claim(repo_root: Path | str, task_id: str) -> dict:
    """Read one exact canonical repo claim from COLLAB/Git.

    No fuzzy task matching and no machine-local worktree path is emitted.
    The consuming runtime must independently verify its local worktree binding.
    """
    return _read_canonical_claim(repo_root, task_id, strict=False)


def read_canonical_claim_strict(repo_root: Path | str, task_id: str) -> dict:
    """Opt-in fail-closed canonical reader; legacy consumers are unchanged.

    Raises ClaimLookupError on malformed tables, ambiguity or unavailable Git
    history, in addition to the existing owner/branch/scope validation errors.
    COLLAB.md is decoded as UTF-8 with optional BOM and CRLF tolerance.
    """
    return _read_canonical_claim(repo_root, task_id, strict=True)


def _read_canonical_claim(repo_root: Path | str, task_id: str, *, strict: bool) -> dict:
    root = Path(repo_root)
    task = (task_id or "").strip()
    if not task:
        raise ClaimLookupError("TASK_ID_REQUIRED")
    parser = parse_claims_strict if strict else parse_claims
    matches = [c for c in parser(root / "COLLAB.md")
               if c["chunk"].strip() == task]
    if not matches:
        raise ClaimLookupError(f"CLAIM_NOT_FOUND: {task}")
    if len(matches) != 1:
        raise ClaimLookupError(f"CLAIM_AMBIGUOUS: {task}")
    claim = matches[0]
    owner = claim["agent"].strip()
    if not owner or owner.lower() == "unknown":
        raise ClaimLookupError(f"OWNER_UNBOUND: {task}")
    generation = (claim_generation_strict(root, task) if strict
                  else claim_generation(root, task))
    head = _branch_head(root, claim["branch"])
    scope = _public_scope_items(claim["scope"])
    digest_input = "\0".join((
        _repo_identity(root), task, str(generation), owner,
        claim["claimed"], claim["branch"], ";".join(scope),
    ))
    claim_id = "awiki-claim-" + hashlib.sha256(
        digest_input.encode("utf-8")).hexdigest()[:20]
    return {
        "schema": "awiki-claim-reader/v1",
        "authority_source": "COLLAB.md+Git",
        "repository": _repo_identity(root),
        "task_id": task,
        "claim_id": claim_id,
        "generation": generation,
        "agent": owner,
        "claimed_at": claim["claimed"],
        "scope": scope,
        "branch": claim["branch"],
        "branch_head_sha": head,
        "worktree_binding": "CONSUMER_VERIFY_REQUIRED",
    }


def list_branches(repo_root: Path) -> list[str]:
    try:
        out = subprocess.run(
            ["git", "branch", "--format=%(refname:short)"],
            capture_output=True, text=True, timeout=15, cwd=str(repo_root),
        )
    except (OSError, subprocess.SubprocessError):
        return []
    return [b for b in out.stdout.split() if b]


def count_hard_gates(repo_root: Path) -> int:
    sys_path = repo_root / "scripts" / "hooks"
    if not sys_path.is_dir():
        return 0
    import sys
    inserted = str(sys_path)
    if inserted not in sys.path:
        sys.path.insert(0, inserted)
    try:
        import registry  # type: ignore
    except Exception:
        return 0
    return sum(1 for e in registry.HOOK_REGISTRY.values()
               if e.get("classification") == "hard")


def conductor_status(repo_root: Path | None = None) -> dict:
    root = Path(repo_root) if repo_root else Path.cwd()
    return {
        "schema": SCHEMA,
        "repo": root.name,
        "claims": parse_claims(root / "COLLAB.md"),
        "branches": list_branches(root),
        "gate_tools": count_hard_gates(root),
    }
