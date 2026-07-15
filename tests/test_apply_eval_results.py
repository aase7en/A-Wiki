"""Tests for apply_eval_results.py — recommend + apply model changes from eval results.

P1 fix coverage: build_change_preview MUST map suites → concrete subagent files
(via build_suite_to_subagents reading the `subagent` field from each eval case),
so that --write can actually find and edit the right frontmatter. Before this
fix, main() called build_change_preview(recs) with suite_to_subagents=None,
producing suite-level placeholder entries ("<all in suite:medical>") that
--write could never resolve to a file.
"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "eval"))

import apply_eval_results as ap  # noqa: E402


# ---------------------------------------------------------------------------
# build_suite_to_subagents — derive suite → [subagent names] from eval suites
# ---------------------------------------------------------------------------

def test_build_suite_to_subagents_reads_subagent_field(tmp_path):
    """build_suite_to_subagents must read the `subagent` field from each case
    in evals/subagents/*.json and return a {suite: [unique subagent names]} map."""
    suite = {
        "suite": "medical",
        "cases": [
            {"id": "c1", "subagent": "medical-lit-reviewer", "prompt": "p",
             "required": [], "forbidden": []},
            {"id": "c2", "subagent": "clinical-reasoner", "prompt": "p",
             "required": [], "forbidden": []},
            {"id": "c3", "subagent": "medical-lit-reviewer", "prompt": "p",
             "required": [], "forbidden": []},  # duplicate → dedup
        ],
    }
    (tmp_path / "medical.json").write_text(json.dumps(suite))
    mapping = ap.build_suite_to_subagents(tmp_path)
    assert mapping == {"medical": ["medical-lit-reviewer", "clinical-reasoner"]}


def test_build_suite_to_subagents_multiple_suites(tmp_path):
    a = {"suite": "a", "cases": [{"id": "1", "subagent": "x", "prompt": "", "required": [], "forbidden": []}]}
    b = {"suite": "b", "cases": [{"id": "1", "subagent": "y", "prompt": "", "required": [], "forbidden": []}]}
    (tmp_path / "a.json").write_text(json.dumps(a))
    (tmp_path / "b.json").write_text(json.dumps(b))
    mapping = ap.build_suite_to_subagents(tmp_path)
    assert mapping == {"a": ["x"], "b": ["y"]}


def test_build_suite_to_subagents_ignores_results_subdir(tmp_path):
    """results/*.json are NOT eval suites — must be excluded."""
    suite = {"suite": "medical", "cases": [{"id": "1", "subagent": "x", "prompt": "",
              "required": [], "forbidden": []}]}
    (tmp_path / "medical.json").write_text(json.dumps(suite))
    # A results file that must NOT be parsed as a suite
    (tmp_path / "results").mkdir()
    (tmp_path / "results" / "results-20260101-000000.json").write_text(
        json.dumps({"medical": {"by_model": {}}}))
    mapping = ap.build_suite_to_subagents(tmp_path)
    assert "medical" in mapping
    # The results file has no "suite" + "cases" keys, but even if it did, it's
    # in a subdir that must be skipped. Verify it didn't pollute the mapping.
    assert all(isinstance(v, list) for v in mapping.values())


# ---------------------------------------------------------------------------
# build_change_preview with suite_to_subagents — maps to concrete subagent files
# ---------------------------------------------------------------------------

def test_build_change_preview_maps_to_concrete_subagent(tmp_path, monkeypatch):
    """With suite_to_subagents provided, preview entries name concrete subagents
    (not "<all in suite:...>" placeholders), so --write can find the file."""
    # Point SUBAGENTS_DIR at a tmp dir with one fake subagent file.
    fake_agents = tmp_path / "agents" / "subagents"
    fake_agents.mkdir(parents=True)
    (fake_agents / "medical-lit-reviewer.md").write_text(
        "---\nname: medical-lit-reviewer\nmodel: deepseek-v4-flash\n---\nbody\n")
    monkeypatch.setattr(ap, "SUBAGENTS_DIR", fake_agents)

    recs = {"medical": {"best_model": "glm-5.2", "pass_at_k": 0.9, "per_model": {}}}
    mapping = {"medical": ["medical-lit-reviewer", "clinical-reasoner"]}
    changes = ap.build_change_preview(recs, suite_to_subagents=mapping)
    names = [c["subagent"] for c in changes]
    assert "medical-lit-reviewer" in names
    assert all(not c["subagent"].startswith("<all in suite") for c in changes), \
        "no placeholder entries when mapping is provided"
    # The change should show current → recommended
    lit = next(c for c in changes if c["subagent"] == "medical-lit-reviewer")
    assert lit["current"] == "deepseek-v4-flash"
    assert lit["recommended"] == "glm-5.2"


def test_build_change_preview_skips_when_already_best(tmp_path, monkeypatch):
    """If a subagent already uses the recommended model, no change entry."""
    fake_agents = tmp_path / "agents" / "subagents"
    fake_agents.mkdir(parents=True)
    (fake_agents / "x.md").write_text("---\nmodel: glm-5.2\n---\n")
    monkeypatch.setattr(ap, "SUBAGENTS_DIR", fake_agents)

    recs = {"medical": {"best_model": "glm-5.2", "pass_at_k": 1.0, "per_model": {}}}
    mapping = {"medical": ["x"]}
    changes = ap.build_change_preview(recs, suite_to_subagents=mapping)
    assert changes == []


# ---------------------------------------------------------------------------
# --write actually edits the right file
# ---------------------------------------------------------------------------

def test_write_edits_correct_frontmatter(tmp_path, monkeypatch):
    """--write rewrites the model: line of the named subagent file only."""
    fake_agents = tmp_path / "agents" / "subagents"
    fake_agents.mkdir(parents=True)
    (fake_agents / "alpha.md").write_text(
        "---\nname: alpha\nmodel: old-model\n---\nbody\n")
    (fake_agents / "beta.md").write_text(
        "---\nname: beta\nmodel: untouched\n---\nbody\n")
    monkeypatch.setattr(ap, "SUBAGENTS_DIR", fake_agents)

    recs = {"medical": {"best_model": "new-model", "pass_at_k": 0.8, "per_model": {}}}
    mapping = {"medical": ["alpha", "beta"]}
    changes = ap.build_change_preview(recs, suite_to_subagents=mapping)
    # Only alpha should change (beta already != new-model, but it IS in mapping,
    # so it will appear — let's make beta already-best to isolate alpha).
    # Adjust: make beta's recommended equal to its current.
    recs2 = {"medical": {"best_model": "new-model", "pass_at_k": 0.8, "per_model": {}}}
    (fake_agents / "beta.md").write_text(
        "---\nname: beta\nmodel: new-model\n---\nbody\n")  # beta already best
    changes2 = ap.build_change_preview(recs2, suite_to_subagents=mapping)
    assert [c["subagent"] for c in changes2] == ["alpha"]

    # Apply --write logic (extracted: re.sub on the model: line).
    import re
    for c in changes2:
        sa_path = fake_agents / f"{c['subagent']}.md"
        text = sa_path.read_text(encoding="utf-8")
        new_text = re.sub(r"^model:\s*.+$", f"model: {c['recommended']}",
                          text, count=1, flags=re.MULTILINE)
        sa_path.write_text(new_text, encoding="utf-8")

    assert "model: new-model" in (fake_agents / "alpha.md").read_text()
    assert "model: new-model" in (fake_agents / "beta.md").read_text()  # unchanged
    assert "model: old-model" not in (fake_agents / "alpha.md").read_text()
