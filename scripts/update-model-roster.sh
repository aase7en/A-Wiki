#!/usr/bin/env bash
# scripts/update-model-roster.sh — Scout & update model-roster.conf from OpenRouter
#
# Queries OpenRouter API for free models, ranks by quality (context length, 
# reasoning flag, community score), and writes top picks to model-roster.conf.
#
# Usage:  scripts/update-model-roster.sh
# Requires: OPENROUTER_API_KEY env var
# Output:  wiki/context/model-roster.conf (sourced by scripts/delegate.sh)
#
# Exit: 0=updated  1=failed  2=no key

set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ROSTER_CONF="$REPO_ROOT/wiki/context/model-roster.conf"
POLICY_SCRIPT="$REPO_ROOT/scripts/model-router-policy.py"

# ─── Key check ────────────────────────────────────────────────────────────────
if [ -z "${OPENROUTER_API_KEY:-}" ]; then
  echo "❌ OPENROUTER_API_KEY not set. Cannot query model roster." >&2
  exit 2
fi

# ─── Fetch free models from OpenRouter ────────────────────────────────────────
echo "🔍 Scouting OpenRouter for available free models..." >&2
API_RESPONSE=$(curl -sS --max-time 15 \
  "https://openrouter.ai/api/v1/models" \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" 2>/dev/null) || {
  echo "❌ Failed to fetch models from OpenRouter API (network error)" >&2
  exit 1
}

TEMP_DIR=$(mktemp -d)
trap "rm -rf '$TEMP_DIR'" EXIT

