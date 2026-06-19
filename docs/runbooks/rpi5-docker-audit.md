# Raspberry Pi 5 Docker Audit — Legacy Projects

**วันที่**: 2026-06-20 | **สถานะ**: 🔍 Audit

## Docker Compatibility on ARM64

| Image | ARM64 Support | Notes |
|-------|:--:|-------|
| `python:3.11-slim` | ✅ | Official multiarch |
| `node:20-alpine` | ✅ | Official multiarch |
| `nginx:alpine` | ✅ | Official multiarch |
| `postgres:16` | ✅ | Official multiarch |
| `redis:7-alpine` | ✅ | Official multiarch |
| `supabase/postgres` | ❌ | x86 only — use `postgres:16` + manual extension install |
| `supabase/realtime` | ❌ | x86 only — use custom build |
| `supabase/studio` | ❌ | x86 only — web UI, run on separate x86 machine |
| `ghcr.io/nousresearch/hermes-agent` | ✅ | Multiarch build available |

## Multiarch Image Check

```bash
# Check if image has ARM64 manifest
docker manifest inspect python:3.11-slim | grep architecture

# Or try to pull explicitly
docker pull --platform linux/arm64 python:3.11-slim
```

## Legacy Projects Migration

### Dockerfiles ที่ต้องแก้
1. แก้ `FROM python:3.11` → `FROM --platform=linux/arm64 python:3.11-slim`
2. ถ้าใช้ `supabase/postgres` → เปลี่ยนเป็น `postgres:16` + install `pg_graphql`, `pg_net` เอง
3. `supabase/realtime` → ใช้ WebSocket library ตรงๆ โดยไม่ต้องผ่าน Supabase realtime

## Performance Benchmarks

| Workload | RPi 5 8GB | RPi 5 16GB | Mac M1 (เทียบ) |
|----------|-----------|------------|----------------|
| Python API (FastAPI) | ~200 req/s | ~200 req/s | ~2000 req/s |
| PostgreSQL queries | ~500 qps | ~800 qps | ~5000 qps |
| Docker build | ช้า (5-10x x86) | ช้า (5-10x x86) | ปกติ |
| Concurrent containers | 5-8 | 10-15 | 20+ |

## Recommendations

1. ✅ Python/Node.js services — รันบน Pi 5 ได้ดี
2. ⚠️ Supabase — ใช้เฉพาะ PostgreSQL; Studio/Realtime ต้องแยกเครื่อง
3. ❌ Heavy build — build บน x86 → push to registry → pull on ARM64
