---
name: obsidian
description: Enhance wiki content with Obsidian skills (wikilinks, bases, canvas, defuddle, CLI). Use when creating or editing markdown files in wiki/, working with pharmacy drug data, or building cross-domain visualizations. Activated on .md, .base, .canvas files.
---

# Obsidian Skills — Claude Integration

โปรเจคนี้มี Obsidian skills ติดตั้งใน `.obsidian/skills/` ทั้ง 5 ตัวจาก [kepano/obsidian-skills](https://github.com/kepano/obsidian-skills)

## 📋 Prerequisites

```bash
# Obsidian CLI สำหรับ automation — ติดตั้งแล้ว
obsidian --version
# ถ้าไม่เจอ: npm install -g obsidian-cli
```

## 🎯 เมื่อไหร่ควรใช้ Obsidian Skills

| สถานการณ์ | Skill ที่ใช้ | ทำไม |
|-----------|-------------|------|
| สร้างหน้า entity/concept ใหม่ | `obsidian-cli` + `obsidian-markdown` | สร้างจาก template ได้เร็ว, wikilinks ถูกต้อง |
| เขียน cross-reference ระหว่างหน้า | `obsidian-markdown` | wikilinks `[[page]]` → Obsidian จัดการ rename อัตโนมัติ |
| ค้นหาหน้าที่เกี่ยวข้องใน vault | `obsidian-cli` | `obsidian vault search` เร็วกว่า grep สำหรับ wikilinks |
| ทำ catalog ยา (pharmacy) | `obsidian-bases` | Table view + filters + aggregation จาก JSON |
| สร้าง network graph | `json-canvas` | Visualize cross-domain relationships (IoT×Env, AI×Pharmacy) |
| Extract web content เป็น markdown | `defuddle` | `npx defuddle <URL>` → clean markdown → ingest ลง wiki |
| Bulk update properties | `obsidian-cli` | `obsidian properties` — update last_verified, tags, sources |

## 🛠️ Workflow: สร้างหน้า Wiki ใหม่

### วิธีที่ 1: ใช้ Obsidian CLI (เร็ว — bulk)
```bash
# สร้าง entity จาก template
obsidian create wiki/entities/iot/new-device \
  --template .obsidian/templates/entity-template

# สร้าง concept จาก template
obsidian create wiki/concepts/pharmacy/new-concept \
  --template .obsidian/templates/concept-template
```

### วิธีที่ 2: ใช้ Claude เขียนตรง (แม่นยำกว่า — schema ถูกต้อง)
Claude เขียนหน้าวิธี Schema ใน CLAUDE.md โดยตรง — เหมาะกับ:
- หน้าต้องการ reasoning ซับซ้อน (synthesis)
- หน้าต้องตรวจ contradiction กับข้อมูลที่มี
- หน้าต้อง cross-reference หลายทาง

### วิธีที่ 3: Hybrid (แนะนำ)
1. Claude สร้าง content + frontmatter ตาม schema
2. ใช้ `obsidian-cli` เพื่อ bulk verify / update properties
3. เปิดใน Obsidian UI เพื่อตรวจ graph view

## 🧪 Workflow: Pharmacy Drug Catalog (Obsidian Bases)

```bash
# 1. สร้าง bases view จาก raw JSON
# ไฟล์: wiki/synthesis/pharmacy-drug-catalog.md
# ~~~
# type: bases
# source: raw/pharmacy/sp_drugs_full_3760.json
# columns:
#   - name (text)
#   - category (select)
#   - price (number)
#   - unit (text)
# filters:
#   - field: "category"
#     value: "Antibiotic"
# ~~~
```

## 🧪 Workflow: Cross-Domain Visualization (Canvas)

```bash
# 1. สร้าง canvas file
touch wiki/synthesis/iot-env-network.canvas

# 2. เปิดใน Obsidian → Create canvas → Add nodes:
#    - IoT sensors → Environmental measurements
#    - AI tools → Data processing pipeline
#    - Pharmacy → Drug cold chain monitoring
```

## 📚 วิธีใช้ Obsidian Markdown ใน Wiki Content

```markdown
# Wikilinks (สำหรับ cross-reference)
[[mqtt-protocol]]                          # link ไป entity
[[concepts/env/rabies-pep-protocol]]       # link ไป concept
[[sources/lora-getting-started-dronebot]]  # link ไป source

# Callouts (สำหรับ highlight)
> [!NOTE] ข้อมูลเพิ่มเติม
> รายละเอียด...

> [!WARNING] ข้อควรระวัง
> ข้อมูลนี้ยังไม่ verified...

# Embeds (สำหรับ reuse content)
![[wiki-overview#IoT Domain]]              # embed section
```

## ⚠️ ข้อควรระวัง

- **ห้าม commit** `.obsidian/workspace.json`, `.obsidian/plugins/` — device-specific, อยู่ใน .gitignore
- **Obsidian CLI** ต้องการ `obsidian` command → ตรวจสอบก่อนใช้ใน automation script
- **Bases** ใช้ได้บน Obsidian UI เท่านั้น (ไม่อ่านผ่าน Markdown parser ปกติ)
- **Canvas** files (`.canvas`) เป็น JSON — สามารถสร้าง/edit ด้วย Claude ได้ แต่แนะนำให้ดูใน Obsidian UI เพื่อ verify layout
- ถ้าไม่แน่ใจว่าควรใช้ skill ไหน → ถาม Claude: Claude ตัดสินใจเองโดยอ้างอิงจาก SKILL.md นี้

## Reference

- `.obsidian/skills/obsidian-markdown/SKILL.md` — Markdown syntax เต็ม
- `.obsidian/skills/obsidian-cli/SKILL.md` — CLI commands เต็ม
- `.obsidian/skills/obsidian-bases/SKILL.md` — Database views + formulas
- `.obsidian/skills/json-canvas/SKILL.md` — Canvas + network graphs
- `.obsidian/skills/defuddle/SKILL.md` — Web extraction
- `docs/OBSIDIAN_SKILLS.md` — Quick reference guide