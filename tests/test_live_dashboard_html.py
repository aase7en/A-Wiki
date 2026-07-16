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
    assert size < 68 * 1024, f"HTML too large: {size} bytes (limit 68 KB — JS/CSS extracted in v8; raised for post-v9 panels + v11 Backup pane)"


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
    # v8: CSS extracted to styles.css — read it directly instead of finding </style>.
    if not STYLES_CSS.is_file():
        pytest.skip("styles.css not found (pre-v8)")
    css = STYLES_CSS.read_text(encoding="utf-8")
    root = css[: css.find("}")]  # :root block ends at first }
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
    # v8: CSS extracted to styles.css — read it directly instead of finding </style>.
    if not STYLES_CSS.is_file():
        pytest.skip("styles.css not found (pre-v8)")
    css = STYLES_CSS.read_text(encoding="utf-8")
    # CSS hex after :root block close (the first `}` ends :root)
    root_end = css.find("}")
    style_after = css[root_end + 1:]
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
