#!/usr/bin/env bash
# Batch GitNexus setup for external/dream project repos.
#
# Usage:
#   AWIKI_DREAM_REPOS="/path/project-a:/path/project-b" bash scripts/setup-dream-gitnexus.sh
#   bash scripts/setup-dream-gitnexus.sh /path/project-a /path/project-b
#
# This script never guesses private paths. Pass explicit repo paths or set
# AWIKI_DREAM_REPOS as a colon-separated list.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

declare -a REPOS=()
if [ "$#" -gt 0 ]; then
  REPOS=("$@")
elif [ -n "${AWIKI_DREAM_REPOS:-}" ]; then
  IFS=':' read -r -a REPOS <<< "$AWIKI_DREAM_REPOS"
else
  echo "Usage: AWIKI_DREAM_REPOS=\"/path/a:/path/b\" bash scripts/setup-dream-gitnexus.sh" >&2
  echo "   or: bash scripts/setup-dream-gitnexus.sh /path/a /path/b" >&2
  exit 2
fi

for repo in "${REPOS[@]}"; do
  if [ ! -d "$repo/.git" ]; then
    echo "WARN: skip non-git repo: $repo" >&2
    continue
  fi
  echo "==> GitNexus setup: $repo"
  bash "$REPO_ROOT/scripts/setup-gitnexus.sh" "$repo"
done

