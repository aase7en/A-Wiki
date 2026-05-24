---
id: 0004
title: "Auto-Synthesis Pipeline (Phase 4c) — Design Spec"
status: proposed
date: 2026-05-24
author: Cline / Aase7en
---

# Auto-Synthesis Pipeline — Design Spec

## Script 1: `scripts/raw-to-source.py`

**Purpose**: Scan `raw/` for `.md` files without a corresponding `wiki/sources/<slug>.md` and auto-generate source frontmatter.

### Slug Generation
```python
def raw_to_slug(filename: str) -> str:
    # Strip .md, lowercase, replace spaces/special chars with hyphens
    # Remove duplicate hyphens, trim trailing hyphens, max 60 chars
```

### Domain Detection (priority)
1. Parent directory inside `raw/` (e.g., `raw/ai/` → `ai-tools`)
2. Keyword match in filename (`pharmacy`, `esp32`, `raspberry`, `iot`, `lora`)

### Frontmatter Template
```yaml
---
type: source
title: <best-guess from H1 or filename>
slug: <slug>
date_ingested: <today's date>
original_file: raw/<filename>
tags: [<auto-detected from keywords>]
---
```

### CLI
```bash
python3 scripts/raw-to-source.py --dry-run   # Show what would be created
python3 scripts/raw-to-source.py --apply      # Create source files
python3 scripts/raw-to-source.py --all        # Force re-process all
```

---

## Script 2: `scripts/raw-to-synth.py`

**Purpose**: Score existing sources (0-10) and auto-generate synthesis stubs for quality ≥ 5.

### Quality Scoring Rubric

| Criterion | Max | Measure |
|-----------|-----|---------|
| Word count | 3 | >300=3pt, >100=2pt, >30=1pt |
| Frontmatter completeness | 2 | title+tags+date=2pt, partial=1pt |
| Section structure | 2 | ≥3 `##` headers=2pt, 1-2=1pt |
| Code/lists/diagrams | 2 | code+table+bullets=2pt, one=1pt |
| Citation density | 1 | references/links=1pt |

**Tiers**: 0-3 Low, 4-6 Medium, 7-10 High

### Synthesis Generation (score ≥ 5)
```markdown
---
type: synthesis
title: "<original> — Synthesis"
slug: synth-<source-slug>
date_synthesized: <today>
sources: [wiki/sources/<slug>.md]
quality_score: <score>/10
domain: <detected>
---

# <Title> — Synthesis
> Quality Score: <score>/10

## Summary
<First 3 lines of TL;DR or H1 paragraph>

## Key Points
1. <extracted from first section>
2. ...
3. ...

## Relevance
_To be filled in by human review._
```

### Scoring Output (table)
```
 Quality Report — wiki/sources/ (68 sources)
┌─────────────────────────────┬──────┬──────────┐
│ Source                      │ Score│ Tier     │
├─────────────────────────────┼──────┼──────────┤
│ esp32-complete-guide-thai   │  8   │ High     │
│ ...                         │      │          │
├─────────────────────────────┼──────┼──────────┤
│ Average: 5.8/10             │      │          │
│ High: 12  Med: 28  Low: 28 │      │          │
└─────────────────────────────┴──────┴──────────┘
```

### CLI
```bash
python3 scripts/raw-to-synth.py                            # Full scan
python3 scripts/raw-to-synth.py --source <slug>            # Single
python3 scripts/raw-to-synth.py --dry-run                  # Scores only
python3 scripts/raw-to-synth.py --json                     # JSON output
```

---

## Chaining (in `gen-index.py`)

```python
# Auto-synthesis pipeline
for chained_script in ("raw-to-source.py", "raw-to-synth.py"):
    sp = scripts_dir / chained_script
    if sp.exists():
        subprocess.run([sys.executable, str(sp), "--apply" if chained_script == "raw-to-source.py" else ""], check=False)
```

---

## Implementation Order
1. `scripts/raw-to-source.py` (~120 lines) — slug + domain + frontmatter
2. `scripts/raw-to-synth.py` (~180 lines) — scoring + synthesis + table

*Design complete — ready for human implementation.*