# ─── Python: parse, rank, generate roster ────────────────────────────────────
printf '%s' "$API_RESPONSE" > "$TEMP_DIR/models.json"
python3 - "$TEMP_DIR/models.json" > "$TEMP_DIR/new_roster.conf" <<'PY' || {
import json, sys
from datetime import date

with open(sys.argv[1], "r", encoding="utf-8") as fh:
    raw = fh.read()
data = json.loads(raw)
models = data.get("data", [])

# Filter: free models only
free_models = []
for m in models:
    pricing = m.get("pricing", {}) or {}
    prompt_price = float(pricing.get("prompt", 1))
    completion_price = float(pricing.get("completion", 1))
    input_price = float(pricing.get("input", 1))
    output_price = float(pricing.get("output", 1))
    is_free = (prompt_price == 0 and completion_price == 0) or (input_price == 0 and output_price == 0)
    if not is_free:
        continue
    model_id = m.get("id", "")
    if "/free" in model_id:
        continue
    context_length = m.get("context_length", 0) or 0
    score = min(context_length / 1000, 200)
    name_lower = model_id.lower()
    if "reasoning" in name_lower or "r1" in name_lower:
        score += 50
    free_models.append({"id": model_id, "context": context_length, "score": score})

free_models.sort(key=lambda x: -x["score"])

def free_id(model_id):
    if model_id.endswith(":free"):
        return model_id
    return model_id + ":free"

tier1_candidates = [m for m in free_models if m["context"] >= 64000]
tier2_candidates = [m for m in free_models if "reasoning" in m["id"].lower() or "r1" in m["id"].lower()]
tier3_candidates = [m for m in free_models if m["context"] >= 128000]

# Fallback defaults
FALLBACK_T1_PRIMARY = "google/gemini-2.5-flash:free"
FALLBACK_T1_FB = ["deepseek/deepseek-chat-v3-0324:free", "qwen/qwen3-30b-a3b:free", "meta-llama/llama-3.3-70b-instruct:free"]
FALLBACK_T2_PRIMARY = "deepseek/deepseek-r1:free"
FALLBACK_T2_FB = ["google/gemini-2.5-flash:free", "openrouter/auto"]
FALLBACK_T3_PRIMARY = "google/gemini-2.5-flash:free"
FALLBACK_T3_FB = ["qwen/qwen3-30b-a3b:free", "openai/gpt-4o-mini"]
FALLBACK_RACE = "deepseek/deepseek-chat-v3-0324:free google/gemini-2.5-flash:free qwen/qwen3-235b-a22b:free"

lines = []
lines.append("# model-roster.conf — Dynamic model roster (auto-generated)")
lines.append(f"# Generated: {date.today().isoformat()}")
lines.append(f"# Free models available: {len(free_models)}")
lines.append("")

# Tier 1
lines.append("# Tier 1: Search / Lookup / Summarize")
if tier1_candidates:
    lines.append(f"TIER1_PRIMARY=\"{free_id(tier1_candidates[0]['id'])}\"")
    for i, m in enumerate(tier1_candidates[1:4]):
        lines.append(f"TIER1_FALLBACK{i+1}=\"{free_id(m['id'])}\"")
else:
    lines.append(f"TIER1_PRIMARY=\"{FALLBACK_T1_PRIMARY}\"")
    for i, fb in enumerate(FALLBACK_T1_FB):
        lines.append(f"TIER1_FALLBACK{i+1}=\"{fb}\"")
lines.append("")

# Tier 2
lines.append("# Tier 2: Reason / Compare / Analyze")
if tier2_candidates:
    lines.append(f"TIER2_PRIMARY=\"{free_id(tier2_candidates[0]['id'])}\"")
    remaining = tier2_candidates[1:3] if len(tier2_candidates) >= 3 else free_models[1:3] if len(free_models) >= 3 else []
    for i, m in enumerate(remaining[:2]):
        lines.append(f"TIER2_FALLBACK{i+1}=\"{free_id(m['id'])}\"")
else:
    lines.append(f"TIER2_PRIMARY=\"{FALLBACK_T2_PRIMARY}\"")
    for i, fb in enumerate(FALLBACK_T2_FB):
        lines.append(f"TIER2_FALLBACK{i+1}=\"{fb}\"")
lines.append("")

# Tier 3
lines.append("# Tier 3: Scan / Long context")
if tier3_candidates:
    lines.append(f"TIER3_PRIMARY=\"{free_id(tier3_candidates[0]['id'])}\"")
    if len(tier3_candidates) > 1:
        lines.append(f"TIER3_FALLBACK1=\"{free_id(tier3_candidates[1]['id'])}\"")
    else:
        lines.append(f"TIER3_FALLBACK1=\"{FALLBACK_T3_FB[0]}\"")
else:
    lines.append(f"TIER3_PRIMARY=\"{FALLBACK_T3_PRIMARY}\"")
    lines.append(f"TIER3_FALLBACK1=\"{FALLBACK_T3_FB[0]}\"")
lines.append(f"TIER3_FALLBACK2=\"{FALLBACK_T3_FB[1]}\"")
lines.append("")

# Race
if free_models:
    race_ids = [free_id(m["id"]) for m in free_models[:3]]
    lines.append("# Race models (parallel)")
    lines.append(f"RACE_MODELS=\"{' '.join(race_ids)}\"")
else:
    lines.append("# Race models (parallel)")
    lines.append(f"RACE_MODELS=\"{FALLBACK_RACE}\"")

for line in lines:
    print(line)
PY
  echo "❌ Python roster generation failed" >&2
  exit 1
}

# Validate: must have at least TIER1_PRIMARY
if ! grep -q 'TIER1_PRIMARY=' "$TEMP_DIR/new_roster.conf" 2>/dev/null; then
  echo "❌ Generated roster is malformed — keeping existing" >&2
  exit 1
fi

# Backup existing roster if it exists
if [ -f "$ROSTER_CONF" ]; then
  cp "$ROSTER_CONF" "${ROSTER_CONF}.bak"
  echo "📦 Backed up existing roster → ${ROSTER_CONF}.bak" >&2
fi

cp "$TEMP_DIR/new_roster.conf" "$ROSTER_CONF"
echo "✅ Model roster updated: $ROSTER_CONF" >&2

if [ -f "$POLICY_SCRIPT" ]; then
  python3 "$POLICY_SCRIPT" --quiet >/dev/null 2>&1 \
    && echo "✅ Model router policy refreshed" >&2 \
    || echo "⚠️  Model router policy refresh failed — delegate.sh will fallback to roster" >&2
fi
exit 0
