"""Kilo runtime surface — keeps .kilo/kilo.jsonc skills.paths registry-owned.

WO-AWIKI-KILOSURF-08. The generated/kilo.skills-paths.json snippet was
correct but nothing merged it into the runtime file Kilo actually reads,
so .kilo/kilo.jsonc carried a stale hand-frozen list (Iron Law #10 drift).

Design (terra r1-r3):
- ``render`` is PURE (safe for --check) and byte-preserving: it reads BYTES
  (no universal-newline translation — CRLF outside the array survives) and
  replaces ONLY the array that is the value of the TOP-LEVEL ``skills``
  object's ``paths`` key, located by a real JSON depth-scanner — never by
  indentation heuristics. A nested ``"skills"`` object anywhere in the file
  cannot be mistaken for the top-level one, and every unexpected shape
  fails loud instead of guessing.
- ``write_atomic`` is the regen-side writer: stats the file BEFORE render
  reads it, re-stats after (refusing to overwrite a file that changed
  mid-render), writes to a temp file, restores the original file mode,
  fsyncs and os.replace()s into place, with a second re-stat immediately
  before the swap. Concurrency: this is BEST-EFFORT single-writer
  protection, not a lock — the guards compare mtime+size only, so an edit
  that preserves both, or one landing between the last stat and the
  replace, can still be lost. Real cross-process serialization would need
  a lock file; that is deliberately out of scope for a regen command.
  A crash can never truncate the runtime config.

Fails loud when the runtime file is missing or its shape is unexpected:
it is a tracked repo file, so absence means a broken checkout.
"""
from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path

from .. import Registry
from .gen_kilo import _category_dirs

REPO_ROOT = Path(__file__).resolve().parents[3]
filename = ".kilo/kilo.jsonc"  # repo-root-relative (ROOT_SURFACES)

_WS = b" \t\r\n"


def _skip_ws(raw: bytes, i: int) -> int:
    while i < len(raw) and raw[i:i + 1] in _WS:
        i += 1
    return i


_SIMPLE_ESCAPES = {
    b'"': b'"', b"\\": b"\\", b"/": b"/", b"b": b"\b",
    b"f": b"\f", b"n": b"\n", b"r": b"\r", b"t": b"\t",
}


def _read_string_at(raw: bytes, i: int) -> tuple[bytes, int]:
    r"""raw[i] is the opening quote; returns (decoded_value, end_index)
    where end_index points just past the closing quote. Escapes are
    decoded EXACTLY like a JSON parser (terra r5 F1: without \uXXXX
    decoding, "sk\\u0069lls" would hide from key comparison while
    json.loads treats it as "skills")."""
    assert raw[i:i + 1] == b'"'
    j = i + 1
    buf = bytearray()
    n = len(raw)
    while j < n:
        c = raw[j:j + 1]
        if c == b"\\":
            nxt = raw[j + 1:j + 2]
            if nxt == b"u":
                cp = int(raw[j + 2:j + 6].decode("ascii"), 16)
                step = 6
                if 0xD800 <= cp <= 0xDBFF and raw[j + 6:j + 8] == b"\\u":
                    lo = int(raw[j + 8:j + 12].decode("ascii"), 16)
                    if 0xDC00 <= lo <= 0xDFFF:
                        cp = 0x10000 + ((cp - 0xD800) << 10) + (lo - 0xDC00)
                        step = 12
                buf += chr(cp).encode("utf-8")
                j += step
                continue
            buf += _SIMPLE_ESCAPES.get(nxt, nxt)
            j += 2
            continue
        if c == b'"':
            return bytes(buf), j + 1
        buf += c
        j += 1
    raise RuntimeError(f"{filename}: unterminated JSON string")


def _locate_top_level_paths_span(raw: bytes) -> tuple[int, int]:
    """Byte span (start, end) of the ``[ ... ]`` array that is the value of
    the TOP-LEVEL ``skills`` object's ``paths`` key. Depth is tracked across
    {} and [] with full string/escape awareness, so a nested ``"skills"``
    key inside any deeper object or array can never match."""
    n = len(raw)
    i = 0
    depth = 0
    seen_skills = False
    while i < n:
        c = raw[i:i + 1]
        if c == b'"':
            value, end = _read_string_at(raw, i)
            k = _skip_ws(raw, end)
            if depth == 1 and value == b"skills" and raw[k:k + 1] == b":":
                if seen_skills:
                    raise RuntimeError(
                        f"{filename}: duplicate top-level skills key — "
                        "json.loads would keep the LAST one while this "
                        "scanner anchors the FIRST; refusing to guess")
                seen_skills = True
                span = _locate_paths_inside_object(raw, k)
                # keep scanning to the END of the document: a SECOND
                # top-level skills key appearing later is the same hazard
                i = k
                continue
            i = end
            continue
        if c in (b"{", b"["):
            depth += 1
        elif c in (b"}", b"]"):
            depth -= 1
        i += 1
    if not seen_skills:
        raise RuntimeError(
            f"{filename}: top-level skills key not found — refusing blind "
            "rewrite")
    return span


