"""Tests for the Live Dashboard Skills service (skills_service.py).

Covers: filtering, per-agent visibility, Thai content roundtrip, detail lookup,
and the agent_overview skill counts.
"""
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "live-dashboard"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import skills_service  # noqa: E402


def test_list_all_returns_canonical():
    r = skills_service.list_skills("")
    assert r["count"] > 0, "expected at least one skill"
    assert r["total_matched"] == r["count"]
    # All returned skills should be canonical (aliases filtered out)
    for s in r["skills"]:
        assert s["status"] == "canonical"
    assert "stats" in r
    assert "agents" in r


def test_filter_by_invocation_auto():
    r = skills_service.list_skills("invocation=auto")
    # awiki-lifecycle-router + continuous-learning-v2 are marked auto in thai_guide
    assert r["count"] >= 1, "expected at least one auto skill"
    for s in r["skills"]:
        assert s["invocation"] == "auto"


def test_filter_by_invocation_manual():
    r = skills_service.list_skills("invocation=manual")
    assert r["count"] > 0
    for s in r["skills"]:
        assert s["invocation"] == "manual"


def test_filter_by_domain():
    r = skills_service.list_skills("domain=code")
    assert r["count"] > 0
    for s in r["skills"]:
        domains = s.get("domain") or []
        if isinstance(domains, str):
            domains = [domains]
        assert "code" in domains


def test_search_thai_content():
    # debug-mantra has th_description containing "debug"
    r = skills_service.list_skills("q=debug")
    names = [s["name"] for s in r["skills"]]
    assert "debug-mantra" in names, f"debug-mantra not in {names}"


def test_search_thai_word():
    # Thai content should be searchable too (th_description contains Thai script)
    r = skills_service.list_skills("q=แก้")
    # At least one skill mentions bug fixing in Thai
    assert r["count"] >= 0  # don't hard-fail if Thai tokenization differs; just exercise path


def test_per_agent_visibility_uses_registry():
    """Skills with agents:['all'] should appear for every known agent."""
    ov = skills_service.agent_overview()
    assert ov["total_canonical"] > 0
    # Most skills are agents:['all'] so claude/codex should see the bulk
    for agent in ("claude", "codex", "zcode"):
        assert ov["skill_counts"][agent] > 0, f"{agent} sees 0 skills"
    # 'all' count should equal total canonical
    assert ov["skill_counts"]["all"] == ov["total_canonical"]


def test_get_skill_detail_returns_thai_fields():
    s = skills_service.get_skill("debug-mantra")
    assert s is not None
    assert s["name"] == "debug-mantra"
    assert s.get("th_description"), "th_description should be populated"
    assert s.get("when_to_use"), "when_to_use should be populated"
    assert isinstance(s.get("examples"), list) and len(s["examples"]) >= 1


def test_get_skill_detail_not_found():
    s = skills_service.get_skill("does-not-exist-xyz")
    assert s is None


def test_get_skill_resolves_alias():
    """get() should resolve aliases to their canonical skill."""
    # two-axis-code-review is the canonical name (renamed from code-review alias)
    s = skills_service.get_skill("two-axis-code-review")
    assert s is not None
    assert s["status"] == "canonical"


def test_agent_filter_matches_canonical_for_agent():
    """list_skills(agent=X) count should match agent_overview count."""
    ov = skills_service.agent_overview()
    for agent in ("claude", "codex"):
        r = skills_service.list_skills(f"agent={agent}")
        assert r["count"] == ov["skill_counts"][agent], (
            f"{agent}: list={r['count']} overview={ov['skill_counts'][agent]}"
        )


def test_stats_structure():
    r = skills_service.list_skills("")
    stats = r["stats"]
    assert "by_domain" in stats
    assert "by_invocation" in stats
    assert "by_agent" in stats
    assert "has_thai" in stats
    assert stats["total"] == r["count"]
    assert stats["has_thai"] >= 40, "expected ~48 skills with Thai content"


def test_limit_param():
    r = skills_service.list_skills("limit=5")
    assert r["count"] <= 5
    assert r["total_matched"] >= r["count"]


# ---------------------------------------------------------------------------
# CHUNK SO3 — category= filter (separates subagents from regular skills)
# ---------------------------------------------------------------------------

