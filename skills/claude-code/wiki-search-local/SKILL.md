# Skill: Wiki Search Local (FTS5)

**Trigger**: ก่อนใช้ Grep/Read สแกน wiki หลายไฟล์, หรือเมื่อ user ถามว่า "มีหน้าไหนพูดถึง X", "ค้นใน wiki", "หาเรื่อง..."

**ตำแหน่ง Cost Pyramid**: Level **-1** (ฟรียิ่งกว่า free API — local, no network)

---

## เมื่อไหร่ใช้

| สถานการณ์ | ใช้ skill นี้? |
|----------|---------------|
| ต้อง scan >3 ไฟล์ใน wiki/ หา keyword | ✅ ใช้ก่อน |
| ถามแบบ "มีหน้าไหนพูดถึง X บ้าง" | ✅ ใช้ |
| Cross-domain synthesis (ขอภาพรวม) | ❌ ใช้ NotebookLM (`/snapshot-nb` + `ask-notebooklm.py`) |
| รู้ path ไฟล์ที่ต้องการแล้ว | ❌ Read ตรง |
| Edit หลายไฟล์พร้อมกัน | ❌ Glob + Edit |
| ค้น code (นอก wiki/) | ❌ Grep ปกติ |

---

## Workflow

```bash
# 1. Ensure index is fresh (auto-built if missing)
python3 scripts/search-wiki.py "QUERY"

# 2. Field-scoped search
python3 scripts/search-wiki.py "supabase" --field title
python3 scripts/search-wiki.py "JWT ES256" --field body

# 3. Rebuild index ก่อน search (หลังแก้ wiki หลายไฟล์)
python3 scripts/search-wiki.py --rebuild "QUERY"

# 4. JSON output (เมื่อต้อง parse ใน script ต่อ)
python3 scripts/search-wiki.py "MQTT" --json
```

## Query Syntax (FTS5)

| Pattern | ความหมาย |
|---------|---------|
| `mqtt esp32` | match ทั้งสองคำ (AND) |
| `"home assistant"` | exact phrase |
| `mqtt OR coap` | either |
| `title:supabase` | search field-specific |
| `mqtt NOT mosquitto` | exclude |
| `iot*` | prefix match |

## Output Format

```
1<TAB>wiki/entities/iot/mqtt-protocol.md<TAB>MQTT Protocol<TAB>…snippet «MQTT»…
2<TAB>wiki/entities/iot/home-assistant.md<TAB>Home Assistant<TAB>…
```

อ่าน path → ถ้า hit ตรงประเด็น → Read แค่ไฟล์ที่จำเป็น (ปกติ 1-3 ไฟล์) แทน Glob + Read 10+ ไฟล์

---

## ความสัมพันธ์

- `delegate-subagent` skill — เป็น Tier 0 ก่อน Explore subagent (ลด token มากกว่า)
- `token-optimization` skill — ใช้ร่วม strategic-compact
- `scripts/build-wiki-index.py` — สร้าง index (รัน auto หลัง gen-index.py ในอนาคต)
- `scripts/search-wiki.py` — query CLI

## ระวัง

- Index อาจ stale หลัง edit wiki หลายไฟล์ → ใช้ `--rebuild` หรือรอ post-wiki-edit hook chain (Phase 3)
- ถ้า FTS5 query syntax error → fallback ใช้ Grep ปกติ
- สำหรับคำถาม synthesize (ไม่ใช่ keyword lookup) → ใช้ `ask-notebooklm` skill แทน
