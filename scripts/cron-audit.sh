#!/bin/bash
# A-Wiki Daily Cost & Delegation Audit
# Run via cron: 0 7 * * * bash /Users/aase7en/Desktop/A-Wiki/scripts/cron-audit.sh
cd "$(dirname "$0")/.." || exit 1
/usr/bin/python3 scripts/cron-audit.py
