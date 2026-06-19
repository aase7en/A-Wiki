# Benchmark Cron Schedule

**วันที่**: 2026-06-20

## Cron Jobs

| Job | Schedule | Script | Purpose |
|-----|----------|--------|---------|
| Model Capability Rescan | ทุกวัน 06:00 | `cron-benchmark-scan.sh` | Refresh free model roster + cost routing |
| Cost/Delegation Audit | ทุกวัน 07:00 | `cron-audit.sh` | Analyze daily cost patterns |
| A-Wiki Health Check (Hermes) | ทุกวัน 08:00 | Hermes cron `224a5351605a` | Wiki structure + git + stats |

## Manual Triggers

```bash
# Run benchmark scan now
bash scripts/cron-benchmark-scan.sh

# Check last scan results
cat .tmp/benchmark-$(date +%Y-%m-%d).json

# Run cost audit
/usr/bin/python3 scripts/cron-audit.py
cat .tmp/cost-audit-$(date +%Y-%m-%d).json
```

## Working Directory

ทุก cron job รันจาก A-Wiki repository root (`/Users/aase7en/Desktop/A-Wiki`)
