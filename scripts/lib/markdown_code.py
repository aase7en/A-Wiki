"""Lightweight CommonMark-style code-region stripping for wiki scanners.

Preserves line breaks so callers may still use surrounding text positions,
while replacing code content with spaces. This intentionally handles only
code fences and code spans; it is not a full Markdown parser.
"""
from __future__ import annotations

import re


_FENCE_OPEN_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
_FENCE_CLOSE_RE = re.compile(r"^ {0,3}([`~]+)[ \t]*$")


def _blank(text: str) -> str:
    """Blank visible characters while preserving CR/LF structure."""
    return "".join(ch if ch in "\r\n" else " " for ch in text)


def _strip_fenced_code(text: str) -> str:
    out: list[str] = []
    fence_char = ""
    fence_len = 0

    for line in text.splitlines(keepends=True):
        raw = line.rstrip("\r\n")
        if fence_char:
            close = _FENCE_CLOSE_RE.match(raw)
            if close:
                run = close.group(1)
                if run[0] == fence_char and set(run) == {fence_char} and len(run) >= fence_len:
                    fence_char = ""
                    fence_len = 0
            out.append(_blank(line))
            continue

        opening = _FENCE_OPEN_RE.match(raw)
        if opening:
            run, rest = opening.group(1), opening.group(2)
            # CommonMark forbids backticks in a backtick-fence info string.
            if run[0] != "`" or "`" not in rest:
                fence_char = run[0]
                fence_len = len(run)
                out.append(_blank(line))
                continue

        out.append(line)

    return "".join(out)


def _strip_code_spans(text: str) -> str:
    chars = list(text)
    i = 0
    while i < len(text):
        if text[i] != "`":
            i += 1
            continue

        opener_end = i + 1
        while opener_end < len(text) and text[opener_end] == "`":
            opener_end += 1
        run_len = opener_end - i

        cursor = opener_end
        close_end = -1
        while cursor < len(text):
            if text[cursor] != "`":
                cursor += 1
                continue
            candidate_end = cursor + 1
            while candidate_end < len(text) and text[candidate_end] == "`":
                candidate_end += 1
            if candidate_end - cursor == run_len:
                close_end = candidate_end
                break
            cursor = candidate_end

        if close_end < 0:
            i = opener_end
            continue

        for pos in range(i, close_end):
            if chars[pos] not in "\r\n":
                chars[pos] = " "
        i = close_end

    return "".join(chars)


def strip_markdown_code(text: str) -> str:
    """Return Markdown text with fenced/inline code regions blanked."""
    return _strip_code_spans(_strip_fenced_code(text))
