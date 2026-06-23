#!/bin/bash
# A-Wiki Daily Cost & Delegation Audit
# Run via cron: 0 7 * * * bash $REPO_ROOT/scripts/cron-audit.sh
cd "$(dirname "$0")/.." || exit 1
/usr/bin/python3 scripts/cron-audit.py
