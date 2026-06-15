"""Tests for GLM/Z.ai engine, provider-enable guards, and capability ranking in delegate.sh."""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
DELEGATE_SH = REPO_ROOT / "scripts" / "swarm" / "delegate.sh"
SCORECARD = REPO_ROOT / "wiki" / "context" / "model-capability-scores.json"


# ── Source-text assertions ────────────────────────────────────────────────────

def _src() -> str:
    return DELEGATE_SH.read_text(encoding="utf-8")


def test_zhipu_engine_defined():
    text = _src()
    assert "try_zhipu_direct()" in text
    assert "$ZHIPU_API_URL" in text
    assert "$ZHIPU_API_KEY" in text
    assert "$ZHIPU_DIRECT_MODEL" in text
    assert "_extract_smart openai" in text  # OpenAI-compatible parser


def test_zhipu_default_is_zai_international():
    text = _src()
    assert "api.z.ai" in text
    assert "glm-4.6" in text


def test_provider_enabled_helper_defined():
    text = _src()
    assert "_provider_enabled()" in text
    assert "AWIKI_DISABLE_" in text


def test_all_engines_respect_disable_flag():
    text = _src()
    for provider in ("GEMINI", "DEEPSEEK", "OPENROUTER", "GROQ", "ANTHROPIC", "ZHIPU"):
        assert f"_provider_enabled {provider}" in text, f"{provider} missing enable guard"


def test_zhipu_wired_into_tier2_and_tier3_after_free():
    text = _src()
    # zhipu appears in the ranked candidate lists for tier 2 and tier 3
    assert text.count('"zhipu|$ZHIPU_DIRECT_MODEL|1"') >= 2
    # cost_rank 1 (paid) ensures it sorts after free (cost_rank 0) candidates


def test_tier1_has_no_paid_zhipu():
    text = _src()
    # Tier 1 branch (search/lookup/summarize) must stay free — no zhipu engine call
    tier1_start = text.index("1)  # search")
    tier2_start = text.index("2)  # reason")
    tier1_block = text[tier1_start:tier2_start]
    assert "zhipu" not in tier1_block.lower()


def test_capability_helpers_defined():
    text = _src()
    assert "_capability_dimension()" in text
    assert "_rank_by_capability()" in text
    assert "_run_ranked()" in text


# ── Capability ranking: cost-first guarantee ───────────────────────────────────

RANK_PY = r'''
import sys, json
dim = sys.argv[1]; card = sys.argv[2]
try:
    fams = json.load(open(card)).get("families", {})
except Exception:
    sys.stdout.write(sys.stdin.read()); sys.exit(0)
def score(mid):
    m = (mid or "").lower()
    for f in fams.values():
        if any(s in m for s in f.get("match", [])):
            return f.get(dim, 50)
    return 50
rows = []
for i, ln in enumerate(sys.stdin.read().splitlines()):
    if not ln.strip(): continue
    parts = (ln.split("|") + ["", "", "9"])[:3]
    eng, mid, cr = parts
    try: cr = int(cr)
    except ValueError: cr = 9
    rows.append((cr, -score(mid), i, ln))
rows.sort()
for r in rows: print(r[3])
'''


def _rank(dim: str, lines: list[str], card: Path = SCORECARD) -> list[str]:
    proc = subprocess.run(
        ["python3", "-c", RANK_PY, dim, str(card)],
        input="\n".join(lines), capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    return [l for l in proc.stdout.splitlines() if l.strip()]


def test_rank_preserves_cost_first():
    # GLM (reasoning 80, paid cost_rank 1) must stay BEHIND a free low-score model
    out = _rank("reasoning", [
        "gemini|gemini-2.5-flash|0",       # free, reasoning 62
        "zhipu|glm-4.6|1",                  # paid, reasoning 80 (higher!)
    ])
    assert out[0].startswith("gemini"), "free model must come first despite lower score"
    assert out[1].startswith("zhipu")


def test_rank_reorders_within_cost_class():
    # Two free models: higher reasoning score should win for a reason task
    out = _rank("reasoning", [
        "gemini|gemini-2.5-flash|0",        # reasoning 62
        "openrouter|qwen/qwen3-235b:free|0", # reasoning 66
    ])
    assert out[0].startswith("openrouter"), "higher-capability free model should rank first"


def test_rank_falls_back_when_no_card():
    missing = Path(tempfile.gettempdir()) / "no-such-scorecard-xyz.json"
    if missing.exists():
        missing.unlink()
    lines = ["gemini|x|0", "zhipu|glm-4.6|1"]
    out = _rank("reasoning", lines, card=missing)
    assert out == lines  # unchanged order


# ── Behavioral: disable flag actually skips the engine ─────────────────────────

def test_disable_zhipu_skips_engine(tmp_path):
    """With AWIKI_DISABLE_ZHIPU=1, zhipu must never emit a delegate_start event."""
    log = REPO_ROOT / ".tmp" / "live-events.jsonl"
    log.parent.mkdir(exist_ok=True)
    log.write_text("", encoding="utf-8")

    env = dict(os.environ)
    env.update({
        "DELEGATE_TIMEOUT": "2",
        "GEMINI_API_KEY": "dummy",  # prevents drive-key load (not all 5 empty)
        "ZHIPU_API_KEY": "dummy",
        "AWIKI_DISABLE_GEMINI": "1", "AWIKI_DISABLE_OPENROUTER": "1",
        "AWIKI_DISABLE_DEEPSEEK": "1", "AWIKI_DISABLE_GROQ": "1",
        "AWIKI_DISABLE_ANTHROPIC": "1", "AWIKI_DISABLE_ZHIPU": "1",
        "HOOK_SKIP": "check_cost_tier",
    })
    subprocess.run(["bash", str(DELEGATE_SH), "reason", "ping"],
                   env=env, capture_output=True, text=True, timeout=30)
    import time
    time.sleep(0.5)
    content = log.read_text(encoding="utf-8")
    assert "zhipu" not in content, "disabled zhipu must not run"


def test_extract_openai_parses_glm_response():
    """GLM/Z.ai returns OpenAI-shaped completions — the openai extractor must handle it."""
    extractor = REPO_ROOT / "scripts" / "_extract_response.py"
    payload = {"choices": [{"message": {"role": "assistant", "content": "GLM_LANE_OK"}}]}
    proc = subprocess.run(["python3", str(extractor), "openai"],
                          input=json.dumps(payload), capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    assert "GLM_LANE_OK" in proc.stdout


# ── Scorecard schema ───────────────────────────────────────────────────────────

def test_scorecard_schema_valid():
    data = json.loads(SCORECARD.read_text(encoding="utf-8"))
    fams = data["families"]
    assert "glm" in fams
    dims = ("swe_bench", "terminal_bench", "nl2repobench", "reasoning", "speed")
    for name, fam in fams.items():
        assert "match" in fam and fam["match"], f"{name} missing match"
        assert "confidence" in fam, f"{name} missing confidence"
        assert "as_of" in fam, f"{name} missing as_of"
        for d in dims:
            assert isinstance(fam.get(d), (int, float)), f"{name} missing dimension {d}"
