#!/usr/bin/env bash
# refresh-skillopt.sh — snapshot Microsoft SkillOpt upstream without bloating A-Wiki.
#
# Default mode copies only docs/config/prompts/core optimizer pieces into
# agent-skills/_upstream/skillopt. Heavy assets, data, WebUI, and benchmark
# payloads stay out unless SKILLOPT_FULL_SNAPSHOT=1 is explicitly set.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

REMOTE="${SKILLOPT_REMOTE:-skillopt}"
URL="https://github.com/microsoft/SkillOpt.git"
BRANCH="${SKILLOPT_BRANCH:-main}"
UPSTREAM_DIR="agent-skills/_upstream/skillopt"
FULL="${SKILLOPT_FULL_SNAPSHOT:-0}"

if ! git remote get-url "$REMOTE" >/dev/null 2>&1; then
  echo "-> adding remote $REMOTE -> $URL"
  git remote add "$REMOTE" "$URL"
fi

echo "-> fetching $REMOTE/$BRANCH"
git fetch "$REMOTE" "$BRANCH"
COMMIT="$(git rev-parse "$REMOTE/$BRANCH")"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
git archive --format=tar "$REMOTE/$BRANCH" | tar -x -C "$TMP"

mkdir -p "$UPSTREAM_DIR"
find "$UPSTREAM_DIR" -mindepth 1 -delete

if [ "$FULL" = "1" ]; then
  echo "-> SKILLOPT_FULL_SNAPSHOT=1, copying full upstream snapshot"
  cp -R "$TMP"/. "$UPSTREAM_DIR"/
else
  echo "-> copying lightweight SkillOpt subset"
  mkdir -p "$UPSTREAM_DIR"
  for path in README.md LICENSE pyproject.toml requirements.txt docs configs/_base_ skillopt/prompts skillopt/evaluation skillopt/optimizer skillopt/envs/_template skillopt/types.py skillopt/utils; do
    if [ -e "$TMP/$path" ]; then
      mkdir -p "$UPSTREAM_DIR/$(dirname "$path")"
      cp -R "$TMP/$path" "$UPSTREAM_DIR/$path"
    fi
  done
fi

cat > "$UPSTREAM_DIR/README.A-WIKI.md" <<EOF
# SkillOpt Upstream Snapshot for A-Wiki

- Upstream: https://github.com/microsoft/SkillOpt.git
- Branch: $BRANCH
- Commit: $COMMIT
- Snapshot mode: $([ "$FULL" = "1" ] && echo full || echo lightweight)

Default A-Wiki policy keeps this snapshot light. The following upstream areas
are intentionally excluded unless SKILLOPT_FULL_SNAPSHOT=1 is set:

- skillopt_webui
- skillopt-assets
- data
- benchmark payloads and generated run outputs

Install runnable SkillOpt locally with:

\`\`\`bash
bash scripts/install-skillopt-local.sh
\`\`\`
EOF

printf '%s\n' "$COMMIT" > "$UPSTREAM_DIR/.upstream-commit"

echo ""
echo "SkillOpt snapshot ready: $UPSTREAM_DIR"
echo "Commit: $COMMIT"
echo ""
echo "Security/weight review hints:"
echo "  rg -n \"subprocess|shell=True|exec\\(|eval\\(|API_KEY|share\" $UPSTREAM_DIR"
echo "  du -sh $UPSTREAM_DIR"
