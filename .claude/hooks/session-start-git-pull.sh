#!/usr/bin/env bash
# L0: SessionStart — Hard Sync Gate
# fetch → report delta → pull --rebase (handles ahead+behind, never blocks)
set -uo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO"

LOAD_KEYS="$REPO/scripts/hooks/load-drive-keys.sh"
if [[ -f "$LOAD_KEYS" ]]; then
  # shellcheck source=scripts/hooks/load-drive-keys.sh
  source "$LOAD_KEYS" >/dev/null 2>&1 || true
fi

git remote get-url origin >/dev/null 2>&1 || exit 0

# Always on main
CURRENT="$(git branch --show-current 2>/dev/null || echo "")"
if [[ "$CURRENT" != "main" ]]; then
  git checkout main 2>/dev/null || true
fi

# Fetch remote refs (fast — no merge yet)
git fetch origin main --quiet 2>/dev/null || { echo "[sync] ⚠️  fetch failed (offline?)" >&2; exit 0; }

# Save fetch timestamp for Edit Guardian (L1)
date +%s > .git/LAST_FETCH_TIME 2>/dev/null

BEHIND=$(git rev-list HEAD..origin/main --count 2>/dev/null || echo 0)
AHEAD=$(git rev-list origin/main..HEAD --count 2>/dev/null || echo 0)

if [ "$BEHIND" -eq 0 ] && [ "$AHEAD" -eq 0 ]; then
  echo "[sync] ✅ up-to-date (origin/main)" >&2
fi

if [ "$BEHIND" -gt 0 ]; then
  echo "[sync] 📥 pulling $BEHIND new commit(s) from origin/main..." >&2
  if git pull --rebase origin main --quiet 2>/dev/null; then
    echo "[sync] ✅ synced — changes since last session:" >&2
    git log --oneline ORIG_HEAD..HEAD 2>/dev/null | head -10 | sed 's/^/  /' >&2 || true
  else
    echo "[sync] ⚠️  rebase conflict — run: git rebase --abort && git pull origin main" >&2
  fi
fi

[ "$AHEAD" -gt 0 ] && echo "[sync] ℹ️  $AHEAD local commit(s) pending push (will push at session end)" >&2

# --- API Key status (Cost Pyramid L1-L2 readiness) ---
# Accept both canonical names + common aliases from Google AI Studio / Project Settings
KEYS_FOUND=()
KEYS_MISSING=()
[ -n "${DEEPSEEK_API_KEY:-}" ]                                              && KEYS_FOUND+=("DeepSeek✓")    || KEYS_MISSING+=("DEEPSEEK_API_KEY")
[ -n "${OPENROUTER_API_KEY:-}" ]                                            && KEYS_FOUND+=("OpenRouter✓")  || KEYS_MISSING+=("OPENROUTER_API_KEY")
{ [ -n "${GEMINI_API_KEY:-}" ] || [ -n "${GOOGLE_AI_STUDIO_KEY:-}" ]; }    && KEYS_FOUND+=("Gemini✓")      || KEYS_MISSING+=("GEMINI_API_KEY")
[ -n "${GROQ_API_KEY:-}" ]                                                  && KEYS_FOUND+=("Groq✓")        || KEYS_MISSING+=("GROQ_API_KEY")

if [ ${#KEYS_FOUND[@]} -gt 0 ]; then
  if [ ${#KEYS_MISSING[@]} -gt 0 ]; then
    echo "⚠️  Free-model partial: ✅ ${KEYS_FOUND[*]} | ❌ missing: ${KEYS_MISSING[*]}" >&2
  else
    echo "✅ Free-model keys: ${KEYS_FOUND[*]} — Cost Pyramid L1-L2 fully active" >&2
  fi
else
  echo "❌ No free-model keys found — all search/lookup will use Claude (costs tokens)" >&2
  echo "   Set in Project Settings: OPENROUTER_API_KEY | GOOGLE_AI_STUDIO_KEY | DEEPSEEK_API_KEY | GROQ_API_KEY" >&2
fi

exit 0
