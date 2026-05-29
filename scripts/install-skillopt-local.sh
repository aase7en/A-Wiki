#!/usr/bin/env bash
# install-skillopt-local.sh — optional runnable SkillOpt install for this clone.
#
# Keeps upstream source and virtualenv in ignored local paths:
#   .tmp/skillopt-src
#   .venv-skillopt

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

SRC_DIR="${AWIKI_SKILLOPT_SRC:-$REPO_ROOT/.tmp/skillopt-src}"
VENV_DIR="${AWIKI_SKILLOPT_VENV:-$REPO_ROOT/.venv-skillopt}"
URL="https://github.com/microsoft/SkillOpt.git"
BRANCH="${SKILLOPT_BRANCH:-main}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
EXTRAS="${SKILLOPT_EXTRAS:-}"

mkdir -p "$(dirname "$SRC_DIR")"

if [ -d "$SRC_DIR/.git" ]; then
  echo "-> updating SkillOpt source: $SRC_DIR"
  git -C "$SRC_DIR" fetch --depth 1 origin "$BRANCH"
  git -C "$SRC_DIR" checkout -q FETCH_HEAD
else
  echo "-> cloning SkillOpt source: $SRC_DIR"
  git clone --depth 1 --branch "$BRANCH" "$URL" "$SRC_DIR"
fi

if [ ! -x "$VENV_DIR/bin/python" ]; then
  echo "-> creating virtualenv: $VENV_DIR"
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/python" -m pip install --upgrade pip
if [ -n "$EXTRAS" ]; then
  "$VENV_DIR/bin/python" -m pip install -e "$SRC_DIR[$EXTRAS]"
else
  "$VENV_DIR/bin/python" -m pip install -e "$SRC_DIR"
fi

cat <<EOF

SkillOpt local install complete.

Activate:
  source "$VENV_DIR/bin/activate"

Run CLI:
  "$VENV_DIR/bin/python" "$SRC_DIR/scripts/train.py" --help

Notes:
  - Source lives in .tmp/skillopt-src (ignored).
  - Virtualenv lives in .venv-skillopt (ignored).
  - Put large datasets and private outputs in drive/, not git.
EOF
