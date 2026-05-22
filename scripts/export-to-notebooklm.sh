#!/usr/bin/env bash
# scripts/export-to-notebooklm.sh
#
# Bundle wiki content per domain into NotebookLM-friendly Markdown.
#
# Usage:
#   bash scripts/export-to-notebooklm.sh                # all domains
#   bash scripts/export-to-notebooklm.sh ai-tools       # single domain
#   bash scripts/export-to-notebooklm.sh ai-tools env   # multiple
#
# Output: exports/notebooklm/<domain>.md
#
# Why: NotebookLM works best with one consolidated source per topic.
# Bundling keeps cross-references intact while staying within the
# ~50 sources / 500K words per source NotebookLM Pro limit.

set -euo pipefail

# Resolve repo root (script may be run from anywhere)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

OUT_DIR="exports/notebooklm"
mkdir -p "${OUT_DIR}"

KNOWN_DOMAINS=(iot env ai-tools pharmacy)

usage() {
  cat <<EOF
Usage: bash scripts/export-to-notebooklm.sh [DOMAIN ...]

Domains: ${KNOWN_DOMAINS[*]}
No args = export all domains.

Output: ${OUT_DIR}/<domain>.md
EOF
}

bundle_file() {
  local src="$1"
  local out="$2"
  [[ -f "${src}" ]] || return 0
  printf '\n### `%s`\n\n' "${src}" >> "${out}"
  cat "${src}" >> "${out}"
  printf '\n\n---\n' >> "${out}"
}

bundle_dir() {
  local dir="$1"
  local out="$2"
  local heading="$3"
  [[ -d "${dir}" ]] || return 0
  local files=( "${dir}"/*.md )
  [[ -e "${files[0]}" ]] || return 0
  printf '\n## %s\n' "${heading}" >> "${out}"
  for f in "${files[@]}"; do
    bundle_file "${f}" "${out}"
  done
}

bundle_domain() {
  local domain="$1"
  local out="${OUT_DIR}/${domain}.md"

  # Header
  {
    printf '# Wiki Snapshot — %s domain\n\n' "${domain}"
    printf '**Snapshot**: %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    printf '**Repo**: aase7en/aase7en-inw-wiki\n'
    printf '**Commit**: %s\n' "$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
    printf '**Generator**: scripts/export-to-notebooklm.sh\n\n'
    printf '> ใช้กับ NotebookLM Pro: upload ไฟล์นี้เป็น single source ใน notebook ของ domain %s\n' "${domain}"
    printf '> สำหรับคำถามเชิงโครงสร้าง/อ้างอิง — ไม่ใช่ source-of-truth (ของจริงอยู่ใน wiki/ ของ repo)\n\n'
    printf -- '---\n'
  } > "${out}"

  # Domain index
  if [[ -f "index-${domain}.md" ]]; then
    {
      printf '\n## Domain Index\n\n'
      printf '### `index-%s.md`\n\n' "${domain}"
      cat "index-${domain}.md"
      printf '\n\n---\n'
    } >> "${out}"
  fi

  # Entities + Concepts (domain-scoped)
  bundle_dir "wiki/entities/${domain}" "${out}" "Entities (${domain})"
  bundle_dir "wiki/concepts/${domain}" "${out}" "Concepts (${domain})"

  # Sources tagged with this domain (best-effort grep on frontmatter)
  if [[ -d "wiki/sources" ]]; then
    local matched=()
    while IFS= read -r f; do
      if grep -qiE "(tags:.*\\b${domain}\\b|original_file:.*${domain}|^${domain}:)" "${f}" 2>/dev/null; then
        matched+=( "${f}" )
      fi
    done < <(find wiki/sources -maxdepth 2 -name '*.md' -type f 2>/dev/null)

    if [[ ${#matched[@]} -gt 0 ]]; then
      printf '\n## Sources tagged with `%s`\n' "${domain}" >> "${out}"
      for f in "${matched[@]}"; do
        bundle_file "${f}" "${out}"
      done
    fi
  fi

  # Synthesis touching this domain
  if [[ -d "wiki/synthesis" ]]; then
    local matched=()
    while IFS= read -r f; do
      if grep -qiE "\\b${domain}\\b" "${f}" 2>/dev/null; then
        matched+=( "${f}" )
      fi
    done < <(find wiki/synthesis -maxdepth 2 -name '*.md' -type f 2>/dev/null)

    if [[ ${#matched[@]} -gt 0 ]]; then
      printf '\n## Synthesis touching `%s`\n' "${domain}" >> "${out}"
      for f in "${matched[@]}"; do
        bundle_file "${f}" "${out}"
      done
    fi
  fi

  # Stats
  local lines bytes words
  lines=$(wc -l < "${out}")
  bytes=$(wc -c < "${out}")
  words=$(wc -w < "${out}")
  printf '✅ %-10s → %s  (%s lines, %s words, %s bytes)\n' \
    "${domain}" "${out}" "${lines}" "${words}" "${bytes}"
}

# Main
if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ $# -eq 0 ]]; then
  set -- "${KNOWN_DOMAINS[@]}"
fi

for d in "$@"; do
  found=0
  for known in "${KNOWN_DOMAINS[@]}"; do
    [[ "${d}" == "${known}" ]] && found=1
  done
  if [[ ${found} -eq 0 ]]; then
    printf '⚠️  Unknown domain: %s (skipping)\n' "${d}" >&2
    continue
  fi
  bundle_domain "${d}"
done

printf '\nDone. Upload exports/notebooklm/*.md to NotebookLM notebooks.\n'
