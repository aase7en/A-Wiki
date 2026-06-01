---
name: render-html
description: Turn A-Wiki structured data (model-scout results, post-mortems/code-reviews, health digests, knowledge graph, plan files) into a self-contained, interactive HTML artifact so a human actually reviews it instead of skimming a wall of Markdown. Use after producing JSON/structured output that the user must read, compare, or decide on. NOT for source-of-truth docs (CLAUDE.md, wiki pages, ADRs) — those stay Markdown.
origin: A-Wiki (local)
last_verified: 2026-06-01
---

# render-html

> HTML is a **layer on top of** Markdown/JSON, never a replacement. Rule of thumb lives in
> `docs/protocols/md-vs-html-output.md`: **Markdown** for git-tracked, long-lived, diff-reviewed files;
> **HTML** for ephemeral, interactive artifacts where a wall of Markdown would push the human out of the loop.
> (Source: Thariq Shihipar / Anthropic — "HTML is the new Markdown", May 2026.)

## When to use

After you produce structured output the user must **read, compare, or decide on**:

| Surface | Data source | Why HTML helps |
|---|---|---|
| `scouter` | `agent-skills/swarm-intelligence/model-scouter.md` JSON | sort/filter models instead of reading raw JSON |
| `report` | post-mortem / scrutinize / code-review output | severity badges, colored diffs, timeline |
| `health` | `scripts/wiki-health-digest.py --json` | at-a-glance OK/WARN/FAIL dashboard |
| `graph` | `.wiki-graph.json` | interactive force view of hubs & links |
| `plan` | `.claude/plans/*.md` via `parse_plan.py` | data-journalist view: progressive sections + phase Approve/Skip cards + round-trip JSON decision |

## How to run

```bash
# data file → artifact (default: exports/html/<surface>-<timestamp>.html)
python3 skills/render-html/scripts/render.py scouter --in scout.json
python3 skills/render-html/scripts/render.py report  --in report.json --out exports/html/pm.html
python3 skills/render-html/scripts/render.py health  --in <(python3 scripts/wiki-health-digest.py --json)
python3 skills/render-html/scripts/render.py graph   --in .wiki-graph.json

# plan viewer — parse a .md plan file then render (pipe in one shot)
python3 skills/render-html/scripts/parse_plan.py ~/.claude/plans/my-plan.md | \
  python3 skills/render-html/scripts/render.py plan --in -

# pipe JSON via stdin
echo '{...}' | python3 skills/render-html/scripts/render.py scouter

# rebuild the artifact index page
python3 skills/render-html/scripts/build-index.py   # → exports/html/index.html
```

Every artifact carries a **Copy as JSON** button → the user's edits/selections round-trip back into
the agent (set `window.AWIKI_EXPORT` in an adapter to customise the payload). This is what keeps the
human in the loop instead of rubber-stamping.

## Output location & safety

- Artifacts write to `exports/html/` which is **gitignored** (`*` except `.gitignore`) — ephemeral by design.
- Zero runtime dependencies: pure HTML/CSS/JS, all data embedded inline (works offline, no CDN).
- Data is embedded in a `<script type="application/json">` block with `</` escaped, so content can't break out.
- Never write HTML into `wiki/`, `raw/`, or onto `CLAUDE.md` — those are Markdown source-of-truth.

## Add a new surface (this is the compounding part)

1. Add `templates/<surface>.html` — body markup, then a `<!--SCRIPT-->` line, then JS that reads
   `window.AWIKI_DATA` and renders into `#awiki-root`. Reuse the base CSS tokens (`var(--text)`, `var(--accent)`, `.card`, `.badge`).
2. Add one entry to `registry.json` (`template`, `title`, `required_keys`, `data_source`).
3. Add `fixtures/<surface>.json` and the surface name to `SURFACES` in `tests/test_render_html.py`.

No change to `scripts/render.py` is needed — the renderer is data-driven from the registry.

## Verify

```bash
python3 -m pytest skills/render-html/tests/test_render_html.py -v
```
