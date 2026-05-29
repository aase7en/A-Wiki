#!/usr/bin/env bash
# update-ai-model-intel.sh — cache current AI model/agent routing intelligence.
#
# Default output is gitignored: .tmp/model-intel/latest.md
# SessionStart calls this with --offline-ok, so missing keys or network failures
# never block A-Wiki startup.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${AWIKI_MODEL_INTEL_OUT:-$REPO_ROOT/.tmp/model-intel/latest.md}"
MAX_AGE_HOURS="${AWIKI_MODEL_INTEL_MAX_AGE_HOURS:-24}"
FORCE=0
PRINT=0
OFFLINE_OK=0
MODEL="${AWIKI_MODEL_INTEL_MODEL:-gemini-2.5-flash}"
TIMEOUT="${AWIKI_MODEL_INTEL_TIMEOUT:-30}"

usage() {
  cat <<'EOF'
Usage: bash scripts/update-ai-model-intel.sh [--force] [--print] [--offline-ok]
       [--out PATH] [--max-age-hours N]

Writes a compact, cached model-routing briefing using Gemini API grounding.
Output defaults to .tmp/model-intel/latest.md so the repository stays clean.

Environment:
  AWIKI_MODEL_INTEL_ON_START=0     Disable session-start refresh
  GEMINI_API_KEY or GOOGLE_AI_STUDIO_KEY
  AWIKI_MODEL_INTEL_OUT=PATH       Override output path
  AWIKI_MODEL_INTEL_MAX_AGE_HOURS=24
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --force) FORCE=1; shift ;;
    --print) PRINT=1; shift ;;
    --offline-ok) OFFLINE_OK=1; shift ;;
    --out)
      [ $# -lt 2 ] && { echo "--out requires a path" >&2; exit 3; }
      OUT="$2"; shift 2 ;;
    --max-age-hours)
      [ $# -lt 2 ] && { echo "--max-age-hours requires a number" >&2; exit 3; }
      MAX_AGE_HOURS="$2"; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    *) echo "Unknown flag: $1" >&2; usage >&2; exit 3 ;;
  esac
done

if [ "${AWIKI_MODEL_INTEL_ON_START:-1}" = "0" ]; then
  echo "model intel disabled: AWIKI_MODEL_INTEL_ON_START=0" >&2
  exit 0
fi

is_fresh() {
  [ -f "$OUT" ] || return 1
  python3 - "$OUT" "$MAX_AGE_HOURS" <<'PY'
from __future__ import annotations

import os
import sys
import time

path = sys.argv[1]
max_age_hours = float(sys.argv[2])
age_seconds = time.time() - os.path.getmtime(path)
raise SystemExit(0 if age_seconds <= max_age_hours * 3600 else 1)
PY
}

if [ "$FORCE" != "1" ] && is_fresh; then
  echo "model intel cache fresh: $OUT" >&2
  [ "$PRINT" = "1" ] && cat "$OUT"
  exit 0
fi

if [ -z "${GEMINI_API_KEY:-}" ] && [ -n "${GOOGLE_AI_STUDIO_KEY:-}" ]; then
  export GEMINI_API_KEY="$GOOGLE_AI_STUDIO_KEY"
fi

if [ -z "${GEMINI_API_KEY:-}" ]; then
  echo "model intel skipped: GEMINI_API_KEY/GOOGLE_AI_STUDIO_KEY not set" >&2
  [ "$OFFLINE_OK" = "1" ] && exit 0
  exit 2
fi

mkdir -p "$(dirname "$OUT")"
TMP_JSON="$(mktemp)"
TMP_MD="$(mktemp)"
trap 'rm -f "$TMP_JSON" "$TMP_MD"' EXIT

TODAY="$(date +%Y-%m-%d)"
PROMPT="As of $TODAY, find current public information about newly released or materially updated AI models, free/cheap model APIs, and AI agent coding harnesses that affect a cost-first personal agent router. Return a concise briefing for A-Wiki with: 1) a routing table from easy/free tasks to stronger paid fallbacks, 2) notable model or agent releases, 3) caveats where pricing, free tier, or availability may change. Prefer official sources and clearly mark uncertainty. Keep it under 900 words."
ESCAPED_PROMPT="$(printf '%s' "$PROMPT" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')"

curl -sS --max-time "$TIMEOUT" \
  "https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:generateContent" \
  -H "x-goog-api-key: ${GEMINI_API_KEY}" \
  -H "Content-Type: application/json" \
  -X POST \
  -d "{
    \"contents\": [{\"parts\": [{\"text\": ${ESCAPED_PROMPT}}]}],
    \"tools\": [{\"google_search\": {}}],
    \"generationConfig\": {\"temperature\": 0.2, \"maxOutputTokens\": 2048}
  }" > "$TMP_JSON" || {
    echo "model intel update failed: network/API request error" >&2
    [ "$OFFLINE_OK" = "1" ] && exit 0
    exit 1
  }

python3 - "$TMP_JSON" "$TMP_MD" "$TODAY" "$MODEL" <<'PY'
from __future__ import annotations

import json
import sys

src, dst, today, model = sys.argv[1:5]
data = json.loads(open(src, encoding="utf-8").read())

if "error" in data:
    err = data["error"]
    message = err.get("message", "unknown Gemini API error")
    raise SystemExit(f"Gemini API error: {message}")

candidates = data.get("candidates") or []
parts = []
sources: list[tuple[str, str]] = []
for cand in candidates[:1]:
    for part in cand.get("content", {}).get("parts", []):
        text = part.get("text")
        if text:
            parts.append(text.strip())
    metadata = cand.get("groundingMetadata") or cand.get("grounding_metadata") or {}
    for chunk in metadata.get("groundingChunks", []) or metadata.get("grounding_chunks", []):
        web = chunk.get("web") or {}
        uri = str(web.get("uri") or "").strip()
        title = str(web.get("title") or uri).strip()
        if uri:
            sources.append((title, uri))

body = "\n\n".join(parts).strip()
if not body:
    raise SystemExit("Gemini response had no text")

deduped = []
seen = set()
for title, uri in sources:
    if uri in seen:
        continue
    seen.add(uri)
    deduped.append((title, uri))

lines = [
    "---",
    "generated: " + today,
    "source: Gemini API with google_search grounding",
    "cache: local gitignored .tmp/model-intel by default",
    "---",
    "",
    "# AI Model Intel Cache",
    "",
    f"> Generated by `{model}` on {today}. Treat pricing/free-tier claims as volatile.",
    "",
    body,
]
if deduped:
    lines.extend(["", "## Sources"])
    for title, uri in deduped[:12]:
        lines.append(f"- [{title}]({uri})")

open(dst, "w", encoding="utf-8").write("\n".join(lines).rstrip() + "\n")
PY

mv "$TMP_MD" "$OUT"
echo "model intel updated: $OUT" >&2
[ "$PRINT" = "1" ] && cat "$OUT"
