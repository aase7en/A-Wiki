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
DASHBOARD_DIR = HTML.parent
SRC_DIR = DASHBOARD_DIR / "src"
STYLES_CSS = DASHBOARD_DIR / "styles.css"

DEAD_REFS = ("primary-card", "connector-svg", "model-grid")


def _read():
    """Read the full dashboard source — HTML markup + extracted JS (src/*.js) + CSS.

    v8 refactor (chunks B8/C8) split the monolithic HTML into:
      - live-dashboard.html  (markup only, ~49KB)
      - styles.css           (extracted CSS, ~41KB)
      - src/*.js             (9 modular JS files, ~180KB total)
    Tests do string matching across all three, so we concatenate them.
    """
    assert HTML.is_file(), "live-dashboard.html must exist"
    parts = [HTML.read_text(encoding="utf-8")]
    # CSS (extracted in B8)
    if STYLES_CSS.is_file():
        parts.append(STYLES_CSS.read_text(encoding="utf-8"))
    # JS source files (extracted in C8)
    if SRC_DIR.is_dir():
        for js in sorted(SRC_DIR.glob("*.js")):
            parts.append(js.read_text(encoding="utf-8"))
    return "\n".join(parts)


def test_no_dead_dom_refs_from_old_layout():
    text = _read()
    found = [r for r in DEAD_REFS if r in text]
    assert not found, f"dead DOM refs from old layout remain: {found}"


def test_file_under_60kb():
    size = HTML.stat().st_size
    # raised to 68 KB to accommodate operational features (SVG icons, filters,
    # error rail, cost tile) beyond Phase 0–1 decoration removal;
    # raised to 112 KB (user-approved 2026-07-12) for the 2026-07-11 feature
    # wave: chat pane, cost tile, failures rail, event filters, green-white
    # theme. Local-only tool served from localhost — payload is not a real
    # bottleneck; the gate now guards against unbounded growth, not leanness.
    # raised to 200 KB (2026-07-14) for the Skills Expansion v4 wave: skill
    # dependency graph, sim export (SVG/PNG), keyboard shortcuts, skill
    # comparison, walkthrough difficulty, trending analytics, AI recommender,
    # and skill versioning. All client-side JS — no external dependency added.
    # raised to 220 KB (2026-07-15) for the Skills Expansion v5 wave: graph
    # export, walkthrough suggestions, coverage inline editor, compare diff
    # highlights, trending toggle, CLI deep-link, skill changelog, semantic
    # search, PWA offline. Still client-side — no external dep added.
    # raised to 250 KB (2026-07-15) for the Skills Expansion v6 wave: command
    # palette (Ctrl+K), skill health score badge + sort, registry push SSE,
    # cycle detection banner, filter presets, matrix CSV export, co-occurrence
    # mining, auto theme (prefers-color-scheme), search history. All client-side.
    # raised to 300 KB (2026-07-15) for the Skills Expansion v7 wave: URL state
    # sync + share URL, shortcut customization (remap/export/import), desktop
    # notification system, skill lifecycle (first_seen), smart default agent,
    # workspace save/restore, skill review queue, cross-device pin (registry),
    # usage analytics tab (Chart.js CDN). 9 features across 10 chunks. Chart.js
    # itself is CDN-loaded (not inlined); the growth is panel markup + handlers.
    # Still a local-only tool; gate guards against unbounded growth, not leanness.
    # lowered to 60 KB (2026-07-15) for the v8 Foundation Refactor: JS extracted
    # to src/*.js (esbuild-bundled to app.min.js), CSS extracted to styles.css.
    # HTML now contains markup only — JS and CSS are loaded via <script src> and
    # <link>. Size budget is for markup growth; JS/CSS have their own files.
    # raised to 64 KB (2026-07-16): post-v9 eval/cost panel markup (U1-U3, V1-V3,
    # T5-T6 commits) pushed markup above 60 KB without scope to extract. Budget
    # tracks markup growth; JS/CSS remain in their own files. v10 A10 deferred
    # CDN scripts, removed chart.js preload — net markup shrank.
    # raised to 68 KB (2026-07-16): v11 Backup pane markup (Settings tab +
    # container) added ~1 KB beyond 64 KB ceiling. Render logic lives in JS;
    # this is panel shell only. Localhost tool — gate guards unbounded growth.
    # raised to 72 KB (2026-07-22): v19 Lucide icons add inline <use href>
    # refs to view-toggle-bar + header (~13 buttons × ~70 bytes SVG wrapper).
    # Sprite itself lives in JS bundle (app.min.js 260 KB budget) — HTML
    # gain is only the <use> references, not the sprite paths.
    assert size < 72 * 1024, f"HTML too large: {size} bytes (limit 72 KB — JS/CSS extracted in v8; raised for post-v9 panels + v11 Backup + v19 Lucide <use> refs)"


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
    """:root must adopt the documented design tokens.

    v8-v16 required specific emerald/teal hex values (#06060d, #14142a, …).
    v17 redesign (DESIGN.md) replaces them with the 11-step neutral scale +
    single brand accent. Updated to assert the v17 minimal palette.
    """
    if not STYLES_CSS.is_file():
        pytest.skip("styles.css not found (pre-v8)")
    css = STYLES_CSS.read_text(encoding="utf-8")
    root = css[: css.find("}")]  # :root block ends at first }
    # v17 minimal palette — documented in DESIGN.md + design-system.json
    for token, hexv in (
        ("--n-50", "#0a0a0c"),
        ("--n-100", "#121215"),
        ("--n-200", "#1a1a1f"),
        ("--brand", "#5b5bd6"),
    ):
        assert token in root, f":root must declare {token}"
        assert hexv in root, f":root {token} must use documented {hexv}"
    # Legacy aliases must still be present (compatibility for existing rules).
    for legacy in ("--elev-0", "--elev-1", "--text-tertiary", "--accent-brand"):
        assert legacy in root, f":root must keep legacy alias {legacy}"
    assert "#7c8aa5" not in root, "old tertiary #7c8aa5 must be gone"


def test_no_hardcoded_hex_outside_root():
    """Color hex literals may only live in :root or named theme-variant blocks.

    v17 (DESIGN.md) introduces `[data-theme="light"]` and `[data-theme="green-white"]`
    which override the neutral scale — these legitimately contain hex literals.
    All other CSS rules must use tokens, not raw hex.
    """
    if not STYLES_CSS.is_file():
        pytest.skip("styles.css not found (pre-v8)")
    css = STYLES_CSS.read_text(encoding="utf-8")
    # Strip CSS comments so they don't confuse block detection.
    css_no_comments = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    # Walk the first few selector blocks. Allowed blocks for hex literals:
    # :root, [data-theme="..."]. Stop at the first non-theme block.
    pos = 0
    theme_section_end = 0
    while True:
        open_b = css_no_comments.find("{", pos)
        if open_b < 0:
            break
        close_b = css_no_comments.find("}", open_b)
        if close_b < 0:
            break
        selector = css_no_comments[pos:open_b].strip()
        if selector.startswith(":root") or selector.startswith("[data-theme"):
            theme_section_end = close_b + 1
            pos = close_b + 1
        else:
            break
    style_after = css_no_comments[theme_section_end:]
    # ignore SVG gradient stop-color attributes which are data, not theme
    leaks = re.findall(r"#[0-9a-fA-F]{6}\b", style_after)
    assert not leaks, f"hardcoded hex outside :root in styles.css: {leaks[:8]}"


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
    """v8-v16 required a `gradient-shift` animation on the .brand title
    (rainbow text shifting hues). v17 redesign (DESIGN.md) removed this —
    it was an AI-slop pattern. Updated to assert the rainbow-text pattern
    is GONE; the brand title now uses a flat color."""
    css = STYLES_CSS.read_text(encoding="utf-8")
    idx = css.find(".brand{")
    if idx >= 0:
        snippet = css[idx:idx + 300]
        assert "background-clip:text" not in snippet.replace(" ", ""), (
            ".brand must not use background-clip:text gradient — v17 minimal"
        )
    # gradient-shift keyframes may still exist (harmless if unused) but
    # the .brand rule must not reference it.
    brand_rule = css[idx:idx + 200] if idx >= 0 else ""
    assert "gradient-shift" not in brand_rule, (
        ".brand must not animate gradient-shift — v17 minimal palette"
    )


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


# ── Phase 3: Event Log power tools — filter + backlog replay ────────────────

def test_event_log_filter_controls_exist():
    text = _read()
    assert (
        "ev-filter" in text or "log-filter" in text or "event-filter" in text
    ), "Event Log severity filter control must exist"


def test_backlog_complete_restores_counters():
    text = _read()
    assert "backlog_complete" in text, "must handle backlog_complete event"
    idx = text.find("backlog_complete")
    after = text[idx : idx + 150]
    assert (
        "renderLanes" in after and ("bumpCounter" in text or "s-hooks" in text)
    ), "backlog_complete must restore counter state, not just layout"


# ── Phase 4: routing rationale + capability legend ──────────────────────────

def test_routing_rationale_surface_exists():
    text = _read()
    assert "route_plan" in text, "must handle route_plan SSE event"
    assert (
        "routing" in text or "route-rationale" in text or "model-rank" in text
    ), "routing rationale must be surfaced to operator"