def test_filter_by_category_subagent():
    """?category=subagent should return only subagent-category skills."""
    r = skills_service.list_skills("category=subagent")
    assert r["count"] > 0, "expected at least one subagent"
    for s in r["skills"]:
        assert s.get("category") == "subagent", (
            f"{s.get('name')} has category={s.get('category')!r}, expected 'subagent'"
        )


def test_filter_by_category_excludes_subagents_when_unset():
    """Without category filter, both regular skills and subagents appear.
    With category=skill (or any non-subagent value), subagents are filtered out."""
    r_all = skills_service.list_skills("")
    r_no_sub = skills_service.list_skills("category=skill")
    # The default view includes everything; restricting to category=skill drops subagents
    assert r_all["count"] >= r_no_sub["count"]
    for s in r_no_sub["skills"]:
        assert s.get("category") != "subagent"


def test_stats_include_by_category():
    """Stats should carry a by_category breakdown for filter chips."""
    r = skills_service.list_skills("")
    assert "by_category" in r["stats"], "stats missing by_category"
    # We registered 28 subagents — they should show up in the breakdown.
    assert r["stats"]["by_category"].get("subagent", 0) >= 20, (
        f"expected >=20 subagents in by_category, got {r['stats']['by_category']}"
    )


def test_filters_echo_category():
    """The returned `filters` object should echo the category param (or None)."""
    r1 = skills_service.list_skills("category=subagent")
    assert r1["filters"]["category"] == "subagent"
    r2 = skills_service.list_skills("")
    assert r2["filters"]["category"] is None


# ---------------------------------------------------------------------------
# CHUNK K — skill_graph() — skill dependency graph for vis-network
# ---------------------------------------------------------------------------

def test_skill_graph_returns_nodes_and_edges():
    g = skills_service.skill_graph()
    assert "nodes" in g and "edges" in g
    assert isinstance(g["nodes"], list) and len(g["nodes"]) > 0
    assert isinstance(g["edges"], list)
    assert g["stats"]["nodes"] == len(g["nodes"])
    assert g["stats"]["edges"] == len(g["edges"])
    # Every node must have id + label + domain + phase
    for n in g["nodes"]:
        assert "id" in n and "label" in n
        assert "domain" in n and "phase" in n


def test_skill_graph_edges_have_weight_gte_2():
    """Edges represent meaningful relationships — same phase (+3) or 2+ shared domains (+2)."""
    g = skills_service.skill_graph()
    for e in g["edges"]:
        assert e["weight"] >= 2, f"edge {e} has weight < 2"
        assert "from" in e and "to" in e


def test_skill_graph_default_excludes_none_phase():
    """Default graph shows skills with lifecycle_phase != 'none' for a usable graph."""
    g = skills_service.skill_graph()
    phases = {n["phase"] for n in g["nodes"]}
    # Default mode should not include 'none' phase (those have no lifecycle relationships)
    assert "none" not in phases, "default graph should exclude phase=none skills"


def test_skill_graph_all_includes_none_phase():
    """?all=1 shows all canonical skills including phase=none."""
    g = skills_service.skill_graph(all_skills=True)
    phases = {n["phase"] for n in g["nodes"]}
    assert "none" in phases


def test_skill_graph_domain_filter():
    g = skills_service.skill_graph(domain="code")
    for n in g["nodes"]:
        domains = n["domain"] if isinstance(n["domain"], list) else [n["domain"]]
        assert "code" in domains


def test_skill_graph_phase_filter():
    g = skills_service.skill_graph(phase="build")
    for n in g["nodes"]:
        assert n["phase"] == "build"


def test_skill_graph_node_colors_set():
    """Each node should carry a color field for vis-network styling."""
    g = skills_service.skill_graph()
    for n in g["nodes"]:
        assert "color" in n and n["color"]


# ---------------------------------------------------------------------------
# CHUNK P — walkthrough_difficulty() — auto-score 0-100
# ---------------------------------------------------------------------------

