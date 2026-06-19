#!/bin/bash
# A-Wiki Benchmark Scan — run via cron daily
# Usage: 0 6 * * * bash /path/to/cron-benchmark-scan.sh
set -euo pipefail
cd "$(dirname "$0")/.." || exit 1
TS=$(date +%Y-%m-%d)
OUTDIR=".tmp"
mkdir -p "$OUTDIR"

echo "=== A-Wiki Benchmark Scan — $TS ==="

# 1. Refresh model capability scores
echo "[1/3] Refreshing model capabilities..."
/usr/bin/python3 scripts/model-capability-scout.py --refresh-all 2>&1 || echo "WARN: scout failed"

# 2. Refresh OpenRouter free roster + cost routing
echo "[2/3] Refreshing cost routing..."
/usr/bin/python3 scripts/batch/scout.py --refresh 2>&1 || echo "WARN: batch scout failed"
/usr/bin/python3 scripts/batch/scout.py --propose 2>&1 || echo "WARN: propose failed"

# 3. Generate summary
echo "[3/3] Generating summary..."
SUMMARY="$OUTDIR/benchmark-$TS.json"
/usr/bin/python3 -c "
import json, os
from datetime import datetime
summary = {'date': '$TS', 'generated_at': datetime.now().isoformat()}
for f in ['model-capability-cache.json', 'model-roster.conf']:
    path = os.path.join('.tmp', f)
    if os.path.exists(path):
        summary[f.replace('.json','').replace('.conf','') + '_exists'] = True
with open('$SUMMARY', 'w') as fh:
    json.dump(summary, fh, indent=2, ensure_ascii=False)
print(f'Benchmark summary → $SUMMARY')
"
echo "=== Done: $TS ==="