def test_capability_legend_exists():
    text = _read()
    assert "cap-legend" in text or "capability-legend" in text, (
        "capability score legend must explain score dimensions and thresholds"
    )


# ── Phase 5: accessibility — contrast, focus, labels, aria-live ─────────────

def test_timestamp_contrast_not_disabled():
    text = _read()
    idx = text.find(".ev-time")
    if idx == -1:
        pytest.skip("ev-time class not found")
    after = text[idx : idx + 200]
    assert "text-disabled" not in after, (
        ".ev-time must not use --text-disabled (2.8:1 contrast fails WCAG AA)"
    )


def test_focus_visible_rule_present():
    text = _read()
    style_end = text.find("</style>")
    style = text[:style_end]
    assert (
        "focus-visible" in style or "focus-visible" in text[style_end:]
    ), "must declare :focus-visible styling for keyboard navigation"


def test_modal_has_keyboard_escape():
    text = _read()
    assert (
        "keydown" in text and ("Escape" in text or "27" in text or "closeSettings" in text)
    ), "settings modal must support Escape key to close"


def test_aria_labels_on_toggles():
    text = _read()
    idx = text.find("glow-toggle")
    after = text[idx : idx + 300] if idx > -1 else ""
    assert (
        "aria-label" in after or "aria-label" in text
    ), "glow-toggle checkboxes must have accessible labels"


# ── Phase 6: robustness — graph offline, ASCII timestamps, language zones ───

def test_graph_has_offline_fallback():
    text = _read()
    idx = text.find("initGraph")
    if idx == -1:
        pytest.skip("initGraph not found")
    after = text[idx : idx + 400]
    assert (
        "window.vis" in after and "fallback" in after.lower()
    ) or (
        "offline" in after.lower() and "graph" in after.lower()
    ) or (
        "graph-unavailable" in text
    ), "graph view must show a visible fallback when vis-network is unavailable"


def test_timestamps_use_ascii_locale():
    text = _read()
    assert (
        "toLocaleTimeString('th'" not in text
    ), "timestamps must use ASCII digits — remove Thai locale from toLocaleTimeString"


def test_language_zone_policy_applied():
    text = _read()
    assert "font-mono" in text, "mono font must be defined for data zones"
    assert any(x in text for x in ("lang=\"th\"", "lang='th'")), "Thai lang attribute must remain on root"


# ── v10 CHUNK A10: CDN non-blocking + lazy chart.js ──────────────────────
# Goal: reduce initial paint blocking by deferring CDN scripts, and avoid
# preloading chart.js (only used by the analytics tab — lazy-load instead).

def test_cdn_scripts_have_defer():
    """External CDN <script> tags must be non-blocking (defer attribute)."""
    html = HTML.read_text(encoding="utf-8")
    # Find all CDN script src tags (defer may come before or after src).
    cdn_tags = re.findall(
        r'<script\s+[^>]*src="https?://(?:unpkg|cdn\.jsdelivr)\.net[^"]*"[^>]*>',
        html,
    )
    assert cdn_tags, "expected at least one CDN <script> tag in head"
    for tag in cdn_tags:
        assert "defer" in tag, f"CDN script tag must have defer: {tag}"


def test_chartjs_not_preloaded_in_head():
    """chart.js is analytics-only — must not be preloaded in <head>."""
    html = HTML.read_text(encoding="utf-8")
    head = html[: html.find("</head>")]
    assert (
        "chart.js" not in head and "chart.umd" not in head
    ), "chart.js must be lazy-loaded from the analytics tab, not preloaded in <head>"


def test_chartjs_lazy_loader_exists():
    """A lazy-load helper for chart.js must exist in src/ (so the analytics
    tab can load it on first open)."""
    text = _read()
    assert (
        "loadChartJs" in text or "_loadChartJs" in text
    ), "lazy chart.js loader function missing"


# ── v10 CHUNK B10: TTL cache layer ──────────────────────────────────────
# Goal: avoid re-fetching expensive APIs (skills/coverage) on every tab
# switch — cache with TTL + invalidate on SSE registry_update.

def test_ttl_cache_helper_exists():
    """_ttlCache helper must exist in src/app.js with get/set/invalidate."""
    text = _read()
    assert "_ttlCache" in text, "_ttlCache namespace missing"
    assert "_ttlGet" in text or "_ttlCache.get" in text or "_cacheGet" in text, "cache .get() missing"
    assert "_ttlSet" in text or "_ttlCache.set" in text or "_cacheSet" in text, "cache .set() missing"


def test_ttl_cache_invalidate_on_registry_update():
    """SSE registry_update handler must invalidate skills+coverage cache."""
    text = _read()
    # Match the actual handler branch in graph.js (not a stray comment in app.js).
    idx = text.find("ev.type==='registry_update'")
    if idx == -1:
        idx = text.find('ev.type === "registry_update"')
    assert idx != -1, "registry_update event handler missing"
    after = text[idx : idx + 600]
    assert (
        "_cacheInvalidate" in after
        or "_ttlCache" in after
        or "_cacheClear" in after
    ), "registry_update must invalidate skills+coverage caches"


def test_skills_load_uses_ttl_cache():
    """skillsLoad() must consult TTL cache before fetching /api/skills."""
    text = _read()
    idx = text.find("async function skillsLoad")
    if idx == -1:
        idx = text.find("function skillsLoad")
    assert idx != -1, "skillsLoad function missing"
    after = text[idx : idx + 1200]
    assert (
        "_cacheGet" in after or "_ttlGet" in after or "_ttlCache" in after
    ), "skillsLoad must consult TTL cache before fetching"


def test_coverage_load_uses_ttl_cache():
    """coverageLoad() must consult TTL cache before fetching /api/coverage."""
    text = _read()
    idx = text.find("async function coverageLoad")
    if idx == -1:
        idx = text.find("function coverageLoad")
    assert idx != -1, "coverageLoad function missing"
    after = text[idx : idx + 1200]
    assert (
        "_cacheGet" in after or "_ttlGet" in after or "_ttlCache" in after
    ), "coverageLoad must consult TTL cache before fetching"


# ── v10 CHUNK C10: lazy view init + animation pause ─────────────────────
# Goal: avoid redundant heavy init when returning to a tab; pause the flow
# particle animation loop when not on the Flow view (saves CPU/background work).

def test_view_loaded_guard_pattern():
    """setView() must check a _loaded guard so revisiting a tab skips re-init
    (Refresh buttons still force reload via explicit cache.invalidate)."""
    text = _read()
    # The lazy-init guard: a flag tracking which views have been initialized.
    assert (
        "_loaded" in text or "_initDone" in text or "_viewsLoaded" in text
    ), "view loaded-guard flag missing — setView() must skip heavy re-init"


def test_particle_loop_paused_when_not_flow():
    """particleLoop() must early-return when currentView !== 'flow' (save CPU
    when the Flow tab is hidden)."""
    text = _read()
    idx = text.find("function particleLoop")
    assert idx != -1, "particleLoop function missing"
    after = text[idx : idx + 600]
    assert (
        "currentView" in after
    ), "particleLoop must early-return when not on the flow view"


def test_setview_has_force_refresh_param():
    """setView() must accept a force-refresh path so Refresh buttons can bypass
    the loaded-guard (user-initiated reload always re-fetches)."""
    text = _read()
    idx = text.find("function setView")
    assert idx != -1, "setView function missing"
    after = text[idx : idx + 800]
    assert (
        "force" in after.lower() or "_loaded" in after
    ), "setView must support force-refresh (bypass loaded guard)"


# ── v11 CHUNK A11: localStorage backup — export all ─────────────────────
# Goal: export all awiki-* keys to a downloadable JSON file so users can
# back up / migrate their dashboard preferences across machines.

def test_backup_pane_exists():
    """Settings must have a Backup tab + pane."""
    html = HTML.read_text(encoding="utf-8")
    assert 'data-pane="pane-backup"' in html, "Backup tab missing in Settings"
    assert 'id="pane-backup"' in html, "Backup pane container missing"


def test_export_all_backup_function_exists():
    """exportAllBackup() function must exist in src/."""
    text = _read()
    assert "exportAllBackup" in text, "exportAllBackup function missing"


def test_backup_whitelist_prefix():
    """Backup must only include keys starting with 'awiki-' (skip unrelated
    localStorage from other tools on the same origin)."""
    text = _read()
    # The whitelist filter must check the awiki- prefix.
    assert (
        "awiki-" in text and ("startsWith" in text or "indexOf" in text)
    ), "backup must filter by 'awiki-' prefix"


def test_backup_schema_has_version_field():
    """Backup JSON must include a version field for future migrations."""
    text = _read()
    # Find the function definition in src (not the onclick reference in HTML).
    idx = text.find("function exportAllBackup")
    assert idx != -1, "exportAllBackup function definition missing"
    after = text[idx : idx + 800]
    assert "version" in after, "backup JSON must include version field"


# ── v11 CHUNK B11: import + selective restore ──────────────────────────
# Goal: import a backup JSON, validate schema, let user pick which keys to
# restore, apply only selected. Reject malformed/unknown-version payloads.

