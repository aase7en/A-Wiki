#!/usr/bin/env python3
"""check-stale-specs.py — plans/ADRs own exact repo-relative paths via `scope:`.

A non-frozen spec is current only when full Git history proves that no scoped
path changed in commits reachable from HEAD but not from the spec's own last
commit. History is graph-ordered, never wall-clock ordered. Shallow, missing,
or invalid history fails closed so CI cannot report a false green.

Usage: python scripts/check-stale-specs.py [--root DIR]
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

_SPEC_GLOBS = ("docs/plans/*.md", "decisions/*.md")
FM_RE = re.compile(r"^---\n(.*?)\n---", re.S)
_DRIVE_RE = re.compile(r"^[A-Za-z]:")


class HistoryError(RuntimeError):
    """Git history is unavailable or incomplete; stale-spec must fail closed."""


def _git(root: Path, *args: str) -> str:
    try:
        proc = subprocess.run(
            ["git", *args], cwd=root, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise HistoryError(f"git {' '.join(args[:2])} failed: {exc}") from exc
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "git command failed").strip().splitlines()
        raise HistoryError(detail[-1][:240] if detail else "git command failed")
    return proc.stdout.strip()


def _require_full_history(root: Path) -> None:
    shallow = _git(root, "rev-parse", "--is-shallow-repository").strip().lower()
    if shallow == "true":
        raise HistoryError("shallow Git history; fetch full history before stale-spec verification")
    if shallow != "false":
        raise HistoryError(f"could not determine shallow-repository state: {shallow!r}")
    if not _git(root, "rev-parse", "--verify", "HEAD^{commit}"):
        raise HistoryError("HEAD commit is unavailable")


def _normalize_scope_path(raw: str) -> str:
    value = raw.strip().replace("\\", "/")
    if not value:
        raise ValueError("scope path is empty")
    if value.startswith("/") or _DRIVE_RE.match(value):
        raise ValueError("scope path must be repo-relative")
    parts: list[str] = []
    for part in value.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            raise ValueError("scope path may not contain '..'")
        if any(ord(ch) < 32 for ch in part):
            raise ValueError("scope path contains a control character")
        parts.append(part)
    if not parts:
        raise ValueError("scope path is empty after normalization")
    return "/".join(parts)


def _last_commit_oid(root: Path, rel: str) -> str:
    oid = _git(root, "--literal-pathspecs", "log", "-1", "--format=%H", "HEAD", "--", rel)
    if not oid:
        raise HistoryError(f"no committed history for {rel}")
    return oid


def _changed_after_spec(root: Path, spec_oid: str, rel: str) -> bool:
    oid = _git(
        root, "--literal-pathspecs", "log", "-1", "--format=%H",
        f"{spec_oid}..HEAD", "--", rel,
    )
    return bool(oid)


def _parse_spec(text: str) -> tuple[dict, list[str]]:
    m = FM_RE.match(text)
    if not m:
        return {}, []
    frozen = False
    scope: list[str] = []
    in_scope = False
    for line in m.group(1).splitlines():
        if re.match(r"^scope:\s*$", line):
            in_scope = True; continue
        if in_scope:
            mm = re.match(r"^\s+-\s*(\S+)\s*$", line)
            if mm:
                scope.append(mm.group(1)); continue
            if line and not line.startswith((" ", "\t", "-")):
                in_scope = False
        if re.match(r"^plan-frozen:\s*true\s*$", line.strip()):
            frozen = True
    return ({"frozen": frozen}, scope)


def check_repo(root: Path) -> list[str]:
    root = Path(root).resolve()
    problems: list[str] = []
    try:
        _require_full_history(root)
    except HistoryError as exc:
        return [f"Git history unavailable: {exc}"]

    for pattern in _SPEC_GLOBS:
        for spec in root.glob(pattern):
            if not spec.is_file():
                continue
            meta, scope = _parse_spec(spec.read_text(encoding="utf-8"))
            if not scope or meta.get("frozen"):
                continue
            spec_rel = spec.relative_to(root).as_posix()
            try:
                spec_oid = _last_commit_oid(root, spec_rel)
            except HistoryError as exc:
                problems.append(f"{spec_rel} history unavailable: {exc}")
                continue

            for raw_rel in scope:
                try:
                    rel = _normalize_scope_path(raw_rel)
                except ValueError as exc:
                    problems.append(f"{spec_rel} has invalid scope path {raw_rel!r}: {exc}")
                    continue
                try:
                    _last_commit_oid(root, rel)  # distinguish unchanged history from no history
                    changed = _changed_after_spec(root, spec_oid, rel)
                except HistoryError as exc:
                    problems.append(f"{spec_rel} scoped file {rel} history unavailable: {exc}")
                    continue
                if changed:
                    problems.append(
                        f"{spec_rel} is stale: scoped file {rel} changed after spec commit "
                        f"{spec_oid[:12]} (update the spec, or mark plan-frozen: true)"
                    )
    return problems


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    args = ap.parse_args(argv)
    problems = check_repo(Path(args.root))
    for problem in problems:
        print(f"[FAIL] {problem}")
    if problems:
        return 1
    print("[OK] no stale specs (full Git history covers exact scoped paths)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
