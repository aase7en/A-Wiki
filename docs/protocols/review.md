# 🕵️ Skeptical Reviewer Protocol

> **Phase 5** — A disciplined review layer that runs every session-end to catch
> stale code, missing docs, broken links, and quality regressions before they pile up.

---

## Rationale

The wiki grows fast. Scripts, hooks, skills, and entities accumulate across
sessions. Without a skeptical reviewer running at session boundaries, three
things happen:

1. **Bit rot** — scripts that depend on removed apis quietly break
2. **Orphan drift** — entities get created but never cross-linked
3. **Quality decay** — bare-bones stubs accumulate without abstracts or
   frontmatter

The Skeptical Reviewer is a **code-review-minded agent** (not an LLM call).
It runs deterministic checks in ~3 seconds and flags actionable items.

---

## Review Layers

| Layer | Check | Owner |
|-------|-------|-------|
| L1 | Script health — each `.py` in `scripts/` has `if __name__` guard | `review-check.py` |
| L2 | Frontmatter completeness — title, type, tags on every wiki page | `review-check.py` |
| L3 | Link integrity — `wiki/*.md` links resolve to existing files | `review-check.py` |
| L4 | Orphan detection — entities not cross-linked from other pages | `review-check.py` |
| L5 | Stale echo — skills/* dirs without an active README.md | `review-check.py` |
| L6 | Quality floor — entities missing abstract or empty body | `review-check.py` |

---

## Results Format

Each review run writes to `wiki/context/review-report.md`:

```markdown
# Review Report — YYYY-MM-DD HH:MM

## Summary
- ✓ Passed: N
- ⚠ Warnings: N
- ❌ Failures: N

## Failures
<!-- itemized -->

## Warnings
<!-- itemized -->

## Passed
<!-- itemized -->
```

The file is overwritten each run (not appended). The MOST RECENT report is
always at `wiki/context/review-report.md`.

---

## CLI Usage

```bash
# Run full review
python3 scripts/review-check.py

# Run only specific layers
python3 scripts/review-check.py --layers L1,L3,L5

# Exit 1 on any failure (CI mode)
python3 scripts/review-check.py --strict
```

---

## Integration

The review runs automatically at the end of every `gen-index.py` execution
(which itself runs at session-start via hooks). Results are written to
`wiki/context/review-report.md` and printed to stdout for immediate awareness.

Sessions that terminate mid-way (e.g. user closes before gen-index runs) will
not trigger review — this is acceptable. The next full session will catch any
issues.

---

*Defined: 2026-05-24 — A-Wiki Hybrid v1.0*