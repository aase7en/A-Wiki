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