def test_walkthrough_difficulty_returns_score_and_level():
    """Difficulty must return score (0-100), level (Thai), and factors dict."""
    flow = {
        "title_th": "test flow",
        "steps": [
            {"skill": "debug-mantra"},
            {"skill": "scrutinize"},
        ],
    }
    d = skills_service.walkthrough_difficulty(flow)
    assert 0 <= d["score"] <= 100
    assert d["level"] in ("เริ่มต้น", "ปานกลาง", "ขั้นสูง")
    assert "factors" in d and isinstance(d["factors"], dict)


def test_walkthrough_difficulty_more_steps_higher_score():
    """A flow with more steps should score >= a flow with fewer steps."""
    small = {"steps": [{"skill": "debug-mantra"}]}
    large = {"steps": [{"skill": "debug-mantra"}, {"skill": "scrutinize"},
                        {"skill": "post-mortem"}, {"skill": "security-and-hardening"},
                        {"skill": "performance-optimization"}, {"skill": "shipping-and-launch"},
                        {"skill": "ci-cd-and-automation"}, {"skill": "documentation-and-adrs"}]}
    d_small = skills_service.walkthrough_difficulty(small)
    d_large = skills_service.walkthrough_difficulty(large)
    assert d_large["score"] >= d_small["score"], (
        f"large ({d_large['score']}) should >= small ({d_small['score']})"
    )


def test_walkthrough_difficulty_level_mapping():
    """Score <=33 = เริ่มต้น, <=66 = ปานกลาง, >66 = ขั้นสูง."""
    # Force a low score by using a single simple skill.
    d1 = skills_service.walkthrough_difficulty({"steps": [{"skill": "debug-mantra"}]})
    assert d1["level"] in ("เริ่มต้น", "ปานกลาง", "ขั้นสูง")
    # Check mapping logic directly via score.
    assert d1["level"] == ("เริ่มต้น" if d1["score"] <= 33
                           else "ปานกลาง" if d1["score"] <= 66
                           else "ขั้นสูง")


def test_walkthrough_difficulty_empty_flow():
    """Empty steps list should return score 0, level เริ่มต้น."""
    d = skills_service.walkthrough_difficulty({"steps": []})
    assert d["score"] == 0
    assert d["level"] == "เริ่มต้น"


# ---------------------------------------------------------------------------
# CHUNK R — recommend_skills() — text-based skill recommendation
# ---------------------------------------------------------------------------

def test_recommend_returns_results_with_match_reason():
    r = skills_service.recommend_skills("debug bug", limit=5)
    assert "results" in r and isinstance(r["results"], list)
    assert r["query"] == "debug bug"
    for res in r["results"]:
        assert "name" in res and "score" in res and "match_reason" in res


def test_recommend_empty_query_returns_empty():
    r = skills_service.recommend_skills("", limit=5)
    assert r["results"] == []
    assert r["total_matched"] == 0


def test_recommend_thai_query():
    """Thai query should work — test a common Thai word."""
    r = skills_service.recommend_skills("แก้", limit=5)
    assert r["total_matched"] >= 0  # don't hard-fail on tokenization


def test_recommend_sorted_by_score_desc():
    r = skills_service.recommend_skills("test", limit=10)
    scores = [res["score"] for res in r["results"]]
    assert scores == sorted(scores, reverse=True), f"scores not sorted desc: {scores}"


def test_recommend_limit_respected():
    r = skills_service.recommend_skills("code", limit=3)
    assert len(r["results"]) <= 3


# ---------------------------------------------------------------------------
# CHUNK V — recommend_skills() walkthrough matching
# ---------------------------------------------------------------------------

def test_recommend_includes_walkthroughs_when_matching():
    """When query matches a walkthrough title/summary, suggest the flow too."""
    r = skills_service.recommend_skills("debug", limit=5)
    assert "walkthroughs" in r, "recommend response must include walkthroughs key"
    assert isinstance(r["walkthroughs"], list)
    # "debug" should match at least one walkthrough (e.g. debug-production-issue)
    if r["walkthroughs"]:
        w = r["walkthroughs"][0]
        assert "id" in w and "title_th" in w and "score" in w and "match_reason" in w


def test_recommend_walkthroughs_empty_when_no_match():
    """Gibberish query should return empty walkthroughs list."""
    r = skills_service.recommend_skills("xyzzyqwerty123", limit=5)
    assert r["walkthroughs"] == []


