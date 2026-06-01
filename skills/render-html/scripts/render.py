#!/usr/bin/env python3
"""render-html — turn A-Wiki structured data into a self-contained HTML artifact.

The HTML layer sits *on top of* Markdown/JSON source-of-truth; it never replaces it.
Use it for ephemeral, interactive artifacts (dashboards, reports, model comparisons)
where a wall of Markdown would push the human out of the review loop.

Usage:
    python3 scripts/render.py <surface> --in data.json [--out path.html]
    python3 scripts/render.py <surface> --in -            # read JSON from stdin
    cat data.json | python3 scripts/render.py <surface>   # stdin shortcut

Surfaces are defined in registry.json. Add a new surface = add a template + one entry.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = SKILL_ROOT / "templates"
REGISTRY = SKILL_ROOT / "registry.json"
# exports/html lives at repo root: A-Wiki/exports/html
REPO_ROOT = SKILL_ROOT.parents[1]
DEFAULT_OUT_DIR = REPO_ROOT / "exports" / "html"

SCRIPT_MARKER = "<!--SCRIPT-->"


def _load_registry() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))["surfaces"]


def _embed_json(data) -> str:
    """JSON-encode and neutralise any '</script>' / '</' breakout inside a
    <script type=application/json> container."""
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


def render(surface: str, data: dict, generated_at: str | None = None) -> str:
    """Return a complete, self-contained HTML document string for ``surface``."""
    registry = _load_registry()
    if surface not in registry:
        raise ValueError(
            f"unknown surface {surface!r}; known: {', '.join(sorted(registry))}"
        )
    entry = registry[surface]

    missing = [k for k in entry.get("required_keys", []) if k not in data]
    if missing:
        raise ValueError(f"{surface}: data missing required keys: {missing}")

    template_text = (TEMPLATES / entry["template"]).read_text(encoding="utf-8")
    if SCRIPT_MARKER in template_text:
        body, _, script = template_text.partition(SCRIPT_MARKER)
    else:
        body, script = template_text, ""

    if generated_at is None:
        generated_at = (
            data.get("scouted_at")
            or data.get("generated_at")
            or _dt.datetime.now().strftime("%Y-%m-%d %H:%M")
        )

    base = (TEMPLATES / "_base.html").read_text(encoding="utf-8")
    # Order matters: inject adapter chunks before data so a stray token in the
    # template can't collide with placeholders that are still unresolved.
    html = (
        base.replace("__TITLE__", entry["title"])
        .replace("__SURFACE__", surface)
        .replace("__GENERATED_AT__", str(generated_at))
        .replace("__ADAPTER_SCRIPT__", script.strip())
        .replace("__ADAPTER__", body.strip())
        .replace("__DATA_JSON__", _embed_json(data))
    )
    return html


def _read_input(path: str | None) -> dict:
    if path in (None, "-"):
        return json.load(sys.stdin)
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render an A-Wiki HTML artifact.")
    parser.add_argument("surface", help="surface name (see registry.json)")
    parser.add_argument("--in", dest="infile", default="-", help="JSON input file or '-' for stdin")
    parser.add_argument("--out", dest="outfile", default=None, help="output .html path")
    args = parser.parse_args(argv)

    data = _read_input(args.infile)
    html = render(args.surface, data)

    if args.outfile:
        out = Path(args.outfile)
    else:
        stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        out = DEFAULT_OUT_DIR / f"{args.surface}-{stamp}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
