# Protocol: Markdown vs HTML for Agent Output

> เจตนา: ให้ทุก agent (Claude/Codex/Gemini/Cursor) เลือก format ของ "ผลงานที่ส่งให้คนอ่าน" อย่างสม่ำเสมอ
> เพื่อดึง human-in-the-loop กลับมา review จริง โดยไม่ทำลาย source-of-truth ที่ต้องอยู่ใน git ระยะยาว.

## หลักการ (durability stratification)

แหล่งอ้างอิง: Thariq Shihipar (ทีม Claude Code, Anthropic) — "HTML is the new Markdown" (พ.ค. 2026).
แก่น: เมื่อ output ของ agent เป็น Markdown ยาวๆ มนุษย์จะ "กวาดตา ไม่อ่าน" แล้วหลุดจาก loop.
HTML ที่มีโครงสร้าง/สี/ปุ่ม ทำให้ review ได้จริง — แต่ HTML diff ยากใน git จึงไม่เหมาะกับไฟล์ที่อยู่นาน.

| อยู่นานแค่ไหน | ตัวอย่าง | Format |
|---|---|---|
| เดือน–ปี, อยู่ใน git, ต้อง diff/review | `CLAUDE.md`, `AGENTS.md`, `wiki/` pages, ADRs, README, journal | **Markdown** |
| ชั่วโมง–วัน, ใช้สื่อสาร/ตัดสินใจครั้งเดียว | dashboard, post-mortem report, code-review, model comparison, health digest | **HTML** (ผ่าน `render-html` skill) |

## กฎ

1. **Source-of-truth = Markdown เสมอ.** HTML เป็น layer ทับ data เดิม ไม่ใช่แทนที่. ห้ามเขียน HTML ลง
   `wiki/`, `raw/`, หรือ `CLAUDE.md`.
2. **เลือก HTML เมื่อ output มีอย่างน้อยหนึ่งอย่าง:** ตารางที่อยากให้ sort/filter, diff ที่ควรไฮไลต์สี,
   ความรุนแรงหลายระดับ (severity), กราฟ/ความสัมพันธ์, หรือผู้ใช้ต้องเลือก/ปรับค่าแล้วส่งกลับ.
3. **เลือก Markdown เมื่อ** เป็นเอกสารสั้น/คำสั่ง/บันทึก ที่เน้นอ่านเป็นข้อความและต้อง review ใน commit.
4. **HTML ต้อง self-contained + gitignored** — ออกที่ `exports/html/` (ephemeral), zero external dependency.
5. **ใส่ทางกลับเสมอ** — artifact ทุกชิ้นมีปุ่ม Copy-as-JSON เพื่อ round-trip ค่าที่ผู้ใช้เลือกกลับเข้า agent.

## วิธีทำ

ใช้ skill: `skills/render-html/` (ดู `SKILL.md`). เพิ่ม surface ใหม่ = template + 1 entry ใน `registry.json`.

```bash
python3 skills/render-html/scripts/render.py <surface> --in data.json
```

## Verify

```bash
python3 -m pytest skills/render-html/tests/test_render_html.py -v
```
