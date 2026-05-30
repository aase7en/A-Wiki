# A-Wiki Brain Improvement Gate

> เรียบเรียงเจตนา: ก่อน AI agent จะแก้ เพิ่ม ลบ ติดตั้ง หรือรับสิ่งใดเข้ามาใน A-Wiki ต้องพิสูจน์ให้ได้ว่าสิ่งนั้นทำให้ A-Wiki เป็น second brain ที่เก่งขึ้นอย่างชัดเจน โดยยังเบา ปลอดภัย ใช้ข้ามเครื่องได้ และไม่ทำให้ public repo เสี่ยงรั่วข้อมูลส่วนตัว

## Core Rule

ทุก change ที่เกี่ยวกับ "สมอง" ของ A-Wiki ต้องผ่าน gate นี้ก่อนลงมือ:

1. **Capability gain** — ทำให้ A-Wiki เก่งขึ้นหรือประยุกต์ใช้ได้จริงในอนาคตอย่างชัดเจน ไม่ใช่แค่เพิ่มของเท่ๆ
2. **Lightweight by default** — เลือกวิธีน้ำหนักเบาก่อน: hook, protocol, skill, plugin, GitHub Action, symlink, local index, หรือ multi-model delegation ตามความเหมาะสม
3. **Cost-first** — เริ่มที่ Level -1/0: local search, generated index, hook automation, context compaction. ใช้ free/cheap/multi-model parallel เฉพาะเมื่อคุ้ม และ primary model ทำหน้าที่ critic/validator
4. **Cross-platform** — ต้องใช้ได้บน Mac, Work PC, WSL/Linux เท่าที่สมเหตุสมผล ห้าม hardcode path เฉพาะเครื่อง
5. **Cross-device** — ต้องไม่ทำลาย workflow sync ข้ามเครื่อง; ถ้าเกี่ยวกับข้อมูลส่วนตัวให้ผ่าน `drive/` หรือ `A_WIKI_DRIVE_PATH`
6. **Everything AI Agent** — ให้ agent อื่นอ่าน/ใช้ต่อได้ผ่าน `AGENTS.md`, platform rules, skills, scripts, docs, หรือ generated context
7. **Public-safe repo** — secrets, raw files, private notes, analytics, voice profile, customer data, and personal files must live in `drive/` or `raw/` links and stay gitignored
8. **Package when useful** — ถ้าของนั้นจะถูกใช้ซ้ำ ให้มัดเป็น installable/reusable unit เช่น skill folder, script, hook, protocol doc, or setup step
9. **Verify** — มี command ตรวจอย่างน้อยหนึ่งอย่าง เช่น preflight, skill-quality, privacy check, tests, or gen-index check

## Decision Table

| Situation | Preferred shape |
|---|---|
| Repeated reminder | Hook or preflight check |
| Reusable agent workflow | Skill package under `skills/` |
| Cross-agent rule | Protocol doc + pointer in platform instruction files |
| Private/heavy data | `drive/` symlink + `.gitignore` |
| Raw source/provenance | `raw/` first, then `wiki/sources/` |
| Web/latest knowledge | Verified source + date; delegate/search before answering |
| Multi-file scan or comparison | Local index first, then free/cheap parallel delegation |
| Public release risk | `check-privacy.py` + secret scan before commit |

## Stop Conditions

Stop and ask or redesign if any answer is "no":

- Does this clearly improve A-Wiki's brain, automation, safety, retrieval, reasoning, or reusable agent workflow?
- Is there a lighter way to do it?
- Can another agent use it without tribal knowledge?
- Will it work across devices without hardcoded personal paths?
- Is all private/raw/secret data outside tracked git?
- Is there a verification command?

## Standard Response Before Significant Edits

For any significant A-Wiki brain change, state this briefly before editing:

```text
Brain Gate:
- Gain: <what A-Wiki gets better at>
- Shape: <hook/skill/plugin/script/protocol/symlink/action>
- Weight: <why this is lightweight enough>
- Safety: <how private/raw/secrets stay out of git>
- Verify: <commands to run>
```

Keep it short. The goal is engineering discipline, not bureaucracy.