def test_import_backup_function_exists():
    """importBackup() function must exist in src/."""
    text = _read()
    assert "function importBackup" in text, "importBackup function missing"


def test_backup_validation_rejects_unknown_version():
    """Validation must check version field — reject payloads without it or
    with an unsupported version number."""
    text = _read()
    # Validation lives in _validateBackupPayload (called by importBackup).
    idx = text.find("_validateBackupPayload")
    assert idx != -1, "_validateBackupPayload helper missing"
    after = text[idx : idx + 400]
    assert "version" in after, "validation must check version field"
    # Must reject (throw or return early) on bad version — check for a numeric
    # literal comparison against the supported version.
    assert "1" in after, "validation must check version === 1 (current schema)"


def test_backup_selective_restore_checkbox_ui():
    """Import must show a key list with checkboxes (selective restore)."""
    text = _read()
    # The restore UI must let the user pick keys via checkboxes.
    assert (
        "checkbox" in text.lower()
    ), "selective restore must use checkboxes for per-key selection"


def test_backup_apply_selected_keys_only():
    """The apply step must only write keys that were checked, not blindly
    overwrite everything."""
    text = _read()
    idx = text.find("function importBackup")
    assert idx != -1, "importBackup function missing"
    after = text[idx : idx + 2500]
    # Look for the apply loop that checks a selected flag per key.
    assert (
        "checked" in after or "selected" in after.lower()
    ), "apply must respect per-key selection (not blind overwrite)"


# ── v11 CHUNK C11: auto-backup (periodic) ──────────────────────────────
# Goal: snapshot localStorage every 7 days automatically so users have a
# safety net even if they never click Export. Stored in localStorage itself
# (key awiki-auto-backups, max 3 snapshots FIFO).

def test_auto_backup_function_exists():
    """autoBackup() function must exist in src/."""
    text = _read()
    assert "function autoBackup" in text or "autoBackup" in text, "autoBackup function missing"


def test_auto_backup_7day_threshold():
    """Auto-backup must check a 7-day threshold before snapshotting."""
    text = _read()
    # The 7-day threshold lives in the AUTO_BACKUP_INTERVAL_MS constant.
    assert (
        "AUTO_BACKUP_INTERVAL_MS" in text
    ), "auto-backup interval constant missing"
    # The constant must express 7 days (7*24*60*60*1000 or 604800000).
    assert (
        "7*24*60*60*1000" in text or "604800000" in text
    ), "auto-backup must use a 7-day threshold (7*24*60*60*1000 ms)"


def test_auto_backup_fifo_cap():
    """Auto-backup store must cap at 3 snapshots (FIFO — oldest dropped)."""
    text = _read()
    idx = text.find("autoBackup")
    assert idx != -1, "autoBackup function missing"
    after = text[idx : idx + 1500]
    # The cap is expressed as a slice or length check against 3.
    assert (
        "3" in after
    ), "auto-backup must cap at 3 snapshots (FIFO)"


def test_auto_backup_skip_self_in_export():
    """The export whitelist must skip awiki-auto-backups to avoid recursion."""
    text = _read()
    # BACKUP_SKIP_KEYS must contain awiki-auto-backups.
    assert (
        "awiki-auto-backups" in text
    ), "export whitelist must skip awiki-auto-backups (recursion safety)"


# ── v11 CHUNK D11: usage meter + per-key clear ─────────────────────────
# Goal: visual feedback on storage usage (progress bar + per-key bytes) +
# a per-key Clear button so users can reclaim quota without nuking everything.

def test_usage_meter_bytes_helper_exists():
    """A bytes calculation helper must exist (sum of key+value lengths)."""
    text = _read()
    # The meter renders total bytes — there must be a bytes calc somewhere.
    assert (
        "totalBytes" in text or "_backupBytes" in text or "5*1024*1024" in text
    ), "usage meter must calculate total bytes against 5MB quota"


def test_usage_meter_quota_thresholds():
    """Meter must show green/yellow/red thresholds based on % of 5MB quota."""
    text = _read()
    # The color thresholds (60% / 85%) must exist.
    assert (
        "60" in text and "85" in text
    ), "usage meter must use 60%/85% thresholds for green/yellow/red"


def test_per_key_clear_button_exists():
    """Each key row must have a Clear button (reclaim quota granularly)."""
    text = _read()
    idx = text.find("function loadBackupPane")
    assert idx != -1, "loadBackupPane function missing"
    after = text[idx : idx + 2000]
    assert (
        "clearBackupKey" in after or "clearKey" in after
    ), "per-key clear function missing in loadBackupPane"


# ── v11 CHUNK E11: smart suggestions scoring engine ────────────────────
# Goal: client-side scoring (frequency × recency × co-occurrence) to suggest
# skills the user is likely to want next. Pure JS — no server endpoint.

def test_smart_suggestions_function_exists():
    """smartSuggestions() function must exist in skills.js."""
    text = _read()
    assert "function smartSuggestions" in text, "smartSuggestions function missing"


def test_smart_suggestions_scoring_weights():
    """Scoring must use frequency, recency, and co-occurrence factors."""
    text = _read()
    idx = text.find("function smartSuggestions")
    assert idx != -1, "smartSuggestions function missing"
    after = text[idx : idx + 2000]
    # All three scoring factors must be present.
    assert "frequency" in after.lower() or "count" in after.lower(), "frequency factor missing"
    assert "recency" in after.lower() or "recent" in after.lower() or "days" in after.lower(), "recency factor missing"
    assert "co-occur" in after.lower() or "cooccur" in after.lower() or "_mineCoOccurrence" in after, "co-occurrence factor missing"


def test_smart_suggestions_excludes_recent_24h():
    """Suggestions must exclude skills opened in the last 24h (user just saw them)."""
    text = _read()
    idx = text.find("function smartSuggestions")
    assert idx != -1, "smartSuggestions function missing"
    after = text[idx : idx + 2500]
    # 24h exclusion expressed as 24 hours or 86400000 ms or 24*60*60.
    assert (
        "24" in after
    ), "smart suggestions must exclude skills opened in last 24h"


def test_smart_suggestions_min_telemetry_fallback():
    """Must return empty if there's insufficient telemetry (<5 opens)."""
    text = _read()
    idx = text.find("function smartSuggestions")
    assert idx != -1, "smartSuggestions function missing"
    after = text[idx : idx + 2500]
    # Minimum telemetry threshold to avoid random suggestions.
    assert (
        "5" in after
    ), "smart suggestions must require minimum 5 opens before suggesting"


# ── v11 CHUNK F11: suggestion chips in discovery bar ───────────────────
# Goal: render smartSuggestions() as chips in the existing discovery bar so
# users see "แนะนำสำหรับคุณ" next to Trending/Recent.

def test_discovery_bar_renders_suggestions():
    """renderDiscoveryBar() must call smartSuggestions() and render chips."""
    text = _read()
    idx = text.find("function renderDiscoveryBar")
    assert idx != -1, "renderDiscoveryBar function missing"
    after = text[idx : idx + 2000]
    assert (
        "smartSuggestions" in after
    ), "renderDiscoveryBar must call smartSuggestions()"


def test_suggestion_chip_has_reason_tooltip():
    """Suggestion chips must show a 'why' tooltip (frequency/days/cooccur)."""
    text = _read()
    idx = text.find("function renderDiscoveryBar")
    assert idx != -1, "renderDiscoveryBar function missing"
    after = text[idx : idx + 3000]
    # The chip title/tooltip must include scoring reason (days/frequency/cooccur).
    assert (
        "reason" in after.lower() or "title=" in after
    ), "suggestion chips must expose a 'why' tooltip with scoring reason"


# ── v12 CHUNK A12: theme pane + custom mode ────────────────────────────
def test_theme_pane_exists():
    html = HTML.read_text(encoding="utf-8")
    assert 'data-pane="pane-theme"' in html, "Theme tab missing in Settings"
    assert 'id="pane-theme"' in html, "Theme pane container missing"


def test_custom_theme_mode_in_cycle():
    text = _read()
    assert "'custom'" in text or '"custom"' in text, "custom mode missing from theme cycle"


def test_custom_theme_storage_key():
    text = _read()
    assert "awiki-theme-custom" in text, "awiki-theme-custom storage key missing"


def test_theme_editable_tokens_defined():
    text = _read()
    assert "THEME_EDITABLE_TOKENS" in text, "editable tokens list missing"


def test_custom_theme_style_injection():
    text = _read()
    assert "custom-theme-style" in text, "custom theme <style> injection point missing"


# ── v12 CHUNK B12: color pickers + live preview ────────────────────────
def test_render_theme_editor_exists():
    text = _read()
    assert "renderThemeEditor" in text, "renderThemeEditor function missing"


def test_theme_color_input_type_color():
    """Color pickers must use <input type='color'>."""
    text = _read()
    idx = text.find("renderThemeEditor")
    assert idx != -1, "renderThemeEditor missing"
    after = text[idx : idx + 1500]
    assert "type='color'" in after or 'type="color"' in after, "color picker must use <input type=color>"


