# A-Wiki Brain Bridge (conductor/, v0.2.0)

**Thin brain-side API** ที่ให้ A-Wiki-Conductor (control plane) และ agent ใดๆ เรียกใช้สมอง A-Wiki — read-mostly + จอง claim แบบ gate-guarded · ดู division of labor: `docs/architecture/brain-vs-conductor-division.md` — บอกว่า *ใครทำอะไรอยู่ / เริ่มงานใหม่ได้เลยไหม / แตกงานอย่างไร* โดยไม่เพิ่ม background service ใดๆ (อ่านอย่างเดียว + deterministic)

> ออกแบบโดยได้แรงบันดาลใจจาก Serena (MIT) — ดู `NOTICE` และ `decisions/adr-conductor-fork-mit.md`

## ใช้จริง

```bash
# ภาพรวมทั้งหมด (COLLAB claims + git branches + จำนวน hard gates)
python -m conductor status --json

# เช็กก่อนเริ่มงานใหม่: GO/NO-GO + แถว claim ที่ควรเพิ่มใน COLLAB
python -m conductor gate --topic "fresh-idea" --agent zcode --json

# แตก objective เป็น work orders (deterministic — ไม่เดา)
python -m conductor plan "spike: config layering, entry gate, CLI" --json
python -m conductor plan "spike: a, b, c" --write   # เขียน WO ไฟล์จริง

# v0.2 — brain bridge สำหรับ control plane
python -m conductor verify --gates registry,scan,health --json  # รัน gates แบบ bounded
python -m conductor recall --query "phase 6" --json             # ค้น L1 memory (redacted)
python -m conductor claim --topic x --agent zcode --branch feat/x  # จอง claim (gate-guarded, idempotent)
```

## กลไก

| โมดูล | หน้าที่ |
|---|---|
| `config.py` | Layered config: defaults → `.awiki-conductor.yaml` → env `AWIKI_CONDUCTOR_*` · fail-closed (schema ผิด/modes ขัดกัน = `ConfigError`) |
| `state.py` | Status รวมแบบ read-only — parse COLLAB claims (anchored ที่หัวตาราง Chunk/WO), branches, นับ hard gates จาก hook registry |
| `gate.py` | Continuity gate เป็น verdict: `collab_read` + `no_conflict` (topic ชน claim/branch → NO-GO พร้อมรายชื่อ) + แนะแถว claim |
| `plan.py` | `objective → work orders` ด้วยกฎแตกคงที่ (หลัง `:` แยกด้วย `,`/`and`) · เลือก lane จาก path · verify ผูกกับ gates จริงของ repo · `--write` ออกไฟล์ WO มาตรฐาม |
| `cli.py` | `status` / `gate` / `plan` — exit code พาเส้นทาง CI (`gate` NO-GO = exit 1) |

## ขอบเขต v0.2 (ตั้งใจ)

- ✅ v0.1: status/gate/plan · v0.2: verify (bounded gates) + recall (L1 redacted) + claim (gate-guarded idempotent)
- ⛔ dispatch/process/UI/model routing = ของ A-Wiki-Conductor (control plane) — bridge ไม่ทำซ้ำ (ตาม division doc)

## การพัฒนา

```bash
python -m pytest tests/test_conductor.py -q   # 29 contract tests (TDD)
```
