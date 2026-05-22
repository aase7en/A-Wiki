# Obsidian Skills — Quick Reference Guide

ติดตั้งแล้ว: ทั้ง 5 skills จาก https://github.com/kepano/obsidian-skills

---

## 🛠️ Priority 1 — Essential Skills

### obsidian-markdown
**สำหรับ**: Wiki content creation — wikilinks, embeds, properties

**วิธีใช้**:
- **Wikilinks**: `[[mqtt-protocol]]` สำหรับ cross-references
- **Block embeds**: `![[page#section]]` เพื่อ reuse content
- **Callouts**: `> [!NOTE]`, `> [!TIP]`, `> [!WARNING]` สำหรับ highlight
- **Properties**: Frontmatter `type: entity`, `tags: []` ตรงกับ CLAUDE.md schema

**ตัวอย่าง**:
```markdown
---
type: entity
domain: iot
tags: [protocol]
sources: [source-mqtt]
---

# MQTT Protocol

[[mqtt-qos]] — Quality of Service levels
```

**ที่อ่านเพิ่มเติม**: `.obsidian/skills/obsidian-markdown/references/`

---

### obsidian-cli
**สำหรับ**: Bulk operations — create notes, search, update properties via terminal

**วิธีใช้**:
```bash
# Search entities ทั้งหมด
obsidian vault search "entity" --tags entity

# Create new note from template
obsidian create wiki/entities/iot/mqtt-protocol --template .obsidian/templates/entity-template

# Update note property
obsidian properties wiki/entities/iot/mqtt-protocol --set "last_verified:2026-05-09"

# List all sources
obsidian vault search "" --path wiki/sources/
```

**สำหรับ automation** (bash scripts):
```bash
#!/bin/bash
# Auto-create entity pages from CSV
while read domain name; do
  obsidian create "wiki/entities/$domain/$name" --template .obsidian/templates/entity-template
done < entities_todo.csv
```

**ที่อ่านเพิ่มเติม**: `.obsidian/skills/obsidian-cli/SKILL.md`

---

## 📊 Priority 2 — Valuable Skills

### obsidian-bases
**สำหรับ**: Database-like catalog views — ดีสำหรับ pharmacy domain

**วิธีใช้** (บน Obsidian UI):
1. สร้าง data file (JSON/YAML) → `.obsidian/bases/drugs.json`
2. Create database view ด้วย bases UI → filter, sort, aggregate
3. Use formulas: `field1 + field2`, `count()`, `filter()`

**ตัวอย่าง schema**:
```json
{
  "drugs": [
    { "name": "Amoxicillin", "category": "Antibiotic", "price": 25.50, "qty": 100 },
    { "name": "Paracetamol", "category": "Analgesic", "price": 5.00, "qty": 500 }
  ]
}
```

**สำหรับ pharmacy**:
- Link `raw/pharmacy/sp_drugs_full_3760.json` ไปยัง bases
- Create table view พร้อม filters: `category = "Antibiotic"`, `price < 50`
- Aggregate: `SUM(qty)`, `AVG(price)` ต่อ category

**ที่อ่านเพิ่มเติม**: `.obsidian/skills/obsidian-bases/references/FUNCTIONS_REFERENCE.md`

---

### json-canvas
**สำหรับ**: Visual knowledge mapping — network graphs, mind maps

**วิธีใช้** (บน Obsidian UI):
1. Create new Canvas file: `wiki/synthesis/drug-interactions-map.canvas`
2. Add nodes → link them → show relationships visually
3. Use groups → organize by drug class, interaction type

**สำหรับ cross-domain synthesis**:
- IoT × Env: Visualize sensor → measurement → environmental impact
- AI × Pharmacy: Map drug recommendation agent → drug database → interactions

**ที่อ่านเพิ่มเติม**: `.obsidian/skills/json-canvas/references/EXAMPLES.md`

---

## 🛠️ Obsidian Templates (โปรเจคเฉพาะ)

### entity-template.md
```
ที่อยู่: .obsidian/templates/entity-template.md
เมื่อใช้: สร้าง entity ใหม่ via obsidian-cli
```

**ใช้งาน**:
```bash
obsidian create wiki/entities/iot/new-device --template .obsidian/templates/entity-template
```

Properties ที่ pre-filled:
- `type: entity`
- `created:`, `updated:`, `last_verified:` → auto-date
- Domain placeholder → เลือกใหม่
- Section placeholders → แก้เนื้อหา

---

### concept-template.md
```
ที่อยู่: .obsidian/templates/concept-template.md
เมื่อใช้: สร้าง concept ใหม่ via obsidian-cli
```

Properties pre-filled:
- `type: concept`
- Sections: นิยาม, ข้อดี/เสีย, ตัวอย่าง
- Confidence marker → `[training]` default

---

## 📋 Workflow Examples

### Example 1: Create MQTT Entity (ง่าย)
```bash
# 1. Create from template
obsidian create wiki/entities/iot/mqtt-protocol --template .obsidian/templates/entity-template

# 2. Edit ด้วย Obsidian UI → fill content, wikilinks
#    - Add [[mqtt-qos]] for QoS concept
#    - Add [[sources/mqtt-whitepaper]] for source

# 3. Update properties
obsidian properties wiki/entities/iot/mqtt-protocol \
  --set "domain:iot" \
  --set "last_verified:2026-05-09"

# 4. Verify wikilinks in Obsidian graph view
```

### Example 2: Create Drug Interaction Database (ขั้นสูง)
```bash
# 1. Link raw pharmacy data
# raw/pharmacy/sp_drugs_full_3760.json → bases view

# 2. Create database view in Obsidian
# File: wiki/synthesis/drug-database.md
# ~~~json-bases
# source: raw/pharmacy/sp_drugs_full_3760.json
# columns:
#   - name (text)
#   - category (select)
#   - price (number)
#   - qty (number)
# filters: [{ field: "category", value: "Antibiotic" }]
# ~~~

# 3. Query from CLI
obsidian vault search "Antibiotic" --path wiki/synthesis/

# 4. Link to entities
# wiki/entities/pharmacy/amoxicillin.md → [[drug-database#Amoxicillin]]
```

---

## ⚠️ Important Notes

✅ **เก็บ**:
- All wikilinks aligned with CLAUDE.md schema
- Templates matched to entity/concept format
- .obsidian/skills/ และ .obsidian/templates/ → commit ลง git

❌ **ห้าม**:
- Edit `.obsidian/plugins/`, `.obsidian/workspace.json` → device-specific
- Commit user settings → อยู่ใน .gitignore แล้ว

---

## 🔧 Troubleshooting

**Obsidian CLI not found**:
```bash
npm list -g obsidian-cli
# ถ้าไม่มี: npm install -g obsidian-cli
```

**Skills folder missing**:
```bash
ls .obsidian/skills/
# ต้องมี: defuddle, json-canvas, obsidian-bases, obsidian-cli, obsidian-markdown
```

**Templates not showing in Obsidian**:
1. Restart Obsidian
2. Settings → Files & Links → Templates location → `.obsidian/templates/`
3. Use templates via command: Ctrl+P → "Insert template"

---

**For more details**, see:
- CLAUDE.md — Wiki schema & rules
- .clinerules — Cline-specific rules
- `.claude/skills/obsidian/SKILL.md` — Claude Code integration (เมื่อไหร่ควรใช้ Obsidian skills อัตโนมัติ)
- `.obsidian/skills/*/SKILL.md` — Official skill documentation
- `https://github.com/kepano/obsidian-skills` — Official repo