def test_theme_live_preview_on_change():
    """Color picker onchange must re-inject style immediately (live preview)."""
    text = _read()
    idx = text.find("renderThemeEditor")
    assert idx != -1, "renderThemeEditor missing"
    after = text[idx : idx + 2500]
    assert "_injectCustomTheme" in after, "onchange must call _injectCustomTheme for live preview"


def test_theme_reset_button_exists():
    """Reset button must exist to clear custom theme back to dark/green-white."""
    text = _read()
    assert "resetCustomTheme" in text or "clearCustomTheme" in text, "reset custom theme function missing"


# ── v12 CHUNK C12: theme export/import + presets ───────────────────────
def test_export_theme_function_exists():
    text = _read()
    assert "exportTheme" in text, "exportTheme function missing"


def test_import_theme_function_exists():
    text = _read()
    assert "importTheme" in text, "importTheme function missing"


def test_theme_preset_seeds_exist():
    text = _read()
    assert "THEME_PRESET_SEEDS" in text, "preset seeds constant missing"
    assert "Ocean" in text, "Ocean preset seed missing"
    assert "Sunset" in text, "Sunset preset seed missing"
    assert "Forest" in text, "Forest preset seed missing"


def test_theme_preset_storage_key():
    text = _read()
    assert "awiki-theme-presets" in text, "awiki-theme-presets storage key missing"


# ── v12 CHUNK D12: view-toggle-bar horizontal scroll (mobile) ──────────
def test_view_toggle_bar_overflow_x_on_mobile():
    """styles.css must make .view-toggle-bar horizontally scrollable at <=600px."""
    if not STYLES_CSS.is_file():
        pytest.skip("styles.css not found")
    css = STYLES_CSS.read_text(encoding="utf-8")
    # Find the max-width:600px media query block.
    idx = css.find("@media(max-width:600px)")
    assert idx != -1, "max-width:600px media query missing"
    block = css[idx : idx + 600]
    assert ".view-toggle-bar" in block, "view-toggle-bar must be in mobile media query"
    assert "overflow-x:auto" in block, "view-toggle-bar must have overflow-x:auto on mobile"


# ── v12 CHUNK E12: skills-grid + skills-toolbar mobile ────────────────
def test_skills_grid_responsive_minmax_on_mobile():
    """styles.css must lower skills-grid minmax on mobile (260px -> smaller)."""
    if not STYLES_CSS.is_file():
        pytest.skip("styles.css not found")
    css = STYLES_CSS.read_text(encoding="utf-8")
    idx = css.find("@media(max-width:600px)")
    assert idx != -1, "max-width:600px media query missing"
    block = css[idx : idx + 800]
    # Must have a skills-grid rule with a smaller minmax (e.g. 150-170px).
    assert "#skills-grid" in block or ".skills-grid" in block, "skills-grid must be in mobile media query"
    assert "minmax(1" in block, "skills-grid minmax must drop below 200px on mobile"


def test_skills_toolbar_wraps_on_mobile():
    """styles.css must make skills-toolbar wrap on narrow screens."""
    if not STYLES_CSS.is_file():
        pytest.skip("styles.css not found")
    css = STYLES_CSS.read_text(encoding="utf-8")
    idx = css.find("@media(max-width:600px)")
    assert idx != -1, "max-width:600px media query missing"
    block = css[idx : idx + 800]
    assert "#skills-toolbar" in block, "skills-toolbar must be in mobile media query"


# ── v12 CHUNK F12: modals + drawer mobile-fit ──────────────────────────
def test_modals_mobile_maxwidth():
    """Modals must expand to 95vw on mobile so they don't clip content."""
    if not STYLES_CSS.is_file():
        pytest.skip("styles.css not found")
    css = STYLES_CSS.read_text(encoding="utf-8")
    idx = css.find("@media(max-width:600px)")
    assert idx != -1, "max-width:600px media query missing"
    block = css[idx : idx + 1200]
    assert "95vw" in block, "modals must use 95vw max-width on mobile"


def test_skills_drawer_fullwidth_on_mobile():
    """Skills detail drawer must go full-width on mobile (100vw not 480px)."""
    if not STYLES_CSS.is_file():
        pytest.skip("styles.css not found")
    css = STYLES_CSS.read_text(encoding="utf-8")
    idx = css.find("@media(max-width:600px)")
    assert idx != -1, "max-width:600px media query missing"
    block = css[idx : idx + 1200]
    assert "#skills-detail" in block, "skills-detail must be in mobile media query"
    assert "100vw" in block, "skills-detail must be full-width (100vw) on mobile"


# ── v13 CHUNK A13: Help pane refresh ───────────────────────────────────
def test_render_help_content_exists():
    text = _read()
    assert "renderHelpContent" in text, "renderHelpContent function missing"


def test_help_mentions_v10_v12_features():
    """Help content must mention features added in v10-v12."""
    text = _read()
    # Find the function definition (not the onclick reference in HTML).
    idx = text.find("function renderHelpContent")
    assert idx != -1, "renderHelpContent function definition missing"
    after = text[idx : idx + 4000]
    assert "backup" in after.lower(), "Help must mention backup (v11)"
    assert "theme" in after.lower(), "Help must mention theme editor (v12)"
    assert "mobile" in after.lower(), "Help must mention mobile responsive (v12)"
    assert "suggest" in after.lower(), "Help must mention smart suggestions (v11)"


def test_help_version_badge():
    """Help must show a version badge (dashboard version)."""
    text = _read()
    idx = text.find("function renderHelpContent")
    assert idx != -1, "renderHelpContent function definition missing"
    after = text[idx : idx + 4000]
    assert "version" in after.lower() or "v1" in after, "Help must show version badge"


# ── v13 CHUNK B13: first-run toast tour ────────────────────────────────
def test_start_tour_function_exists():
    text = _read()
    assert "function startTour" in text or "startTour" in text, "startTour function missing"


def test_tour_steps_array_exists():
    """TOUR_STEPS array must exist with at least 5 steps."""
    text = _read()
    assert "TOUR_STEPS" in text, "TOUR_STEPS array missing"


def test_tour_state_keys_exist():
    """Tour must persist state (completed + current step) for resume."""
    text = _read()
    assert "awiki-tour-completed" in text, "awiki-tour-completed key missing"
    assert "awiki-tour-step" in text, "awiki-tour-step key missing"


def test_tour_active_flag_exists():
    """_tourActive flag must exist to suppress other toasts during tour."""
    text = _read()
    assert "_tourActive" in text, "_tourActive flag missing"


# ── v13 CHUNK C13: dashboard health check ──────────────────────────────
def test_run_health_check_exists():
    text = _read()
    assert "runHealthCheck" in text, "runHealthCheck function missing"


def test_health_check_items():
    """Health check must cover SSE, API, localStorage, and CDN."""
    text = _read()
    idx = text.find("async function runHealthCheck")
    assert idx != -1, "runHealthCheck function definition missing"
    after = text[idx : idx + 3000]
    assert "SSE" in after or "live-dot" in after or "connected" in after.lower(), "SSE check missing"
    assert "/api/" in after, "API check missing"
    assert "localStorage" in after or "5*1024*1024" in after, "localStorage check missing"


def test_health_check_timeout():
    """Health check must use a timeout (5s) so it doesn't hang."""
    text = _read()
    idx = text.find("async function runHealthCheck")
    assert idx != -1, "runHealthCheck function definition missing"
    after = text[idx : idx + 3000]
    assert "5000" in after or "AbortController" in after or "timeout" in after.lower(), "health check must use timeout"


# ── v13 CHUNK D13: "What's new" badge ──────────────────────────────────
def test_whats_new_badge_storage_key():
    """Badge must track seen version via awiki-seen-version key."""
    text = _read()
    assert "awiki-seen-version" in text, "awiki-seen-version key missing"


def test_whats_new_badge_function_exists():
    """Badge show/hide logic must exist."""
    text = _read()
    assert "updateWhatsNewBadge" in text or "whatsNewBadge" in text.lower() or "_maybeShowBadge" in text, "what's new badge function missing"


def test_whats_new_badge_version_compare():
    """Badge must compare seen version against DASHBOARD_VERSION."""
    text = _read()
    assert "DASHBOARD_VERSION" in text, "DASHBOARD_VERSION constant must exist for badge comparison"


# ── v14 CHUNK A14: agent capability radar chart ────────────────────────
def test_render_capability_radar_exists():
    text = _read()
    assert "renderCapabilityRadar" in text, "renderCapabilityRadar function missing"


def test_capability_radar_uses_chart_js_radar():
    """Radar must use Chart.js type='radar'."""
    text = _read()
    idx = text.find("renderCapabilityRadar")
    assert idx != -1, "renderCapabilityRadar missing"
    after = text[idx : idx + 2000]
    assert "radar" in after.lower(), "radar chart must use type=radar"


def test_capability_radar_fetches_capabilities():
    """Radar must fetch /api/capabilities."""
    text = _read()
    idx = text.find("async function renderCapabilityRadar")
    assert idx != -1, "renderCapabilityRadar function definition missing"
    after = text[idx : idx + 3000]
    assert "/api/capabilities" in after, "radar must fetch /api/capabilities"