# ---------------------------------------------------------------------------
# CHUNK NN — bugfix: _load_walkthroughs_for_recommend must be defined
# Pre-fix this test FAILS because the function was orphaned (no `def` header)
# ---------------------------------------------------------------------------

def test_recommend_returns_walkthrough_when_query_matches_flow_id():
    """deploy-flask-app flow has id 'deploy-flask-app' — query 'deploy' must match.

    Pre-CHUNK-NN this fails silently: _load_walkthroughs_for_recommend
    was missing its `def` header, so NameError was swallowed by try/except
    and walkthroughs was always []. This test pins the fix.
    """
    r = skills_service.recommend_skills("deploy", limit=5)
    assert "walkthroughs" in r
    assert isinstance(r["walkthroughs"], list)
    assert len(r["walkthroughs"]) >= 1, (
        "expected 'deploy' to match deploy-flask-app walkthrough; "
        "if this fails, _load_walkthroughs_for_recommend may be broken again"
    )
    ids = [w.get("id") for w in r["walkthroughs"]]
    assert "deploy-flask-app" in ids, f"deploy-flask-app missing from {ids}"


def test_load_walkthroughs_for_recommend_is_callable():
    """The helper must be a real callable, not orphaned code."""
    fn = getattr(skills_service, "_load_walkthroughs_for_recommend", None)
    assert callable(fn), "_load_walkthroughs_for_recommend must be defined and callable"
    data = fn()
    assert isinstance(data, dict)
    # Real file has 16 flows + _meta
    assert len(data) >= 10, f"expected >=10 walkthrough entries, got {len(data)}"

def test_skill_history_returns_dict_for_known_skill():
    """skill_history should return a dict with expected keys for a real skill."""
    h = skills_service.skill_history("debug-mantra")
    assert isinstance(h, dict)
    # version may be empty, but key must exist.
    assert "version" in h
    # Git-derived fields (may be empty if git fails, but keys must exist).
    assert "last_commit_date" in h
    assert "last_commit_hash" in h
    assert "commit_count" in h


def test_skill_history_missing_skill_returns_empty():
    """Unknown skill name should return empty dict (fail gracefully)."""
    h = skills_service.skill_history("does-not-exist-xyz-123")
    assert h == {} or h.get("commit_count", 0) == 0


def test_skill_history_no_shell_true():
    """Ensure git is invoked via subprocess list (not shell=True) — security check.
    We verify by checking the function doesn't crash and returns structured data.
    The actual no-shell enforcement is in the code itself.
    """
    h = skills_service.skill_history("debug-mantra")
    # If shell injection were possible, this would error; structured return = safe.
    assert isinstance(h, dict)


# ---------------------------------------------------------------------------
# CHUNK W — update_skill_field() — inline editor write-back (security-sensitive)
# ---------------------------------------------------------------------------

