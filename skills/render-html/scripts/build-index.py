#!/usr/bin/env python3
"""Build exports/html/index.html — a single entry point listing generated artifacts.

Reads the artifact filenames already in exports/html/ (gitignored, ephemeral) and
writes an index that links to each, newest first. Run after generating artifacts:

    python3 skills/render-html/scripts/build-index.py
"""
from __future__ import annotations

import datetime as _dt
import html
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = REPO_ROOT / "exports" / "html"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    items = sorted(
        (p for p in OUT_DIR.glob("*.html") if p.name != "index.html"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    rows = "\n".join(
        '<li><a href="{n}">{n}</a> <span class="m">{when} · {kb} KB</span></li>'.format(
            n=html.escape(p.name),
            when=_dt.datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
            kb=p.stat().st_size // 1024,
        )
        for p in items
    ) or '<li class="m">No artifacts yet — run render.py to generate some.</li>'

    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>A-Wiki HTML artifacts</title>
<style>
body{{font:15px/1.6 -apple-system,"Segoe UI",Roboto,system-ui,sans-serif;background:#0f1115;color:#e6e9ef;max-width:760px;margin:40px auto;padding:0 22px}}
h1{{background:linear-gradient(90deg,#7c5cff,#28d6c8);-webkit-background-clip:text;background-clip:text;color:transparent}}
a{{color:#28d6c8;text-decoration:none}} a:hover{{text-decoration:underline}}
ul{{list-style:none;padding:0}} li{{padding:10px 0;border-bottom:1px solid #2b313c}}
.m{{color:#9aa4b2;font-size:12px}}
</style></head><body>
<h1>A-Wiki · HTML artifacts</h1>
<p class="m">Ephemeral, self-contained dashboards & reports. Source-of-truth stays in Markdown/JSON.</p>
<ul>
{rows}
</ul>
</body></html>
"""
    out = OUT_DIR / "index.html"
    out.write_text(doc, encoding="utf-8")
    print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
