#!/usr/bin/env bash
# Run every deterministic A-Wiki skill eval suite.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

for suite in evals/awiki/*.json; do
  python3 scripts/skillopt/awiki_eval.py --suite "$suite"
done