def _locate_paths_inside_object(raw: bytes, colon: int) -> tuple[int, int]:
    k = _skip_ws(raw, colon + 1)
    if raw[k:k + 1] != b"{":
        raise RuntimeError(
            f"{filename}: top-level skills value is not an object")
    # scan inside the object (depth relative to its opening brace)
    n = len(raw)
    i = k
    depth = 0
    started = False
    while i < n:
        c = raw[i:i + 1]
        if c == b'"':
            value, end = _read_string_at(raw, i)
            j = _skip_ws(raw, end)
            if (started and depth == 0 and value == b"paths"
                    and raw[j:j + 1] == b":"):
                a = _skip_ws(raw, j + 1)
                if raw[a:a + 1] != b"[":
                    raise RuntimeError(
                        f"{filename}: skills.paths value is not an array")
                b = a + 1
                d = 1  # the opening '[' at raw[a] is already consumed
                in_str = esc = False
                while b < n:
                    ch = raw[b:b + 1]
                    if in_str:
                        if esc:
                            esc = False
                        elif ch == b"\\":
                            esc = True
                        elif ch == b'"':
                            in_str = False
                    elif ch == b'"':
                        in_str = True
                    elif ch == b"[":
                        d += 1
                    elif ch == b"]":
                        d -= 1
                        if d == 0:
                            span = (a, b + 1)
                            # continue scanning the REST of the skills
                            # object for a duplicate paths key
                            b += 1
                            d2 = 0
                            while b < n:
                                ch2 = raw[b:b + 1]
                                if ch2 == b'"':
                                    v2, e2 = _read_string_at(raw, b)
                                    j2 = _skip_ws(raw, e2)
                                    if (d2 == 0 and v2 == b"paths"
                                            and raw[j2:j2 + 1] == b":"):
                                        raise RuntimeError(
                                            f"{filename}: duplicate paths "
                                            "key in skills object — "
                                            "refusing to guess")
                                    b = e2
                                    continue
                                if ch2 in (b"{", b"["):
                                    d2 += 1
                                elif ch2 in (b"}", b"]"):
                                    if ch2 == b"}" and d2 == 0:
                                        return span
                                    d2 -= 1
                                b += 1
                            return span
                    b += 1
                raise RuntimeError(f"{filename}: unterminated paths array")
            i = end
            continue
        if c == b"{":
            if not started:
                started = True  # entering the object itself — do not count
            else:
                depth += 1
        elif c == b"}" and started:
            if depth == 0:
                break  # end of the skills object — paths never found
            depth -= 1
        elif c == b"[":
            depth += 1
        elif c == b"]":
            depth -= 1
        i += 1
    raise RuntimeError(
        f"{filename}: skills object has no paths key — refusing blind rewrite")


def _render_paths_array(paths: list[str]) -> bytes:
    inner = ",\n".join(json.dumps(p) for p in paths)
    indented = "\n".join(
        ("      " + line if line else line) for line in inner.splitlines()
    )
    return f'[\n{indented}\n    ]'.encode("utf-8")


def render(registry: Registry) -> bytes:
    """Pure render: current file BYTES with ONLY the top-level
    skills.paths array replaced by the registry-derived list. Raises
    RuntimeError on any structural surprise — never guesses."""
    runtime_path = REPO_ROOT / filename
    if not runtime_path.exists():
        raise RuntimeError(
            f"{filename} missing — tracked runtime config expected in every "
            "checkout; refusing to invent one from scratch")
    raw = runtime_path.read_bytes()
    start, end = _locate_top_level_paths_span(raw)
    out = raw[:start] + _render_paths_array(_category_dirs(registry)) + raw[end:]
    # sanity: the result must parse and carry exactly the derived paths at
    # the TOP LEVEL.
    parsed = json.loads(out.decode("utf-8"))
    if parsed.get("skills", {}).get("paths") != _category_dirs(registry):
        raise RuntimeError(
            f"{filename}: span replace produced wrong top-level paths")
    return out


def write_atomic(registry: Registry, out_path: Path) -> None:
    """Regen-side writer with concurrent-modification guards and atomic
    replace. regen-skill-surfaces.py prefers this over plain write_text
    when a generator defines it."""
    runtime_path = REPO_ROOT / filename
    stat_before = runtime_path.stat()  # BEFORE render reads the file
    expected = render(registry)
    # TOCTOU guard #1: refuse to clobber a file that changed mid-render.
    current = runtime_path.read_bytes()
    stat_mid = runtime_path.stat()
    if (stat_mid.st_mtime_ns, stat_mid.st_size) != (
            stat_before.st_mtime_ns, stat_before.st_size):
        raise RuntimeError(
            f"{filename} changed while rendering — refusing to overwrite; "
            "re-run regen")
    if current == expected:
        return  # already in sync; no write, no mtime churn
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        dir=str(out_path.parent), prefix=".kilo.jsonc.", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as tmp:
            tmp.write(expected)
            tmp.flush()
            os.fsync(tmp.fileno())
        # preserve the original file mode (mkstemp creates 0600; the
        # tracked config is 0644 — other readers must keep access)
        os.chmod(tmp_name, stat_before.st_mode & 0o7777)
        # TOCTOU guard #2: last check immediately before the atomic swap.
        stat_last = runtime_path.stat()
        if (stat_last.st_mtime_ns, stat_last.st_size) != (
                stat_before.st_mtime_ns, stat_before.st_size):
            raise RuntimeError(
                f"{filename} changed during write — refusing to replace; "
                "re-run regen")
        os.replace(tmp_name, out_path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
