"""a_design_gate.py — Quality Gate rubric evaluator (pure function).

Deterministic scoring of design decisions against the 8-category rubric
documented in skills/awiki/a-design/references/quality-gate.md.

The rubric is intentionally NON-vision — it accepts structured design_tokens
JSON (the same shape a-design's composition layer produces) and checks
verifiable rules. Vision-based evaluation is out of scope (would need ML).

Public API:
  - evaluate(design_tokens) -> dict   returns {total, per_category, blocked, fails}
  - SHIP_THRESHOLD = 80

Categories (max 100):
  Hierarchy (15) · Typography (15) · Color (15) · Composition (15)
  Motion (10) · Accessibility (15) · Distinctiveness (10) · Craft (5)

Fail-soft: missing fields do not crash; they earn 0 in their category.
"""
from __future__ import annotations

from typing import Any

__all__ = ["evaluate", "SHIP_THRESHOLD", "MAX_SCORE", "CATEGORIES"]

SHIP_THRESHOLD = 80
MAX_SCORE = 100

# Category -> max points
CATEGORIES: dict[str, int] = {
    "hierarchy": 15,
    "typography": 15,
    "color": 15,
    "composition": 15,
    "motion": 10,
    "accessibility": 15,
    "distinctiveness": 10,
    "craft": 5,
}

# WCAG relative luminance threshold for "dark background" classification.
# Adapted from ui-ux-pro-max (skills/ui-ux-pro-max/) + StyleSeed concept.
_DARK_BG_MAX_LUMINANCE = 0.18


# ── helpers ────────────────────────────────────────────────────────────────

