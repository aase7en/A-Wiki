#!/usr/bin/env bash
# Resolve private local A-Wiki files with public-clone fallbacks.

awiki_repo_root() {
  local source_path="${BASH_SOURCE[0]:-$0}"
  cd "$(dirname "$source_path")/../.." && pwd
}

awiki_first_existing_file() {
  local candidate
  for candidate in "$@"; do
    if [ -f "$candidate" ]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  return 1
}

awiki_session_memory_path() {
  local root="${1:-$(awiki_repo_root)}"
  awiki_first_existing_file \
    "$root/wiki/context/session-memory.md" \
    "$root/drive/personal/journal/wiki-context-session-memory.md" \
    "$root/drive/personal/journal/session-memory.md" \
    "$root/wiki/context/session-memory.md.example"
}

awiki_log_path() {
  local root="${1:-$(awiki_repo_root)}"
  awiki_first_existing_file \
    "$root/log.md" \
    "$root/drive/personal/journal/log.md" \
    "$root/log.md.example"
}