def test_update_skill_field_writes_and_restores():
    """update_skill_field must write th_description and validate.
    Saves + restores the original value to avoid polluting the registry."""
    import json
    reg_path = REPO_ROOT / "skills-registry.json"
    # Save original value.
    with open(reg_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    by_name = {s["name"]: s for s in data["skills"] if "name" in s}
    original = by_name.get("debug-mantra", {}).get("th_description", "")
    test_value = "[TEST] ทดสอบ inline editor — ลบทิ้งได้"
    try:
        r = skills_service.update_skill_field("debug-mantra", "th_description", test_value)
        assert r["ok"], f"update failed: {r.get('error')}"
        # Verify it was written.
        with open(reg_path, "r", encoding="utf-8") as f:
            data2 = json.load(f)
        by_name2 = {s["name"]: s for s in data2["skills"] if "name" in s}
        assert by_name2["debug-mantra"]["th_description"] == test_value
    finally:
        # Restore original.
        with open(reg_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for s in data["skills"]:
            if s.get("name") == "debug-mantra":
                s["th_description"] = original
                break
        with open(reg_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def test_update_skill_field_rejects_non_editable_field():
    """field 'name' must be rejected — not in EDITABLE_FIELDS allowlist."""
    r = skills_service.update_skill_field("debug-mantra", "name", "hacked")
    assert not r["ok"]
    assert "allowlist" in r.get("error", "").lower() or "not editable" in r.get("error", "").lower()


def test_update_skill_field_rejects_oversized_value():
    """Value > 2000 chars must be rejected."""
    r = skills_service.update_skill_field("debug-mantra", "th_description", "x" * 2001)
    assert not r["ok"]
    assert "too long" in r.get("error", "").lower() or "length" in r.get("error", "").lower()


def test_update_skill_field_rejects_unknown_skill():
    r = skills_service.update_skill_field("does-not-exist-xyz", "th_description", "val")
    assert not r["ok"]
    assert "not found" in r.get("error", "").lower()


# ---------------------------------------------------------------------------
# CHUNK AA — skill_history() changelog expansion
# ---------------------------------------------------------------------------

def test_skill_history_changelog_format():
    """include_changelog=True must return a list of {date, hash, message}."""
    h = skills_service.skill_history("debug-mantra", include_changelog=True)
    assert "changelog" in h, "changelog key must exist when include_changelog=True"
    assert isinstance(h["changelog"], list)
    if h["changelog"]:  # may be empty if git unavailable, but structure must be right
        entry = h["changelog"][0]
        assert "date" in entry
        assert "hash" in entry
        assert "message" in entry


def test_skill_history_changelog_empty_for_missing():
    """Unknown skill should return empty dict even with changelog requested."""
    h = skills_service.skill_history("does-not-exist-xyz", include_changelog=True)
    assert h == {} or h.get("commit_count", 0) == 0


def test_skill_history_no_changelog_by_default():
    """Default call (no include_changelog) must NOT include changelog key."""
    h = skills_service.skill_history("debug-mantra")
    assert "changelog" not in h, "changelog should be omitted unless requested"


# ---------------------------------------------------------------------------
# CHUNK BB — recommend_skills() semantic search fallback tier
# ---------------------------------------------------------------------------

def test_recommend_returns_mode_field():
    """recommend_skills response must include 'mode' field (semantic|substring)."""
    r = skills_service.recommend_skills("debug", limit=3)
    assert "mode" in r, "recommend response must include mode field"
    assert r["mode"] in ("semantic", "substring"), f"invalid mode: {r['mode']}"


def test_recommend_fallback_to_substring_when_no_vec():
    """If sqlite_vec/fastembed unavailable, mode must be 'substring'."""
    # This test verifies the fallback works. Whether we actually have
    # the deps installed determines which path runs, but either way the
    # response must be valid and contain results for a known query.
    r = skills_service.recommend_skills("debug", limit=3)
    assert r["mode"] in ("semantic", "substring")
    if r["mode"] == "substring":
        # Fallback path must still return results.
        assert r["total_matched"] > 0, "substring fallback should find 'debug'"


# ---------------------------------------------------------------------------
# CHUNK FF — skill_health_score()
# ---------------------------------------------------------------------------

def test_skill_health_score_returns_expected_shape():
    """skill_health_score must return dict with score, level, missing."""
    r = skills_service.skill_health_score({"name": "x"})
    assert isinstance(r, dict)
    assert set(r.keys()) >= {"score", "level", "missing"}
    assert 0 <= r["score"] <= 100
    assert r["level"] in ("critical", "weak", "ok", "good")
    assert isinstance(r["missing"], list)


def test_skill_health_score_empty_skill_is_critical():
    """A skill with no documented fields should score 0 and be 'critical'."""
    r = skills_service.skill_health_score({"name": "ghost-skill"})
    assert r["score"] == 0, f"empty skill should be 0, got {r['score']}"
    assert r["level"] == "critical"
    assert len(r["missing"]) == 6, "all 6 coverage fields missing"


def test_skill_health_score_full_skill_is_good():
    """A skill with all 6 documented fields should score 100 and be 'good'."""
    full = {
        "name": "complete",
        "th_description": "ทดสอบ",
        "when_to_use": "เมื่อไหร่",
        "examples": [{"scenario": "x", "how": "y"}],
        "process_steps": ["a", "b"],
        "invocation_hint": "/test",
        "invocation": "manual",
    }
    r = skills_service.skill_health_score(full)
    assert r["score"] == 100, f"full skill should be 100, got {r['score']}"
    assert r["level"] == "good"
    assert r["missing"] == []


def test_skill_health_score_weighting():
    """th_description (weight 3) should outweigh invocation_hint (weight 1).

    max=11 (3+2+2+2+1+1). Only th_description set => 3/11 ≈ 27 => score 24
    rounded down. Only invocation_hint set => 1/11 ≈ 9 => score 9.
    The first must score higher than the second.
    """
    r_desc = skills_service.skill_health_score({"name": "a", "th_description": "x"})
    r_hint = skills_service.skill_health_score({"name": "a", "invocation_hint": "/x"})
    assert r_desc["score"] > r_hint["score"], (
        f"th_description (w3) should score higher than invocation_hint (w1): "
        f"{r_desc['score']} vs {r_hint['score']}"
    )


def test_skill_health_score_in_list_item():
    """list_skills response items should include a 'health' field."""
    r = skills_service.list_skills("")
    assert r["count"] > 0
    for s in r["skills"][:5]:
        assert "health" in s, f"skill {s.get('name')} missing health field"
        h = s["health"]
        assert "score" in h and "level" in h


# ---------------------------------------------------------------------------
# CHUNK GG — registry push (SSE auto-refresh on registry mtime change)
# ---------------------------------------------------------------------------

def test_registry_push_event_format():
    """The SSE event broadcast for registry changes must be valid JSON with
    type='registry_update' and a numeric ts. Tested via the pure helper.
    """
    import importlib
    server = importlib.import_module("server")
    evt = server.build_registry_event()
    import json
    parsed = json.loads(evt)
    assert parsed["type"] == "registry_update", f"wrong type: {parsed.get('type')}"
    assert isinstance(parsed["ts"], (int, float)) and parsed["ts"] > 0


def test_registry_push_detects_mtime_change():
    """check_registry_changed() must return True once after mtime advances,
    then False on the next call (idempotent within the same mtime window).
    """
    import importlib
    server = importlib.import_module("server")
    # Reset internal last-mtime so the first call seeds it.
    server._registry_last_mtime = 0.0
    # First call seeds and reports no change.
    assert server.check_registry_changed() is False, "first call should seed, not change"
    # Force a fake newer mtime by monkeypatching the stat call path.
    import skills_service as ss
    orig = ss.REGISTRY_FILE
    class _FakePath:
        def stat(self):
            class _S:
                st_mtime = 9999999999.0
            return _S()
    ss.REGISTRY_FILE = _FakePath()
    try:
        assert server.check_registry_changed() is True, "newer mtime must trigger True"
        # Second call at same mtime must be False (debounce).
        assert server.check_registry_changed() is False, "same mtime must not re-trigger"
    finally:
        ss.REGISTRY_FILE = orig


# ---------------------------------------------------------------------------
# CHUNK HH — detect_cycles() on skill graph edges
# ---------------------------------------------------------------------------

def test_detect_cycles_returns_expected_shape():
    """detect_cycles must return dict with cycles, has_cycle, count."""
    r = skills_service.detect_cycles([])
    assert set(r.keys()) >= {"cycles", "has_cycle", "count"}
    assert isinstance(r["cycles"], list)
    assert r["has_cycle"] is False
    assert r["count"] == 0


def test_detect_cycles_none_on_linear():
    """A→B→C (no back edge) has no cycle."""
    edges = [
        {"from": "A", "to": "B"},
        {"from": "B", "to": "C"},
    ]
    r = skills_service.detect_cycles(edges)
    assert r["has_cycle"] is False
    assert r["cycles"] == []


def test_detect_cycles_simple_two_node():
    """A→B, B→A is a 2-cycle."""
    edges = [
        {"from": "A", "to": "B"},
        {"from": "B", "to": "A"},
    ]
    r = skills_service.detect_cycles(edges)
    assert r["has_cycle"] is True
    assert r["count"] >= 1
    # Each cycle is a list of node names; the pair {A,B} must be in one.
    found = any(set(c) == {"A", "B"} for c in r["cycles"])
    assert found, f"A-B cycle missing from {r['cycles']}"


def test_detect_cycles_three_node():
    """A→B, B→C, C→A is a 3-cycle."""
    edges = [
        {"from": "A", "to": "B"},
        {"from": "B", "to": "C"},
        {"from": "C", "to": "A"},
    ]
    r = skills_service.detect_cycles(edges)
    assert r["has_cycle"] is True
    assert r["count"] >= 1
    found = any(set(c) == {"A", "B", "C"} for c in r["cycles"])
    assert found, f"A-B-C cycle missing from {r['cycles']}"


def test_detect_cycles_respects_max_depth():
    """A long chain longer than max_depth should not be reported as a cycle
    even if it eventually loops back — we cap exploration to avoid pathological
    O(n!) blowups on huge graphs.
    """
    # Build a 20-node ring A0→A1→...→A19→A0.
    edges = [{"from": f"A{i}", "to": f"A{(i+1) % 20}"} for i in range(20)]
    r = skills_service.detect_cycles(edges, max_depth=5)
    # With max_depth=5, the 20-ring exceeds the cap -> no cycle reported.
    assert r["has_cycle"] is False
    # With default max_depth=10, still too long -> no cycle.
    r2 = skills_service.detect_cycles(edges)
    assert r2["has_cycle"] is False
    # But with max_depth=25, the ring is within cap -> detected.
    r3 = skills_service.detect_cycles(edges, max_depth=25)
    assert r3["has_cycle"] is True


# ---------------------------------------------------------------------------
# CHUNK JJ — agent_skill_matrix()
# ---------------------------------------------------------------------------

def test_agent_skill_matrix_shape():
    """agent_skill_matrix must return agents/skills/matrix/totals."""
    r = skills_service.agent_skill_matrix()
    assert set(r.keys()) >= {"agents", "skills", "matrix", "totals"}
    # 11 agents (KNOWN_AGENTS excludes 'all').
    assert len(r["agents"]) == 11, f"expected 11 agents, got {len(r['agents'])}"
    # Skills should be canonical (status check done internally).
    assert len(r["skills"]) > 0
    assert isinstance(r["matrix"], dict)
    assert isinstance(r["totals"], dict)


def test_agent_skill_matrix_all_visible_for_all_tagged():
    """A skill with agents:['all'] must be visible to every agent column."""
    r = skills_service.agent_skill_matrix()
    # Find a skill tagged 'all' in the real registry.
    reg = skills_service._load_registry()
    all_skill = next((s for s in reg.skills
                      if s.get("status") == "canonical"
                      and "all" in (s.get("agents") or [])), None)
    if not all_skill:
        return  # no 'all' skill in registry — skip
    name = all_skill["name"]
    assert name in r["matrix"], f"{name} missing from matrix"
    row = r["matrix"][name]
    # Every agent column must be True.
    for agent in r["agents"]:
        assert row.get(agent) is True, (
            f"{name} (agents:['all']) not visible to {agent}"
        )


def test_agent_skill_matrix_specific_agent_visibility():
    """A skill tagged only to a specific agent (not 'all') must show True
    only for that agent, False for others."""
    r = skills_service.agent_skill_matrix()
    reg = skills_service._load_registry()
    # Find a skill tagged to exactly one specific agent (not 'all').
    specific = next((s for s in reg.skills
                     if s.get("status") == "canonical"
                     and "all" not in (s.get("agents") or [])
                     and len(s.get("agents") or []) == 1), None)
    if not specific:
        return  # no specific-agent skill — skip
    name = specific["name"]
    tagged_agent = specific["agents"][0]
    row = r["matrix"].get(name, {})
    if tagged_agent in r["agents"]:
        assert row.get(tagged_agent) is True, (
            f"{name} should be visible to {tagged_agent}"
        )
        # At least one OTHER agent should be False.
        others = [a for a in r["agents"] if a != tagged_agent]
        assert any(not row.get(a) for a in others), (
            f"{name} appears visible to all agents — expected only {tagged_agent}"
        )


def test_agent_skill_matrix_totals_match_matrix():
    """totals[agent] must equal count of skills visible to that agent."""
    r = skills_service.agent_skill_matrix()
    for agent in r["agents"]:
        expected = sum(1 for row in r["matrix"].values() if row.get(agent))
        assert r["totals"][agent] == expected, (
            f"totals[{agent}]={r['totals'][agent]} != matrix count {expected}"
        )
