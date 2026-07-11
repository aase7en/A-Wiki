#!/usr/bin/env bash
# SessionStart: scan raw/ for gitignored files not yet in local-sources.md manifest

# Lean mode (token-save): skip informational session-start output
if [ "${AWIKI_LEAN_SESSION_START:-0}" = "1" ]; then exit 0; fi

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO"

MANIFEST="wiki/context/local-sources.md"
[ -f "$MANIFEST" ] || { echo "⚠️  local-sources.md ไม่มี — สร้างก่อน" >&2; exit 0; }

UNREGISTERED=()
while IFS= read -r -d '' f; do
  BASENAME=$(basename "$f")
  grep -qF "$BASENAME" "$MANIFEST" 2>/dev/null || UNREGISTERED+=("$f")
done < <(find raw/ -type f \( \
  -name "*.pdf" -o -name "*.json" -o -name "*.csv" \
  -o -name "*.xlsx" -o -name "*.xls" \
  -o -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" \
  \) -print0 2>/dev/null)

if [ ${#UNREGISTERED[@]} -gt 0 ]; then
  echo "⚠️  พบ local-only files ที่ยังไม่อยู่ใน manifest (${#UNREGISTERED[@]} ไฟล์):" >&2
  for f in "${UNREGISTERED[@]}"; do echo "    • $f" >&2; done
  echo "    → เพิ่มใน wiki/context/local-sources.md หลัง ingest" >&2
else
  echo "✅ local-sources manifest ครบ (ไม่มีไฟล์ใหม่)" >&2
fi