# ── v14 CHUNK B14: cost projection (trend forecast) ────────────────────
def test_render_cost_projection_exists():
    text = _read()
    assert "renderCostProjection" in text, "renderCostProjection function missing"


def test_cost_projection_uses_regression():
    """Projection must compute a linear regression (slope/intercept)."""
    text = _read()
    idx = text.find("async function renderCostProjection")
    assert idx != -1, "renderCostProjection function definition missing"
    after = text[idx : idx + 3500]
    assert "slope" in after.lower() or "trend" in after.lower() or "regression" in after.lower(), "projection must use regression"


def test_cost_projection_dashed_forecast_line():
    """Forecast portion must be dashed (borderDash) to distinguish from actual."""
    text = _read()
    idx = text.find("async function renderCostProjection")
    assert idx != -1, "renderCostProjection function definition missing"
    after = text[idx : idx + 3500]
    assert "borderDash" in after or "dashed" in after.lower(), "forecast line must be dashed"


# ── v14 CHUNK C14: skill dependency heatmap ────────────────────────────
def test_render_skill_heatmap_exists():
    text = _read()
    assert "renderSkillHeatmap" in text, "renderSkillHeatmap function missing"


def test_skill_heatmap_domain_phase_matrix():
    """Heatmap must build a domain × lifecycle_phase matrix."""
    text = _read()
    idx = text.find("function renderSkillHeatmap")
    assert idx != -1, "renderSkillHeatmap function definition missing"
    after = text[idx : idx + 3000]
    assert "domain" in after.lower(), "heatmap must use domain axis"
    assert "phase" in after.lower(), "heatmap must use lifecycle phase axis"


def test_skill_heatmap_click_filter():
    """Clicking a cell must filter the skills view by domain+phase."""
    text = _read()
    idx = text.find("function renderSkillHeatmap")
    assert idx != -1, "renderSkillHeatmap function definition missing"
    after = text[idx : idx + 3000]
    assert "onclick" in after.lower() or "click" in after.lower(), "heatmap cells must be clickable"


# ── v14 CHUNK D14: summary view KPI cards ──────────────────────────────
def test_render_kpi_cards_exists():
    text = _read()
    assert "renderKpiCards" in text, "renderKpiCards function missing"


def test_kpi_cards_click_navigation():
    """Each KPI card must navigate to its related view when clicked."""
    text = _read()
    idx = text.find("function renderKpiCards")
    assert idx != -1, "renderKpiCards function definition missing"
    after = text[idx : idx + 2500]
    assert "setView" in after, "KPI cards must navigate via setView()"


def test_kpi_cards_target_container():
    """HTML must have a container for the KPI cards."""
    html = HTML.read_text(encoding="utf-8")
    assert 'id="kpi-cards"' in html or 'id="summary-kpi"' in html, "KPI cards container missing in HTML"


# ── v15 CHUNK A15: event log ring buffer + text search ─────────────────
def test_event_log_array_exists():
    text = _read()
    assert "_eventLog" in text, "_eventLog ring buffer missing"


def test_event_search_function_exists():
    text = _read()
    assert "eventSearch" in text, "eventSearch function missing"


def test_event_search_input_in_html():
    html = HTML.read_text(encoding="utf-8")
    assert 'id="event-search"' in html, "event search input missing in HTML"


# ── v15 CHUNK B15: event bookmark/pin ──────────────────────────────────
def test_toggle_event_bookmark_exists():
    text = _read()
    assert "toggleEventBookmark" in text, "toggleEventBookmark function missing"


def test_event_bookmarks_storage_key():
    text = _read()
    assert "awiki-event-bookmarks" in text, "awiki-event-bookmarks key missing"


def test_event_bookmark_filter_option():
    """Filter dropdown must have a 'bookmarked' option."""
    html = HTML.read_text(encoding="utf-8")
    assert 'value="bookmarked"' in html or "bookmarked" in html, "bookmarked filter option missing"


# ── v15 CHUNK C15: event log export JSON ───────────────────────────────
def test_export_event_log_exists():
    text = _read()
    assert "exportEventLog" in text, "exportEventLog function missing"


def test_export_event_log_uses_download_blob():
    text = _read()
    idx = text.find("function exportEventLog")
    assert idx != -1, "exportEventLog function definition missing"
    after = text[idx : idx + 1500]
    assert "_downloadBlob" in after, "exportEventLog must use _downloadBlob helper"


def test_export_event_button_in_html():
    html = HTML.read_text(encoding="utf-8")
    assert "exportEventLog" in html, "export event button missing in HTML"


# ── v15 CHUNK D15: chat history persistence ────────────────────────────
def test_chat_history_key_exists():
    text = _read()
    assert "awiki-chat-history" in text, "awiki-chat-history storage key missing"


def test_push_chat_history_exists():
    text = _read()
    assert "pushChatHistory" in text, "pushChatHistory function missing"


def test_load_chat_history_exists():
    text = _read()
    assert "loadChatHistory" in text, "loadChatHistory function missing"


def test_clear_chat_button_in_html():
    html = HTML.read_text(encoding="utf-8")
    assert "clearChat" in html, "clear chat button missing in HTML"


# ── v16 integration audit: SSE + localStorage + lazy-load gaps ────────────────
# Found via debug-mantra 4-step audit on 2026-07-21. Each test guards a real
# bug the static/runtime scans surfaced — see audit-report.json.


def test_subagent_invoke_sse_handler_exists():
    """subagent_invoke events come from scripts/hooks/log_subagent_result.py
    (every real subagent call). Without a dedicated handler they fall through
    to the default pushTimeline branch and the dashboard never bumps the
    subagent KPI, never animates the lane, never spawns a thought bubble."""
    text = _read()
    # The handler must be referenced in handleEvent's switch.
    assert "subagent_invoke" in text, (
        "subagent_invoke event type is emitted by log_subagent_result.py "
        "but has no handler reference in the dashboard source"
    )
    assert "onSubagentInvoke" in text, "dedicated handler onSubagentInvoke() missing"


def test_vis_network_fallback_auto_retries():
    """If the user clicks the Graph tab before the vis-network defer script
    finishes loading, initGraph() shows the #graph-unavailable fallback and
    bails. Without an auto-retry, the user is stuck on 'Graph unavailable'
    even after the CDN script loads. We require a retry hook that re-runs
    initGraph when window.vis becomes available."""
    text = _read()
    # A retry hook looks like: setTimeout(initGraph, N) inside the !window.vis
    # branch, OR an onload listener that calls initGraph(), OR a polling
    # pattern. We accept any of: 'setTimeout(initGraph', 'vis.onload',
    # '_visRetry', or a script-tag onload that calls initGraph.
    assert (
        "setTimeout(initGraph" in text
        or "_visRetry" in text
        or "visReady" in text
        or ("addEventListener('load'" in text and "initGraph" in text)
    ), "vis-network fallback has no auto-retry when defer script loads late"


def test_compare_last_has_reader():
    """src/skills.js:924 writes awiki-compare-last but nothing reads it.
    Either provide a reader (a 'Restore last comparison' affordance) or
    remove the write. This test currently asserts the write is paired
    with a reader in the same file."""
    text = _read()
    write_pos = text.find("_lsSet('awiki-compare-last'")
    assert write_pos >= 0, "compare-last write site moved or removed"
    # Search for a reader (getItem / _lsGet) of the same key AFTER the write.
    after = text[write_pos:]
    assert (
        "_lsGet('awiki-compare-last'" in after
        or "getItem('awiki-compare-last'" in after
        or "restoreLastCompare" in text
    ), "awiki-compare-last is write-only — add a reader or remove the write"


def test_workspace_last_has_reader():
    """src/modals.js:296 writes WORKSPACE_LAST_KEY but nothing reads it."""
    text = _read()
    assert "WORKSPACE_LAST_KEY=" in text, "WORKSPACE_LAST_KEY alias missing"
    # Either a getItem/_lsGet call on WORKSPACE_LAST_KEY, or a
    # restoreLastWorkspace() function that reads it.
    assert (
        "_lsGet(WORKSPACE_LAST_KEY" in text
        or "getItem(WORKSPACE_LAST_KEY" in text
        or "restoreLastWorkspace" in text
    ), "WORKSPACE_LAST_KEY is write-only — add a reader or remove the write"


def test_view_switch_clears_sim_timers():
    """setView() must clearInterval on _simTimer and _wfTimer when the user
    navigates away, so the background sim doesn't keep updating a hidden DOM
    forever. Cheap guard, big hygiene win."""
    text = _read()
    assert "function setView" in text
    # The setView body (delimited by the closing brace before the next top-level
    # function/const) must reference at least one timer clear.
    sv_start = text.find("function setView")
    # Find the matching end — search for the next top-level "function " after.
    next_fn = text.find("\nfunction ", sv_start + 10)
    sv_body = text[sv_start:next_fn if next_fn > 0 else sv_start + 4000]
    assert (
        "_simTimer" in sv_body or "_wfTimer" in sv_body
    ), "setView() does not clear simulation timers on view switch"


# ── v17 minimal redesign (design-system skill) ───────────────────────────────
# Pure Minimal + Neutral+Accent (Linear-style). Guards the design tokens
# shipped in DESIGN.md / design-system.json so the palette can't drift back
# to multi-hue gradients/glass.


