"""Tests for eval suite validity across all evals/subagents/*.json.

Q3 adds two new suites (thai.json, adversarial.json). This test file validates
the structural integrity of ALL suites (existing + new) so a malformed suite
is caught before eval --apply wastes API calls.

Run via: python -m pytest tests/test_eval_suites.py -v
"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SUITES_DIR = REPO_ROOT / "evals" / "subagents"
SUBAGENTS_DIR = REPO_ROOT / "agents" / "subagents"

sys.path.insert(0, str(REPO_ROOT / "scripts" / "eval"))
import run_subagent_eval as ev  # noqa: E402


def _all_suites():
    """Return [(name, parsed_dict), ...] for every *.json suite (not results/).

    Excludes pipeline suites (which use 'stages' not 'cases') — those are
    validated by test_run_pipeline_eval.py.
    """
    out = []
    for p in sorted(SUITES_DIR.glob("*.json")):
        if p.parent.name == "results":
            continue
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass  # malformed — caught by test below
        else:
            # Skip pipeline suites (different schema — 'stages' not 'cases').
            if "stages" in d:
                continue
            out.append((p.stem, d))
    return out


def _existing_subagent_names():
    """Set of subagent names derived from agents/subagents/*.md frontmatter."""
    import re
    names = set()
    for p in SUBAGENTS_DIR.glob("*.md"):
        m = re.search(r"^name:\s*[\"']?([^\"'\n]+)[\"']?\s*$",
                      p.read_text(encoding="utf-8", errors="replace"), re.MULTILINE)
        names.add(m.group(1).strip() if m else p.stem)
    return names


# ---------------------------------------------------------------------------
# Structural validity — every suite must parse + have required keys
# ---------------------------------------------------------------------------

def test_all_suite_files_parse():
    """Every *.json in evals/subagents/ must be valid JSON."""
    for p in SUITES_DIR.glob("*.json"):
        if p.parent.name == "results":
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        assert isinstance(d, dict), f"{p.name} is not a dict"


def test_all_suites_have_required_keys():
    """Every (non-pipeline) suite must have 'suite' and 'cases' keys.
    Pipeline suites (with 'stages') are validated separately."""
    for name, d in _all_suites():
        assert "suite" in d, f"{name}.json missing 'suite' key"
        assert "cases" in d, f"{name}.json missing 'cases' key"
        assert isinstance(d["cases"], list), f"{name}.json 'cases' is not a list"


def test_every_case_has_required_fields():
    """Every case must have id, subagent, prompt, required, forbidden."""
    for name, d in _all_suites():
        for i, c in enumerate(d["cases"]):
            for field in ("id", "subagent", "prompt"):
                assert field in c, f"{name}.json case[{i}] missing '{field}'"
            assert "required" in c, f"{name}.json case[{i}] missing 'required'"
            assert "forbidden" in c, f"{name}.json case[{i}] missing 'forbidden'"
            assert isinstance(c["required"], list), \
                f"{name}.json case[{i}] 'required' is not a list"
            assert isinstance(c["forbidden"], list), \
                f"{name}.json case[{i}] 'forbidden' is not a list"


def test_suite_name_matches_filename():
    """The 'suite' field value should match the filename stem (convention)."""
    for name, d in _all_suites():
        assert d["suite"] == name, \
            f"{name}.json has suite='{d['suite']}' (expected '{name}')"


def test_case_ids_unique_within_suite():
    """Case IDs within a suite must be unique (judge() uses them as keys)."""
    for name, d in _all_suites():
        ids = [c["id"] for c in d["cases"]]
        assert len(ids) == len(set(ids)), \
            f"{name}.json has duplicate case IDs: {ids}"


# ---------------------------------------------------------------------------
# Subagent reference validity — every case's subagent must exist
# ---------------------------------------------------------------------------

def test_all_case_subagents_exist():
    """Every case's 'subagent' field must map to an existing agents/subagents/*.md."""
    existing = _existing_subagent_names()
    for name, d in _all_suites():
        for i, c in enumerate(d["cases"]):
            sa = c["subagent"]
            assert sa in existing, \
                f"{name}.json case[{i}] references unknown subagent '{sa}'"


# ---------------------------------------------------------------------------
# Thai suite specific (Q3) — must contain Thai-language prompts
# ---------------------------------------------------------------------------

def test_thai_suite_exists():
    """Q3: thai.json suite must exist."""
    assert (SUITES_DIR / "thai.json").is_file(), "thai.json suite missing"


def test_thai_suite_has_thai_prompts():
    """Q3: thai.json cases must contain actual Thai characters (non-ASCII)."""
    p = SUITES_DIR / "thai.json"
    if not p.is_file():
        return  # covered by test_thai_suite_exists
    d = json.loads(p.read_text(encoding="utf-8"))
    thai_count = 0
    for c in d["cases"]:
        # Thai Unicode range: U+0E00–U+0E7F
        if any("\u0e00" <= ch <= "\u0e7f" for ch in c.get("prompt", "")):
            thai_count += 1
    assert thai_count >= 10, \
        f"thai.json should have >=10 Thai-character prompts, found {thai_count}"


def test_thai_suite_references_thai_subagents():
    """Q3: thai.json should test the Thai-variant subagents (-th suffix)."""
    p = SUITES_DIR / "thai.json"
    if not p.is_file():
        return
    d = json.loads(p.read_text(encoding="utf-8"))
    subagents = {c["subagent"] for c in d["cases"]}
    th_variants = {s for s in subagents if s.endswith("-th")}
    assert len(th_variants) >= 2, \
        f"thai.json should reference >=2 -th subagents, found {th_variants}"


# ---------------------------------------------------------------------------
# Adversarial suite specific (Q3) — wrong-answer traps
# ---------------------------------------------------------------------------

def test_adversarial_suite_exists():
    """Q3: adversarial.json suite must exist."""
    assert (SUITES_DIR / "adversarial.json").is_file(), "adversarial.json missing"


def test_adversarial_suite_has_forbidden_keywords():
    """Q3: adversarial.json cases must have non-empty 'forbidden' (the trap)."""
    p = SUITES_DIR / "adversarial.json"
    if not p.is_file():
        return
    d = json.loads(p.read_text(encoding="utf-8"))
    with_traps = sum(1 for c in d["cases"] if len(c.get("forbidden", [])) > 0)
    assert with_traps >= 10, \
        f"adversarial.json should have >=10 cases with forbidden traps, found {with_traps}"


# ---------------------------------------------------------------------------
# Integration — load_suite works on new suites
# ---------------------------------------------------------------------------

def test_load_suite_works_on_thai():
    """run_subagent_eval.load_suite must parse thai.json."""
    p = SUITES_DIR / "thai.json"
    if not p.is_file():
        return
    loaded = ev.load_suite(p)
    assert loaded is not None
    assert loaded["suite"] == "thai"


def test_load_suite_works_on_adversarial():
    """run_subagent_eval.load_suite must parse adversarial.json."""
    p = SUITES_DIR / "adversarial.json"
    if not p.is_file():
        return
    loaded = ev.load_suite(p)
    assert loaded is not None
    assert loaded["suite"] == "adversarial"
