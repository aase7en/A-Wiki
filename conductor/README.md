# A-Wiki Conductor (v0.1.0)

Orchestration head ที่นั่งบนสมอง A-Wiki — บอกว่า *ใครทำอะไรอยู่ / เริ่มงานใหม่ได้เลยไหม / แตกงานอย่างไร* โดยไม่เพิ่ม background service ใดๆ (อ่านอย่างเดียว + deterministic)

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
```

## กลไก

| โมดูล | หน้าที่ |
|---|---|
| `config.py` | Layered config: defaults → `.awiki-conductor.yaml` → env `AWIKI_CONDUCTOR_*` · fail-closed (schema ผิด/modes ขัดกัน = `ConfigError`) |
| `state.py` | Status รวมแบบ read-only — parse COLLAB claims (anchored ที่หัวตาราง Chunk/WO), branches, นับ hard gates จาก hook registry |
| `gate.py` | Continuity gate เป็น verdict: `collab_read` + `no_conflict` (topic ชน claim/branch → NO-GO พร้อมรายชื่อ) + แนะแถว claim |
| `plan.py` | `objective → work orders` ด้วยกฎแตกคงที่ (หลัง `:` แยกด้วย `,`/`and`) · เลือก lane จาก path · verify ผูกกับ gates จริงของ repo · `--write` ออกไฟล์ WO มาตรฐาม |
| `cli.py` | `status` / `gate` / `plan` — exit code พาเส้นทาง CI (`gate` NO-GO = exit 1) |

## ขอบเขต v0.1.0 (ตั้งใจ)

- ✅ อ่าน state รวม + gate + plan deterministic + CLI
- ⛔ ยังไม่มี: การกระจายงานจริงให้ agents, scheduler, daemon, model routing (เป็นเป้าของรอบถัดไปตาม roadmap)

## การพัฒนา

```bash
python -m pytest tests/test_conductor.py -q   # 18 contract tests (TDD)
```