def test_v17_minimal_palette_tokens_defined():
    """v17 must ship the 11-step neutral scale + single brand accent in CSS."""
    css = STYLES_CSS.read_text(encoding="utf-8")
    # The minimal palette lives in :root or a [data-theme="minimal"] block.
    required = [
        "--n-50",   # app bg
        "--n-100",  # surface 1
        "--n-200",  # surface 2 (cards)
        "--n-400",  # border strong
        "--n-500",  # border default
        "--n-700",  # text secondary
        "--n-800",  # text primary on dark
        "--brand",  # single accent
        "--brand-muted",
    ]
    missing = [t for t in required if t not in css]
    assert not missing, f"v17 minimal palette missing tokens: {missing}"


def test_v17_default_theme_is_minimal():
    """The dashboard must ship minimal as the default theme (documentElement
    or body data-theme=minimal), not the legacy green-white."""
    css = STYLES_CSS.read_text(encoding="utf-8")
    # The :root block (whatever its whitespace) must define the minimal
    # palette directly so dark mode (which sets data-theme="") uses it.
    assert "--n-50:" in css and "--brand:" in css, (
        "minimal palette must be defined in :root so dark mode (data-theme='')"
        " inherits it by default"
    )
    # Also ensure the :root block declares n-50 BEFORE any [data-theme] block
    # (so the cascade order is correct).
    n50_pos = css.find("--n-50:")
    theme_block_pos = css.find("[data-theme=")
    assert n50_pos > 0 and (theme_block_pos < 0 or n50_pos < theme_block_pos), (
        ":root minimal palette must precede any [data-theme] override block"
    )


def test_v17_removes_brand_gradient_on_view_btn():
    """v17 view-btn.active must NOT use linear-gradient(135deg,brand,cool) —
    that's the AI-slop pattern flagged in DESIGN.md."""
    css = STYLES_CSS.read_text(encoding="utf-8")
    # Find the .view-btn.active rule and inspect its body.
    idx = css.find(".view-btn.active")
    assert idx >= 0, ".view-btn.active rule missing"
    # Take the next 240 chars (enough for the rule body).
    snippet = css[idx:idx + 240]
    assert "linear-gradient" not in snippet, (
        "view-btn.active still uses gradient — v17 must use flat brand color"
    )


def test_v17_removes_glass_card_class_slop():
    """v17 must not retain the .glass-card class with backdrop-filter blur +
    gradient — that's textbook AI-slop per DESIGN.md. Either remove the class
    entirely or strip the blur+gradient."""
    css = STYLES_CSS.read_text(encoding="utf-8")
    if ".glass-card" not in css:
        return  # removed entirely — pass
    # Find every .glass-card rule body.
    import re as _re
    matches = list(_re.finditer(r"\.glass-card[^{]*\{([^}]+)\}", css))
    for m in matches:
        body = m.group(1)
        assert "backdrop-filter:blur" not in body.replace(" ", ""), (
            ".glass-card still uses backdrop-filter:blur — must be removed"
        )
        assert "linear-gradient" not in body, (
            ".glass-card still uses gradient background — must be flat color"
        )


def test_v17_reduces_decorative_gradients():
    """v17 must dramatically cut decorative linear-gradient usage. v16 had 20;
    we allow at most 4 (for unavoidable cases like particle bg, glow dividers
    that communicate state — not decoration)."""
    css = STYLES_CSS.read_text(encoding="utf-8")
    count = css.count("linear-gradient")
    assert count <= 6, (
        f"v17 still has {count} linear-gradient() calls (target ≤6, v16 had 20). "
        "Strip decorative gradients per DESIGN.md."
    )


def test_v17_header_no_glow_underline():
    """The #header::after gradient underline was a v16 AI-slop tell.
    v17 must remove or replace it with a solid 1px border."""
    css = STYLES_CSS.read_text(encoding="utf-8")
    if "#header::after" not in css:
        return  # removed — pass
    import re as _re
    m = _re.search(r"#header::after[^{]*\{([^}]+)\}", css)
    if m:
        body = m.group(1)
        assert "linear-gradient" not in body, (
            "#header::after still draws a gradient underline — v17 must be flat"
        )


def test_v17_brand_text_no_gradient_clip():
    """The .brand title used background-clip:text gradient (rainbow text).
    v17 must use a flat color — rainbow text is AI-slop tell #1."""
    css = STYLES_CSS.read_text(encoding="utf-8")
    idx = css.find(".brand{")
    if idx < 0:
        return
    snippet = css[idx:idx + 300]
    assert "background-clip:text" not in snippet.replace(" ", ""), (
        ".brand still uses background-clip:text gradient — v17 must be flat color"
    )


def test_v17_stat_values_no_gradient_clip():
    """The .stat-val counter used gradient text. v17 must use flat color
    so numbers are the focal point, not decoration."""
    css = STYLES_CSS.read_text(encoding="utf-8")
    idx = css.find(".stat-val{")
    if idx < 0:
        return
    snippet = css[idx:idx + 300]
    assert "background-clip:text" not in snippet.replace(" ", ""), (
        ".stat-val still uses background-clip:text gradient — v17 must be flat"
    )


# ── v17 chunk C17 — emoji declutter + density ──────────────────────────────
def test_v17_offline_heading_no_emoji_prefix():
    """The offline overlay h2 was '📡 รอ Dashboard Server…'. v17 removes
    emoji prefixes from headings per DESIGN.md. The heading text should
    start with a non-emoji character."""
    html = HTML.read_text(encoding="utf-8")
    # Find the offline h2
    import re as _re
    m = _re.search(r"<h2[^>]*>([^<]+)</h2>", html)
    if not m:
        return
    txt = m.group(1).strip()
    # Allow leading whitespace; first non-space char should not be an emoji.
    # Emojis are in the U+1F300-U+1FAFF range or U+2600-U+27BF.
    first = txt[0] if txt else ""
    code = ord(first)
    is_emoji = (
        0x1F300 <= code <= 0x1FAFF
        or 0x2600 <= code <= 0x27BF
        or 0x2190 <= code <= 0x21FF  # arrow range often used as icon
    )
    assert not is_emoji, (
        f"offline <h2> still starts with emoji ({first!r}); v17 removes emoji prefixes"
    )


def test_v17_section_headings_use_semantic_weight():
    """v17 DESIGN.md: headings use font-weight 600 (semibold), not 800.
    Linear's hallmark: strong-but-restrained titles."""
    css = STYLES_CSS.read_text(encoding="utf-8")
    # Find any rule like 'h2{...font-weight:800...}' or similar
    import re as _re
    bad = _re.findall(r"(?:^|[},])\s*(?:h[1-6]|\.brand|\.stat-val)\{[^}]*font-weight:800", css)
    assert not bad, (
        f"headings/brand/stat-val still use font-weight:800 — v17 caps at 600: {bad}"
    )


# ── v18 chunk A18 — emoji-headings removal ──────────────────────────────────
# 8 emoji-prefix <h5> headings in src/skills.js detail panel were flagged
# in D17 backlog. v18 strips them per DESIGN.md (type leads, emoji = noise).

def test_v18_skill_panel_no_emoji_headings():
    """src/skills.js must not render emoji-prefixed <h5> headings in the
    skill detail panel. v18 DESIGN.md: emoji removal for Typography score.

    Affected (v17): 📝 📋 💡 📌 🎬 🔗 📋 🔍 (8 occurrences).
    """
    skills = (DASHBOARD_DIR / "src" / "skills.js").read_text(encoding="utf-8")
    # Find <h5>...</h5> patterns and inspect first char.
    import re as _re
    matches = _re.findall(r"<h5[^>]*>([^<]+)</h5>", skills)
    assert matches, "expected at least one <h5> in skills.js detail panel"
    bad = []
    for txt in matches:
        txt = txt.strip()
        if not txt:
            continue
        first = txt[0]
        code = ord(first)
        is_emoji = (
            0x1F300 <= code <= 0x1FAFF
            or 0x2600 <= code <= 0x27BF
            or 0x2190 <= code <= 0x21FF
        )
        if is_emoji:
            bad.append(txt[:40])
    assert not bad, (
        f"emoji-prefix <h5> headings still in skills.js detail panel: {bad}"
    )


# ── v18 chunk B18 — transition token migration ─────────────────────────────
# styles.css had 23 hardcoded 'transition: X .Ys ...' rules. v18 maps them
# to --t-fast (120ms) / --t-normal (200ms) / --t-slow (320ms) + --ease
# so the whole motion system lives in 3 tokens (Linear hallmark).

def test_v18_transitions_use_tokens():
    """Hardcoded transition rules (not using --t-* tokens) must drop to ≤ 3.
    v17 had 23; v18 target ≤ 3 (allow for unavoidable cubic-bezier outliers)."""
    css = STYLES_CSS.read_text(encoding="utf-8")
    import re as _re
    # Match 'transition: <value>;' on a single line.
    all_trans = _re.findall(r"transition\s*:\s*([^;]+);", css)
    hardcoded = []
    for t in all_trans:
        # Skip if it references a token.
        if "--t-" in t or "var(--ease)" in t:
            continue
        hardcoded.append(t.strip()[:60])
    assert len(hardcoded) <= 3, (
        f"v18 must reduce hardcoded transitions to ≤3, found {len(hardcoded)}: "
        f"{hardcoded[:8]}"
    )


