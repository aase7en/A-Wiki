"""WO-AWIKI-SKILLECO-14 — A/B token measurement fixture contract tests.

Issue #76: "Compare 10+ matched A/B fixtures in Thai/English with
auto-on/auto-off … explicitly disclose UNKNOWN billing where unavailable."

The fixtures are deterministic regression material: no network, no provider
billing — the measurement harness must disclose that (billing UNKNOWN).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

FIXTURE = REPO_ROOT / "tests" / "fixtures" / "token_ab_pairs.json"


def _load():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _variants(pair: dict, lang: str) -> dict:
    return pair[lang]


def test_fixture_exists_with_schema():
    assert FIXTURE.exists(), f"missing fixture: {FIXTURE}"
    data = _load()
    assert data["schema"] == "awiki-token-ab-fixtures/v1"
    assert "billing_disclosure" in data and "UNKNOWN" in data["billing_disclosure"]


def test_at_least_ten_matched_pairs_covering_categories():
    pairs = _load()["pairs"]
    assert len(pairs) >= 10, f"need >=10 pairs, got {len(pairs)}"
    ids = [p["id"] for p in pairs]
    assert len(ids) == len(set(ids)), "pair ids must be unique"
    assert all(p.get("category") for p in pairs), "every pair needs a category"
    assert len({p["category"] for p in pairs}) >= 6, "categories must be diverse (>=6)"


def test_every_pair_has_four_nonempty_variants():
    for p in _load()["pairs"]:
        for lang in ("thai", "english"):
            v = _variants(p, lang)
            for style in ("verbose", "compact"):
                assert isinstance(v.get(style), str) and v[style].strip(), (
                    f"pair {p['id']}/{lang}/{style} missing or empty")


def test_compact_is_shorter_than_verbose_in_bytes():
    # caveman contract: compact (auto-on) must not exceed verbose (auto-off)
    for p in _load()["pairs"]:
        for lang in ("thai", "english"):
            v = _variants(p, lang)
            assert len(v["compact"].encode("utf-8")) < len(v["verbose"].encode("utf-8")), (
                f"pair {p['id']}/{lang}: compact not smaller than verbose")


def test_measurement_is_deterministic_and_discloses_unknown():
    from tokenizer_cost import build_counter
    count, backend = build_counter("proxy")  # deterministic backend for the contract
    assert backend == "char/4 proxy"
    pairs = _load()["pairs"]
    for p in pairs:
        for lang in ("thai", "english"):
            v = _variants(p, lang)
            first = {s: count(v[s]) for s in ("verbose", "compact")}
            second = {s: count(v[s]) for s in ("verbose", "compact")}
            assert first == second, f"pair {p['id']}/{lang}: non-deterministic counts"
            assert all(n >= 1 for n in first.values())


def test_measure_script_emits_jsonl_with_unknown_billing():
    import subprocess
    r = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "token-ab-measure.py"), "--json"],
        capture_output=True, text=True, encoding="utf-8", timeout=120)
    assert r.returncode == 0, r.stderr[:300]
    lines = [ln for ln in r.stdout.splitlines() if ln.strip()]
    assert lines, "no JSONL output"
    records = [json.loads(ln) for ln in lines]
    summary = [rec for rec in records if rec.get("record") == "summary"]
    assert summary, "missing summary record"
    assert "UNKNOWN" in summary[0]["billing"], "summary must disclose UNKNOWN billing"
    assert summary[0]["tokenizer"], "summary must name the tokenizer backend"
    per_pair = [rec for rec in records if rec.get("record") == "pair"]
    assert len(per_pair) >= 10
    for rec in per_pair:
        for key in ("thai_verbose_tokens", "english_verbose_tokens",
                    "thai_compact_tokens", "english_compact_tokens",
                    "thai_ratio", "english_compact_ratio"):
            assert key in rec, f"pair record missing {key}"