def _hex_luminance(hex_color: str) -> float:
    """WCAG relative luminance of a #RRGGBB hex. Returns 0.0 on parse failure."""
    if not isinstance(hex_color, str):
        return 0.0
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return 0.0
    try:
        r, g, b = (int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
    except ValueError:
        return 0.0
    linear = [
        c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
        for c in (r, g, b)
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast_ratio(fg: str, bg: str) -> float:
    """WCAG contrast ratio between two hex colors. Returns 1.0 on failure."""
    l1 = _hex_luminance(fg)
    l2 = _hex_luminance(bg)
    lighter, darker = max(l1, l2), min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def _is_ai_purple(hex_color: str) -> bool:
    """Detect the cliché AI-purple defaults (Lila Rule from taste-skill)."""
    cliches = {"#6366F1", "#8B5CF6", "#7C3AED", "#A855F7"}  # indigo/violet defaults
    return hex_color.lstrip("#").upper() in {c.lstrip("#") for c in cliches}


# ── per-category scorers ──────────────────────────────────────────────────

def _score_hierarchy(tokens: dict[str, Any]) -> tuple[int, list[str]]:
    """15 pts: focal point present + visual weight ladder."""
    score = 0
    fails: list[str] = []
    if tokens.get("focal_point"):
        score += 8
    else:
        fails.append("no focal_point declared")
    # weight ladder: at least 2 distinct levels
    weights = tokens.get("visual_weights") or []
    if len(set(weights)) >= 2:
        score += 4
    elif weights:
        fails.append("visual_weights all same — no hierarchy")
    # size-based hierarchy signal
    if tokens.get("uses_size_hierarchy"):
        score += 3
    return min(score, 15), fails


def _score_typography(tokens: dict[str, Any]) -> tuple[int, list[str]]:
    """15 pts: scale ratio + line-height + non-default font."""
    score = 0
    fails: list[str] = []
    if tokens.get("type_scale_ratio") in {"3:2", "4:5", "1.618", "minor-third", "major-second", "perfect-fourth"}:
        score += 5
    elif tokens.get("type_scale_ratio"):
        fails.append(f"type_scale_ratio unrecognized: {tokens['type_scale_ratio']}")
    body_lh = tokens.get("body_line_height")
    if isinstance(body_lh, (int, float)) and 1.4 <= body_lh <= 1.6:
        score += 4
    elif body_lh:
        fails.append(f"body_line_height {body_lh} outside 1.4–1.6")
    # ban Inter/Roboto/Arial as defaults
    body_font = (tokens.get("body_font") or "").lower()
    if body_font and body_font not in {"inter", "roboto", "arial", "helvetica", "system-ui"}:
        score += 4
    elif body_font:
        fails.append(f"body_font {body_font} is overused default")
    # serif discipline (taste-skill)
    if tokens.get("serif_default") is False:
        score += 2
    return min(score, 15), fails


def _score_color(tokens: dict[str, Any]) -> tuple[int, list[str]]:
    """15 pts: WCAG contrast + semantic tokens + no AI-purple."""
    score = 0
    fails: list[str] = []
    palette = tokens.get("palette") or {}
    fg = palette.get("fg")
    bg = palette.get("bg")
    if fg and bg:
        ratio = _contrast_ratio(fg, bg)
        if ratio >= 4.5:
            score += 5
        elif ratio >= 3.0:
            score += 2
            fails.append(f"contrast {ratio:.1f}:1 < 4.5 (large-text only)")
        else:
            fails.append(f"contrast {ratio:.1f}:1 FAIL WCAG AA")
    # semantic tokens present (not ad-hoc hex)
    semantic_keys = {"bg", "fg", "card", "border", "accent", "destructive"}
    if semantic_keys.issubset(palette.keys()):
        score += 4
    else:
        missing = semantic_keys - palette.keys()
        fails.append(f"palette missing semantic keys: {sorted(missing)}")
    # refined black (not pure #000)
    if fg and fg.lstrip("#").upper() in {"000000", "000"}:
        fails.append("fg is pure #000 — use refined black #2A2A2A")
    elif fg:
        score += 2
    # anti AI-purple
    accent = palette.get("accent", "")
    if _is_ai_purple(accent):
        fails.append("accent is AI-purple cliché (Lila Rule)")
    elif accent:
        score += 4
    return min(score, 15), fails


def _score_composition(tokens: dict[str, Any]) -> tuple[int, list[str]]:
    """15 pts: grid + density-appropriate + alignment."""
    score = 0
    fails: list[str] = []
    if tokens.get("grid_system") in {"12-col", "bento", "asymmetric", "single-column", "8-col"}:
        score += 5
    elif tokens.get("grid_system"):
        fails.append(f"grid_system unrecognized: {tokens['grid_system']}")
    # density matches grammar
    grammar = tokens.get("grammar", "")
    density = tokens.get("density", "")
    pairs_ok = (
        ("consumer-service", "spacious"),
        ("operations-console", "dense"),
        ("technical-instrument", "dense"),
        ("editorial-reading", "balanced"),
        ("expressive-marketing", "balanced"),
    )
    if any(g == grammar and d == density for g, d in pairs_ok):
        score += 5
    elif density:
        fails.append(f"density {density!r} may not match grammar {grammar!r}")
    # whitespace as design element
    if tokens.get("whitespace_intentional"):
        score += 5
    return min(score, 15), fails


def _score_motion(tokens: dict[str, Any]) -> tuple[int, list[str]]:
    """10 pts: duration tokens + reduced-motion + exit faster than enter."""
    score = 0
    fails: list[str] = []
    if tokens.get("duration_tokens"):
        score += 3
    if tokens.get("prefers_reduced_motion") is True:
        score += 4
    else:
        fails.append("prefers_reduced_motion not handled (critical)")
    # exit faster than enter
    exit_dur = tokens.get("exit_duration_ms")
    enter_dur = tokens.get("enter_duration_ms")
    if isinstance(exit_dur, (int, float)) and isinstance(enter_dur, (int, float)):
        if exit_dur <= enter_dur * 0.75:
            score += 3
        else:
            fails.append(f"exit {exit_dur}ms not faster than enter {enter_dur}ms")
    return min(score, 10), fails


def _score_accessibility(tokens: dict[str, Any]) -> tuple[int, list[str]]:
    """15 pts: touch targets + focus states + ARIA semantic + color-not-only-state."""
    score = 0
    fails: list[str] = []
    a11y = tokens.get("accessibility") or {}
    if a11y.get("touch_target_pt") and a11y["touch_target_pt"] >= 44:
        score += 5
    elif a11y.get("touch_target_pt"):
        fails.append(f"touch_target {a11y['touch_target_pt']}pt < 44pt minimum")
    if a11y.get("focus_visible") is True:
        score += 5
    else:
        fails.append("focus_visible not declared (critical)")
    if a11y.get("aria_semantic") is True:
        score += 3
    if a11y.get("color_not_only_state") is True:
        score += 2
    return min(score, 15), fails


def _score_distinctiveness(tokens: dict[str, Any]) -> tuple[int, list[str]]:
    """10 pts: anti-AI-tell (icon-chip cliché, all-even grid, ghost numbering)."""
    score = 10  # start full, deduct for tells
    fails: list[str] = []
    distinct = tokens.get("distinctiveness") or {}
    if distinct.get("icon_chip_cliche"):
        score -= 4
        fails.append("icon-chip cliché detected (Lucide in tinted rounded-square)")
    if distinct.get("all_even_grid"):
        score -= 3
        fails.append("all-even grid — no focal point")
    if distinct.get("ghost_numbering"):
        score -= 2
        fails.append("ghost 01/02/03 numbering on every section")
    if distinct.get("stock_hero_visual"):
        score -= 3
        fails.append("hero uses stock/placeholder visual")
    return max(score, 0), fails


def _score_craft(tokens: dict[str, Any]) -> tuple[int, list[str]]:
    """5 pts: number ratio 2:1 + refined black + low-opacity shadow + single accent."""
    score = 0
    fails: list[str] = []
    craft = tokens.get("craft") or {}
    if craft.get("number_ratio_2to1"):
        score += 1
    if craft.get("refined_black"):
        score += 1
    if craft.get("low_opacity_shadow"):
        score += 1
    if craft.get("single_accent"):
        score += 1
    if craft.get("eyebrow_restraint"):
        score += 1
    return min(score, 5), fails


_SCORERS = {
    "hierarchy": _score_hierarchy,
    "typography": _score_typography,
    "color": _score_color,
    "composition": _score_composition,
    "motion": _score_motion,
    "accessibility": _score_accessibility,
    "distinctiveness": _score_distinctiveness,
    "craft": _score_craft,
}


# ── public API ────────────────────────────────────────────────────────────

def evaluate(design_tokens: dict[str, Any]) -> dict[str, Any]:
    """Evaluate design decisions against the 8-category Quality Gate rubric.

    Returns:
      {
        "total": int,                # 0-100
        "ship_threshold": 80,
        "blocked": bool,             # True if total < 80
        "per_category": {cat: {"score": int, "max": int, "fails": [str]}},
        "fails": [str],              # flat list of all fail reasons
      }

    Fail-soft: missing fields score 0 in their category, never raise.
    """
    per_category: dict[str, dict[str, Any]] = {}
    all_fails: list[str] = []
    total = 0
    for cat, scorer in _SCORERS.items():
        score, fails = scorer(design_tokens)
        max_pts = CATEGORIES[cat]
        per_category[cat] = {"score": score, "max": max_pts, "fails": fails}
        total += score
        all_fails.extend(f"{cat}: {f}" for f in fails)
    return {
        "total": total,
        "ship_threshold": SHIP_THRESHOLD,
        "blocked": total < SHIP_THRESHOLD,
        "per_category": per_category,
        "fails": all_fails,
    }