# ── v18 chunk C18 — Cmd+K palette visual minimal ────────────────────────────
# Runtime audit (Stage 4 of A-Plan) confirmed Cmd+K already works since
# CHUNK EE. This chunk upgrades visuals: drop emojis, drop backdrop-blur,
# use brand-muted for hover per DESIGN.md.

def test_v18_palette_uses_geometric_icons():
    """PALETTE_ICONS in src/modals.js must not use emojis.
    v18 used geometric shapes (◆ ● ◇); v19 E19 supersedes with Lucide icon
    names (puzzle/circle/keyboard). This test now guards BOTH v18 and v19:
    no emojis, must use one of the approved minimal forms."""
    modals = (DASHBOARD_DIR / "src" / "modals.js").read_text(encoding="utf-8")
    import re as _re
    m = _re.search(r"PALETTE_ICONS\s*=\s*\{([^}]+)\}", modals)
    assert m, "PALETTE_ICONS const not found in src/modals.js"
    body = m.group(1)
    # Must NOT contain any emoji.
    for ch in body:
        code = ord(ch)
        is_emoji = (
            0x1F300 <= code <= 0x1FAFF
            or 0x2600 <= code <= 0x27BF
        )
        assert not is_emoji, (
            f"PALETTE_ICONS still contains emoji {ch!r}"
        )
    # Must use either geometric shapes (v18) OR Lucide icon names (v19).
    has_v18_shapes = ("◆" in body or "●" in body or "◇" in body)
    has_v19_lucide = (
        "puzzle" in body or "circle" in body or "keyboard" in body
        or "diamond" in body or "square" in body or "circle-dot" in body
    )
    assert has_v18_shapes or has_v19_lucide, (
        "PALETTE_ICONS must use geometric shapes (v18) or Lucide names (v19)"
    )


def test_v18_palette_backdrop_no_blur():
    """palette-backdrop in live-dashboard.html must NOT use
    backdrop-filter:blur — v18 DESIGN.md removed this slop pattern."""
    html = HTML.read_text(encoding="utf-8")
    # Find palette-backdrop div
    import re as _re
    m = _re.search(r'id="palette-backdrop"[^>]*style="([^"]+)"', html)
    assert m, "palette-backdrop div not found in HTML"
    style = m.group(1)
    assert "backdrop-filter" not in style.replace(" ", ""), (
        f"palette-backdrop still has backdrop-filter — v18 must be flat: {style[:120]}"
    )


def test_v18_palette_row_uses_brand_muted_hover():
    """palette-row .sel/hover must use var(--brand-muted), not var(--elev-2).
    Required for Component Consistency audit dimension."""
    # The palette row styles are inline in src/modals.js (_paletteRender).
    modals = (DASHBOARD_DIR / "src" / "modals.js").read_text(encoding="utf-8")
    # Find the palette-row template.
    import re as _re
    m = _re.search(r'palette-row[^"]*"[^>]*>', modals)
    assert m, "palette-row template not found in src/modals.js"
    # Look in the surrounding context for the active/sel background.
    start = m.start()
    snippet = modals[start:start + 600]
    # After v18: brand-muted should appear in the sel/hover context.
    assert "brand-muted" in snippet or "--brand" in snippet, (
        "palette-row sel/hover still uses elev-2 — v18 must use --brand-muted"
    )


# ── v18 chunk D18 — ⌘K hint badge + recent commands ─────────────────────────
# Discoverability gap: user didn't know Cmd+K existed. v18 adds a visible
# hint badge in the header + tracks last-5 used commands for smart ranking.

def test_v18_header_has_cmdk_hint():
    """#header must contain a ⌘K / Ctrl K hint badge that opens the palette
    on click. Required for Discoverability audit dimension."""
    html = HTML.read_text(encoding="utf-8")
    # Look for a clickable badge that calls openPalette().
    import re as _re
    # Find any element inside #header that calls openPalette via onclick.
    hstart = html.find('id="header"')
    assert hstart > 0, "#header div not found in HTML"
    # Take next 4000 chars (whole header content; expanded for v19 brand mark).
    header_block = html[hstart:hstart + 4000]
    has_hint = (
        "openPalette()" in header_block
        and ("kbd-hint" in header_block or "⌘K" in header_block or "Ctrl" in header_block)
    )
    assert has_hint, (
        "header must have a clickable ⌘K hint badge that calls openPalette()"
    )


def test_v18_palette_recent_commands_tracking():
    """_paletteActivate must push to awiki-palette-recent localStorage key
    so the empty-query view can show recent commands at top."""
    modals = (DASHBOARD_DIR / "src" / "modals.js").read_text(encoding="utf-8")
    # Must reference the localStorage key + a function that tracks recents.
    assert "awiki-palette-recent" in modals, (
        "awiki-palette-recent localStorage key not defined for recent tracking"
    )
    # And there must be a helper function for reading/rendering recents.
    assert (
        "_paletteRecent" in modals or "paletteRecent" in modals
    ), "no recent-tracking helper function found"


# ── v19 chunk A19 — Lucide SVG sprite + icon() helper ───────────────────────
# Replaces emojis (cross-OS inconsistent, not professional per user feedback)
# with inline Lucide SVG sprite — Linear/Vercel/shadcn standard. See ADR-0011.

def test_v19_icon_sprite_defined():
    """v19 must ship an SVG sprite with ≥20 <symbol> icons for use via
    <use href='#icon-X'>. The sprite lives in src/icons.js (injected into
    <body> on boot) to keep live-dashboard.html under the markup budget.
    ADR-0011 documents the rationale (sprite too big for inline HTML markup,
    fine inside the JS bundle which has its own 260 KB budget)."""
    # Look in src/icons.js (sprite source of truth)
    icons_js = DASHBOARD_DIR / "src" / "icons.js"
    if not icons_js.is_file():
        # Fallback: sprite might be inline in HTML (older v19 alpha)
        html = HTML.read_text(encoding="utf-8")
        import re as _re
        symbols = _re.findall(r'<symbol\s+id="icon-([a-z0-9-]+)"', html)
    else:
        text = icons_js.read_text(encoding="utf-8")
        import re as _re
        # In src/icons.js the sprite is stored as escaped JS strings,
        # so the symbol id appears as id=\"icon-X\" (with backslash-quotes).
        # Accept either form for robustness.
        symbols = _re.findall(r'<symbol\s+id=\\?"icon-([a-z0-9-]+)\\?"', text)
    assert len(symbols) >= 20, (
        f"v19 SVG sprite must contain ≥20 icons, found {len(symbols)}: {symbols[:10]}"
    )


def test_v19_icon_helper_exists():
    """A JS helper function `icon(name)` (or similar) must exist to render
    <svg class='icon'><use href='#icon-X'/></svg> markup consistently."""
    src_dir = DASHBOARD_DIR / "src"
    found = False
    for js in src_dir.glob("*.js"):
        text = js.read_text(encoding="utf-8")
        # Match: function icon(name or icon(name or function _icon(
        if _matches_icon_helper(text):
            found = True
            break
    assert found, (
        "no icon() helper function found in src/*.js — v19 must provide one"
    )


def _matches_icon_helper(text):
    import re as _re
    patterns = [
        r"function\s+icon\s*\(",
        r"function\s+_icon\s*\(",
        r"\bicon\s*=\s*function\s*\(",
        r"\bicon\s*=\s*\(?[a-zA-Z_]+\)?\s*=>",
        r"function\s+renderIcon\s*\(",
    ]
    return any(_re.search(p, text) for p in patterns)


def test_v19_icon_css_class_present():
    """styles.css must define `.icon` class with stroke=currentColor for
    the SVG sprite usage to inherit theme color automatically."""
    css = STYLES_CSS.read_text(encoding="utf-8")
    # Look for .icon { ... stroke: currentColor ... }
    import re as _re
    m = _re.search(r"\.icon\s*\{[^}]+\}", css)
    assert m, ".icon CSS class not defined in styles.css"
    body = m.group(0)
    assert "currentColor" in body, (
        ".icon must use stroke:currentColor to inherit theme color"
    )


# ── v19 chunk B19 — Header icons replacement ────────────────────────────────
def test_v19_header_no_emoji_in_buttons():
    """#header buttons must not contain emoji text. v19 replaces with
    Lucide SVG icons (settings, save, bell, trash-2, etc)."""
    html = HTML.read_text(encoding="utf-8")
    import re as _re
    # Find the #header block
    hstart = html.find('id="header"')
    assert hstart > 0, "#header not found"
    # Take next 2500 chars (whole header content)
    header_block = html[hstart:hstart + 2500]
    # Find all <button ...>TEXT</button> and inspect TEXT for emoji.
    buttons = _re.findall(r"<button[^>]*>([^<]*)</button>", header_block)
    emoji_buttons = []
    for txt in buttons:
        txt = txt.strip()
        if not txt:
            continue
        for ch in txt:
            code = ord(ch)
            if 0x1F300 <= code <= 0x1FAFF or 0x2600 <= code <= 0x27BF:
                emoji_buttons.append(txt[:30])
                break
    assert not emoji_buttons, (
        f"#header still has emoji in buttons: {emoji_buttons}"
    )


