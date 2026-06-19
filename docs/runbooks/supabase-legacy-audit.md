# Supabase Legacy Projects Audit

**วันที่**: 2026-06-20 | **สถานะ**: 🔍 Audit

## Projects Using Supabase

| Project | Status | DB Size | Migration Path |
|---------|--------|---------|---------------|
| Pharmacy App v2 | Active | ~2MB | → PostgreSQL on Pi 5 |
| Env Health Webapp | Active | ~1MB | → PostgreSQL on Pi 5 |
| IoT Dashboard (old) | Archived | ~500KB | No migration needed |
| Vaccine Monitor | Prototype | ~100KB | → SQLite (lightweight) |

## Connection Secrets

```
drive/.secrets/
├── supabase-url.txt       → https://xxxxx.supabase.co
├── supabase-anon-key.txt  → eyJhbG...
├── supabase-service-key.txt → eyJhbG... (DO NOT SHARE)
└── postgres-direct-url.txt → postgresql://...
```

## Migration Notes for RPi 5

### จาก Supabase → PostgreSQL ตรง
```bash
# 1. Dump from Supabase
pg_dump "$(cat drive/.secrets/postgres-direct-url.txt)" > supabase-dump.sql

# 2. Restore to Pi 5 PostgreSQL
psql -h localhost -U postgres -d awiki < supabase-dump.sql
```

### Features ที่ต้องหาทางแทน
| Supabase Feature | Replacement on Pi 5 |
|-----------------|---------------------|
| Auth (Supabase Auth) | Simple bcrypt + session cookie |
| Realtime (WebSocket) | SSE (มีอยู่แล้วใน Live Dashboard) |
| Storage (S3-compatible) | Local filesystem + Nginx serve |
| Edge Functions | Python scripts (cron หรือ webhook) |
| Studio (Admin UI) | Custom dashboard หรือ pgAdmin |
