"""
Contract tests for the redesigned A-Wiki Live Dashboard (live-dashboard.html).

Guards the Definition of Done from docs/design/dashboard-design-system.md:
no dead DOM refs from the old layout, < 60KB, all SSE/API contracts wired, the
8 requested animation components present, and prefers-reduced-motion honored.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
HTML = REPO_ROOT / "scripts" / "live-dashboard" / "live-dashboard.html"

DEAD_REFS = ("primary-card", "connector-svg", "model-grid")


def _read():
    assert HTML.is_file(), "live-dashboard.html must exist"
    return HTML.read_text(encoding="utf-8")


def test_no_dead_dom_refs_from_old_layout():
    text = _read()
    found = [r for r in DEAD_REFS if r in text]
    assert not found, f"dead DOM refs from old layout remain: {found}"


def test_file_under_60kb():
    size = HTML.stat().st_size
    assert size < 60 * 1024, f"HTML too large: {size} bytes (limit 60KB)"


# ── Phase 0: token reconciliation + size contract ─────────────────────────

def test_no_deep_space_decoration():
    """The deep-space palette (nebula, stars, --space-*) is banned decoration."""
    text = _read()
    assert "--space-" not in text, "deep-space --space-* tokens must be removed"
    assert 'id="nebula"' not in text, "#nebula element must be removed"
    assert 'id="stars"' not in text, "#stars element must be removed"
    assert "#nebula" not in text, "#nebula selector must be removed"
    assert "#stars" not in text, "#stars selector must be removed"


def test_no_glow_triplet():
    """The three --glow-* tokens collapse into a single --shadow-glow."""
    text = _read()
    for t in ("--glow-cyan", "--glow-gold", "--glow-violet"):
        assert t not in text, f"{t} must be removed (collapse to --shadow-glow)"
    assert "--shadow-glow" in text, "single --shadow-glow token must exist"


def test_root_declares_documented_tokens():
    """:root must adopt the dashboard-design-system.md tokens verbatim."""
    text = _read()
    root = text[: text.find("</style>")]
    for token, hexv in (
        ("--elev-0", "#06060d"),
        ("--elev-1", "#0c0c18"),
        ("--elev-2", "#14142a"),
        ("--elev-3", "#1e1e3a"),
        ("--text-tertiary", "#64748b"),
    ):
        assert token in root, f":root must declare {token}"
        assert hexv in root, f":root {token} must use documented {hexv}"
    assert "#7c8aa5" not in root, "old tertiary #7c8aa5 must be gone"


def test_no_hardcoded_hex_outside_root():
    """Color hex literals may only live in :root (design-system DoD)."""
    text = _read()
    root_end = text.find("</style>")
    outside_root = text[root_end:]
    # CSS hex inside the rest of <style> (after :root block close)
    style_after = text[text.find("}") + 1 : root_end]
    # ignore SVG gradient stop-color attributes which are data, not theme
    leaks = re.findall(r"#[0-9a-fA-F]{6}\b", style_after)
    assert not leaks, f"hardcoded hex outside :root in <style>: {leaks[:8]}"


def test_sse_and_api_contracts_wired():
    text = _read()
    for token in ("/events", "/api/graph", "/api/models", "/api/keys", "/api/capabilities"):
        assert token in text, f"missing API/SSE contract: {token}"
    assert "EventSource" in text, "must open an SSE EventSource"


def test_prefers_reduced_motion_honored():
    text = _read()
    assert "prefers-reduced-motion" in text, "must honor prefers-reduced-motion"


# ── The 8 requested animation components ──────────────────────────────────

def test_animated_counter():
    text = _read()
    assert ("requestAnimationFrame" in text and ("data-counter" in text or "animateCounter" in text)), \
        "Animated Counter (rAF + counter target) missing"


def test_glow_line_divider():
    text = _read()
    assert "glow-divider" in text and "@keyframes" in text, "Glow Line Divider missing"


def test_progress_bar_with_shimmer():
    text = _read()
    assert "progress-bar" in text and "shimmer" in text.lower(), \
        "Progress Bar + shimmer overlay missing"


def test_typed_rotator():
    text = _read()
    assert ("data-typed" in text) or ("typedRotator" in text) or ("typeRotate" in text), \
        "Typed Rotator (types/deletes phrases) missing"


def test_fade_word_cycle():
    text = _read()
    assert "fade-cycle" in text or "fadeWord" in text, "Fade Word Cycle missing"


def test_animated_gradient():
    text = _read()
    assert "gradient-shift" in text or "animated-gradient" in text, "Animated Gradient missing"


def test_glow_toggle():
    text = _read()
    assert "glow-toggle" in text or "glow-toggle" in text, "Glow Toggle missing"


def test_glassmorphism_cards():
    text = _read()
    assert "glass-card" in text and "backdrop-filter" in text, "Glassmorphism Cards missing"


def test_branching_timeline_present():
    """Centerpiece: delegation lanes branching over a time axis."""
    text = _read()
    assert "lane" in text and ("time-axis" in text or "axis" in text), \
        "branching timeline (lanes + time axis) missing"


# ── Phase 1: animation-as-signal discipline ────────────────────────────────

def test_no_infinite_animation_on_decorative_elements():
    """Only status-driven (.active,.on,.busy,.hot,.tick,.block,.done,.fail)
    and component-marker (.fade-cycle,.word,#typed-intro) elements may use
    animation:...infinite. No always-on ambient loops."""
    text = _read()
    style_end = text.find("</style>")
    style = text[:style_end]
    # the minified CSS splits rules with "}\n"
    rules = style.split("}\n")
    errs = []
    for rule in rules:
        if "infinite" not in rule:
            continue
        brace = rule.find("{")
        if brace == -1:
            continue
        selector = rule[:brace].strip()
        ok = any(x in selector for x in (
            ".active", ".on", ".busy", ".hot", ".tick",
            ".block", ".done", ".fail",
            ".word", "#typed-intro",
        ))
        if not ok:
            errs.append(f"infinite animation on non-status selector: {selector[:80]}")
    assert not errs, "\n".join(errs)


# ── Phase 2: operator signal — failures KPI + cost tile + Summary view ────

def test_failures_and_cost_kpi_tiles_exist():
    text = _read()
    assert "s-fail" in text, "Failures KPI counter (#s-fail) must exist"
    assert "errors-rail" in text, "Errors rail (#errors-rail) must exist"
    assert "kpi-cost" in text, "Cost KPI tile (#kpi-cost) must exist"


def test_summary_view_exists_and_is_default():
    text = _read()
    assert "view-summary" in text, "Summary view panel must exist"
    assert "currentView=" in text, "view-tracking variable must exist"


def test_failures_handler_wires_to_errors_rail():
    text = _read()
    assert "s-fail" in text, "fail counter element id must exist"