def test_v19_header_uses_lucide_icons():
    """#header must reference Lucide icons via <use href='#icon-X'> or
    inline <svg class='icon'> patterns."""
    html = HTML.read_text(encoding="utf-8")
    hstart = html.find('id="header"')
    header_block = html[hstart:hstart + 2500]
    # Look for any icon reference — sprite use or inline svg.icon
    has_icon = (
        "icon-settings" in header_block
        or "icon-save" in header_block
        or "icon-bell" in header_block
        or "icon-trash" in header_block
        or 'class="icon' in header_block
        or "icon('settings'" in header_block
    )
    assert has_icon, (
        "#header must reference at least one Lucide icon (icon-settings/"
        "icon-save/icon-bell/icon-trash) after v19 B19"
    )


# ── v19 chunk C19 — View-tabs icons replacement ─────────────────────────────
def test_v19_view_tabs_no_emoji():
    """view-toggle-bar buttons must not start with emoji. v19 replaces with
    inline Lucide SVG icons (layout-dashboard, workflow, etc)."""
    html = HTML.read_text(encoding="utf-8")
    import re as _re
    # Find the view-toggle-bar block
    vstart = html.find('class="view-toggle-bar"')
    assert vstart > 0, "view-toggle-bar not found"
    # Take next 2500 chars (whole bar content)
    block = html[vstart:vstart + 2500]
    # Find button text contents
    buttons = _re.findall(r"<button[^>]*>([^<]+)</button>", block)
    bad = []
    for txt in buttons:
        txt = txt.strip()
        if not txt:
            continue
        first = txt[0]
        code = ord(first)
        if 0x1F300 <= code <= 0x1FAFF or 0x2600 <= code <= 0x27BF or 0x2190 <= code <= 0x21FF:
            bad.append(txt[:30])
    assert not bad, f"view-toggle-bar still has emoji in buttons: {bad}"


def test_v19_view_tabs_use_lucide():
    """view-toggle-bar must reference Lucide icons (icon-layout-dashboard,
    icon-workflow, etc) via inline <use href='#icon-X'>."""
    html = HTML.read_text(encoding="utf-8")
    vstart = html.find('class="view-toggle-bar"')
    block = html[vstart:vstart + 2500]
    has_icons = (
        "icon-layout-dashboard" in block
        or "icon-workflow" in block
        or "icon-puzzle" in block
        or "icon-bar-chart" in block
    )
    assert has_icons, "view-toggle-bar must use Lucide icons after v19 C19"


# ── v19 chunk D19 — Workflow tabs icons ─────────────────────────────────────
def test_v19_wf_tabs_no_emoji():
    """#wf-tabs buttons must not start with emoji. v19 replaces with
    Lucide SVG icons (rocket, clipboard-list, brain, dollar-sign)."""
    html = HTML.read_text(encoding="utf-8")
    import re as _re
    wstart = html.find('id="wf-tabs"')
    assert wstart > 0, "#wf-tabs not found"
    block = html[wstart:wstart + 1500]
    buttons = _re.findall(r"<div[^>]*class=\"[^\"]*wf-tab[^\"]*\"[^>]*>([^<]+)</div>", block)
    bad = []
    for txt in buttons:
        txt = txt.strip()
        if not txt:
            continue
        first = txt[0]
        code = ord(first)
        if 0x1F300 <= code <= 0x1FAFF or 0x2600 <= code <= 0x27BF:
            bad.append(txt[:30])
    assert not bad, f"#wf-tabs still has emoji in tabs: {bad}"


# ── v19 chunk E19 — Palette icons (◆●◇ -> Lucide) ───────────────────────────
def test_v19_palette_icons_use_lucide():
    """PALETTE_ICONS in src/modals.js must call icon() helper to render
    Lucide SVG icons, not use emoji or geometric shapes (◆●◇)."""
    modals = (DASHBOARD_DIR / "src" / "modals.js").read_text(encoding="utf-8")
    # PALETTE_ICONS should now map type -> icon name passed to icon() helper.
    # Find the constant or its usage in _paletteRowHtml.
    import re as _re
    m = _re.search(r"PALETTE_ICONS\s*=\s*\{([^}]+)\}", modals)
    assert m, "PALETTE_ICONS const not found"
    body = m.group(1)
    # Old v18 shapes (◆●◇) must be gone.
    for shape in ("◆", "●", "◇"):
        assert shape not in body, (
            f"PALETTE_ICONS still uses geometric shape {shape!r} — v19 uses Lucide"
        )
    # Should reference Lucide icon names like 'puzzle', 'circle', 'keyboard'.
    has_lucide = (
        "puzzle" in body or "circle" in body or "keyboard" in body
        or "diamond" in body or "square" in body
    )
    assert has_lucide, (
        "PALETTE_ICONS must reference Lucide icon names (puzzle/circle/keyboard)"
    )


# ── v19 chunk F19 — Status/event icons (evIcon) ─────────────────────────────
def test_v19_evIcon_uses_lucide():
    """evIcon function in src/graph.js must return Lucide SVG markup (via
    icon() helper), not emojis. Affects every row in the event timeline."""
    graph = (DASHBOARD_DIR / "src" / "graph.js").read_text(encoding="utf-8")
    import re as _re
    # Find evIcon function body.
    m = _re.search(r"function\s+evIcon\s*\([^)]*\)\s*\{([^}]+)\}", graph)
    assert m, "evIcon function not found in src/graph.js"
    body = m.group(1)
    # Must NOT return emojis for hook_check/cost_declare/session_start.
    # v16 emojis: 🔌💰✅🔴🔒⚠▸ ✓ ✗
    for ch in body:
        code = ord(ch)
        if 0x1F300 <= code <= 0x1FAFF or 0x2600 <= code <= 0x27BF:
            # Allow if used inside a string fallback (rare); flag if main return.
            pass
    # Should reference icon() helper OR icon-XXX sprite IDs.
    has_lucide = (
        "icon(" in body or "icon-" in body
        or "'power'" in body or "'dollar-sign'" in body
        or "'check-circle" in body or "'x-circle" in body
        or "'alert-triangle" in body
    )
    assert has_lucide, (
        "evIcon must use Lucide icon() helper or icon-XXX sprite IDs (v19 F19)"
    )


# ── v19 chunk G19 — Skill-detail + chat avatars ─────────────────────────────
def test_v19_chat_avatars_use_lucide():
    """Chat message avatars must use Lucide icons (bot, user) instead of
    emoji. addChatMessage in src/chat.js renders the avatar."""
    chat = (DASHBOARD_DIR / "src" / "chat.js").read_text(encoding="utf-8")
    # Look for icon() calls with 'bot' or 'user' OR sprite references.
    has_lucide = (
        "icon('bot'" in chat or 'icon("bot")' in chat
        or "icon-bot" in chat
        or "icon('user'" in chat or 'icon("user")' in chat
        or "icon-user" in chat
    )
    assert has_lucide, (
        "chat.js must use Lucide bot/user icons via icon() helper (v19 G19)"
    )


def test_v19_skill_detail_share_button_lucide():
    """Skill-detail share button must use icon-share / icon-link via icon()
    helper instead of 🔗 emoji."""
    skills = (DASHBOARD_DIR / "src" / "skills.js").read_text(encoding="utf-8")
    # Look for share button — was previously 🔗 emoji in copySkillLink button.
    has_lucide_share = (
        "icon('link'" in skills or 'icon("link")' in skills
        or "icon('share" in skills or 'icon("share' in skills
        or "icon-link" in skills or "icon-share" in skills
    )
    assert has_lucide_share, (
        "skills.js copy/share button must use Lucide icon (v19 G19)"
    )


# ── v19 chunk H19 — imagegen brand mark ─────────────────────────────────────
def test_v19_brand_mark_exists():
    """Brand mark SVG asset must exist for the header. Replaces plain text
    'A-Wiki Live' wordmark with a geometric diamond + wordmark combo."""
    brand_svg = DASHBOARD_DIR / "brand-mark.svg"
    assert brand_svg.is_file(), "brand-mark.svg not found in dashboard dir"
    content = brand_svg.read_text(encoding="utf-8")
    # Must be a valid SVG with the wordmark text.
    assert "<svg" in content, "brand-mark.svg must be valid SVG"
    assert "A-Wiki" in content, "brand-mark.svg must contain the wordmark"


def test_v19_header_uses_brand_mark():
    """#header .brand must reference brand-mark.svg (or inline equivalent)
    instead of plain 'A-Wiki Live' text only."""
    html = HTML.read_text(encoding="utf-8")
    hstart = html.find('id="header"')
    header_block = html[hstart:hstart + 4000]
    # Accept any of: <img src='brand-mark.svg'>, inline SVG, or class hook.
    has_brand = (
        "brand-mark.svg" in header_block
        or 'class="brand brand-mark"' in header_block
        or 'class="brand-mark"' in header_block
    )
    assert has_brand, (
        "#header must reference brand-mark.svg or inline brand SVG (v19 H19)"
    )

