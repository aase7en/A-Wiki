# Agent Continuity Gate — กฎเข้า-ออก-ส่งต่อ สำหรับทุก agent ใน repo นี้

> **สถานะ: BINDING** ตั้งแต่ 2026-08-20 — อนุมัติโดยเจ้าของ repo (human)
> แก้ปัญหาจริง: auto-commit `c343542c` จาก MacBook ทำ main-CI แดงโดยไม่มีใครรู้ตัว ·
> branch `phase6-hook-engine-consolidation` ซ้ำกับงาน Phase 6 ที่กำลังรอ review ·
> agent หลายตัวสลับกันทำตาม 5-hr limit แต่ไม่อ่านงานกัน → ชน/ซ้ำ/งง

**สาระสำคัญ:** กลไกทั้งหมด (claims, work orders, handoff) มีอยู่แล้ว —
ปัญหาคือไม่มีตัวบังคับ ไฟล์นี้คือประตูที่ทุก session ต้องผ่าน **ก่อนแตะอะไรใน repo**

---

## 1. ENTRY GATE — 5 ขั้น ก่อน mutation ใดๆ (ทุก agent ทุก session)

```
1. อ่าน COLLAB.md            → รู้ lanes + ตาราง claim ว่าใครทำอะไรอยู่
2. อ่านงานที่เกี่ยวข้อง        → docs/work-orders/<id>.md / docs/migration/*-work-order.md
                                + handoff ล่าสุดของงานนั้น
3. เช็คชนกัน                  → git branch -a + ตาราง claim: ชื่องานใกล้เคียง = ห้ามเริ่มใหม่
                                ให้ claim ต่อจากของเดิม (scope ผูกกับ chunk ไม่ผูกกับ agent)
4. Claim via conductor       -> run `python -m conductor claim ...` as the primary durable COLLAB writer
                            -> if it succeeds, do not add a manual duplicate row; commit+push the claim before real code mutation
5. ถ้างานเป็น migration phase → ทำตาม work order ของ phase นั้นเท่านั้น (ห้ามข้าม phase)
```

Agent ที่เข้ามาแล้ว "ทำต่อ" โดยไม่ผ่าน 5 ขั้นนี้ = ต้นเหตุของงานชน/ซ้ำทั้งหมดที่เจอมา

## 2. FILE-PURPOSE MAP — ห้ามสร้างไฟล์ซ้ำ role (หนึ่ง role = หนึ่งไฟล์)

| Role | ไฟล์เดียวที่ใช้ | ห้ามสร้างเพิ่มที่ทับ role นี้ |
|---|---|---|
| Roadmap/แผนหลัก | `docs/migration/awiki-vnext-plan.md` (migration) | PROJECT-PLAN อื่น, plan ซ้ำ |
| งานที่กำลังทำ | work order ของ chunk นั้น (`docs/work-orders/<id>.md` / `docs/migration/phase-N-*-work-order.md`) | CURRENT-WORK/TODO ไฟล์ใหม่ |
| ส่งต่อ/หยุดกลางทาง | `docs/migration/phase-N-execution-handoff.md` (หรือ Checkpoint log ใน WO) | HANDOFF ไฟล์ใหม่ที่แยกจากงาน |
| ตาราง claim/เลน | `COLLAB.md` | ตาราง claim ในไฟล์อื่น |
| การตัดสินใจถาวร | `decisions/` (ADR) + migration log | decision log ของชั่วคราว |

จะสร้างไฟล์ plan/todo/status/handoff ใหม่ → **อ่านตารางก่อน แล้ว update ของเดิม**
(กฎเดียวกับ continuity protocol ข้อ 2 — เขียนซ้ำที่นี่เพราะนี่คือจุดที่ agent พลาดบ่อยสุด)

## 3. AUTO-COMMIT HYGIENE — session-end hook กับ main

เหตุการณ์จริง: Stop hook ของ agent บน Mac auto-commit generated noise
(`.wiki-graph.json`, `brain-map.canvas`, wiki overviews) push ตรงเข้า main →
security scan บน main แดง → PR อื่นที่ merge main แดงตามไปด้วย

**กฎ:**
1. auto-commit สิ้นสมัย session ได้ commit ไฟล์ state ของตัวเองเท่านั้น
   (session-memory, ledger ที่ gitignore อยู่แล้ว) — **generated noise
   (.wiki-graph.json / brain-map.canvas / wiki/context/overview-*) ห้าม push
   เข้า main โดยตรง** ให้รวมเป็นส่วนหนึ่งของ branch งานที่ผ่าน CI
2. ก่อน push ใดๆ เข้า main: ต้องรัน `python scripts/security/scan_repo.py --ci
   --baseline scripts/security/baseline.txt` ผ่านก่อน — ไม่ผ่าน = ห้าม push
   (แม้จะเป็น "แค่ generated files")
3. main เป็น human/merge-gate เสมอ — agent ไม่ push ตรงเข้า main เอง
   ยกเว้น hook ที่ได้รับอนุญาตเฉพาะที่ผ่านกฎข้อ 2

## 4. DUPLICATE-WORK GUARD — ก่อนสร้าง branch / เริ่มงาน

1. `git branch -a | grep -i <หัวข้องาน>` + อ่านตาราง claim ใน `COLLAB.md`
2. มี branch/claim ใกล้เคียงอยู่แล้ว → อย่าสร้างใหม่ ให้ทำต่อจาก branch/claim นั้น
   (หรือถาม human ว่าปลดเก่าได้ไหม)
3. ชื่อ branch ต้องสื่องานเดียวกับ claim ใน COLLAB.md

## 5. CHECKPOINT / HANDOFF — ทุกครั้งที่หยุด

ทำตาม `cross-agent-work-orders.md` §Pause-Resume เป๊ะๆ:
commit งานค้าง (build พัง → `wip/<id>`) → append Checkpoint ใน WO →
อัปเดต claim → push — **ห้ามหยุดโดยมี state อยู่แค่ใน chat**

## 6. สิ่งที่ยังเป็น follow-up (สร้างเป็น work order ถัดไป ไม่ใช่ข้ออ้าง)

- [ ] Hook บังคับ entry gate: SessionStart stamp `.tmp/agent-sessions/<id>.json`
      + PreToolUse เช็ค stamp ก่อนให้แก้ shared surface (upgrade จาก warning → block เมื่อทดสอบแล้วว่าไม่ deadlock)
- [ ] stop-auto-commit ผ่าน scan-gate ตามกฎข้อ 3 ก่อน push main
- [ ] แจ้งเตือนใน COLLAB เมื่อมี branch ใหม่บน origin ที่ไม่มีแถว claim รองรับ

## 7. Cross-machine no-human-relay amendment (2026-08-30)

Before creating work, search in this order: `python -m conductor status --json` -> active WO/checkpoint -> `git branch -a` -> open PRs -> existing implementation. A similar goal/WO/branch means `RESUME/RECONCILE`, not CREATE.

Use `python -m conductor claim ...` as the primary claim-row writer. If it succeeds, do not manually add another COLLAB row. Commit and push the claim before real mutation.

Agents must fetch/read checkpoint state from the repository themselves. When a platform cannot invoke another agent directly, the human relays only a WO-ID/pointer prompt. HEAD, tests, evidence, blockers, and next action belong in the WO/branch/PR; never require the human to copy an agent result back into another chat.
