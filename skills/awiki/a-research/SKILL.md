---
name: a-research
description: "งานค้นคว้า/วิเคราะห์/ตรวจสอบข้อมูล — ผูก 7-phase spine เข้ากับ deep-research, web-research, iterative-retrieval, ask-notebooklm, literature-review, market-research. รวม 3 หมวด (วิจัย+วิเคราะห์+ตรวจสอบ) ไว้ที่เดียว. Trigger: 'วิจัย', 'ค้นคว้า', 'research', 'สืบค้น'."
version: 1.0.0
author: A-Wiki
domain: [engineering, data]
lifecycle_phase: meta
category: pipeline
agents: [all]
status: canonical
invocation: manual
invocation_hint: "/A-Research"
a_phase: any
---

# A-Research — วิจัย · วิเคราะห์ · ตรวจสอบแหล่งข้อมูล

> **Dispatcher ล้วน** — ไม่มีเทคนิคเป็นของตัวเอง หน้าที่เดียวคือผูก 7-phase spine
> เข้ากับ canonical skill ที่มีอยู่แล้ว ถ้าต้อง *อธิบายวิธีทำ* แปลว่ามันควรเป็น
> canonical skill ไม่ใช่ pack

## เมื่อไหร่ใช้

✅ ใช้:
- หาข้อมูลเรื่องที่ยังไม่รู้ ต้องสังเคราะห์หลายแหล่ง
- literature review / market research
- ตรวจสอบว่าข้ออ้างหนึ่งจริงไหม มีแหล่งอ้างอิงไหม

❌ ข้าม:
- ค้นใน wiki ตัวเอง → `/search` (ฟรี เร็วกว่า)
- คำถามข้อเท็จจริงสั้น ๆ → ตอบเลย
- รีวิวโค้ด → `/A-Council`

## Iron Law

> **`focus_set` ก่อนเริ่มเสมอ** — pack ครอบทั้ง chain ถ้าไม่ประกาศ phase
> จะไหลจาก ASK ไป IMPLEMENT โดยไม่มีอะไรจับได้

```
focus_set({"skill": "a-research", "goal": "<done criteria>", "phase": "ask"})
```

## Phase → skill

| Phase | ใช้ | ทำอะไร |
|-------|-----|--------|
| ASK | `a-think` | ตั้งคำถามวิจัยให้คมก่อน — คำถามกว้าง = คำตอบไร้ค่า |
| DESIGN | `research-pipeline` | วางว่าจะหาจากไหน เกณฑ์คัดแหล่งคืออะไร |
| PLAN | `a-plan` | แตกเป็น sub-question ที่ตอบได้ทีละข้อ |
| IMPLEMENT | `search-first` · `wiki-search-local` · `web-research` · `deep-research` · `iterative-retrieval` | ค้นจริง — local ก่อน แล้วค่อยออกเน็ต (cost-first) |
| REVIEW | `a-council` · `scholar-evaluation` | ประเมินคุณภาพแหล่ง + ตรวจ bias |
| DEBUG | `a-debug` | ผลขัดแย้งกัน → หาว่าทำไม |
| TEST | `literature-review` · `ask-notebooklm` · `market-research` | สังเคราะห์ + cross-check |

> เดิน phase ด้วย `focus_advance` · จบงาน `focus_clear`
> phase ไหนไม่มี skill เฉพาะ → ใช้ตัว generic ของ spine (`a-plan`, `a-council`, `a-debug`)

## Rationalization table

| ข้ออ้าง | คำตอบโต้ |
|---|---|
| "ข้าม ASK/DESIGN ไปโค้ดเลย" | pack ไม่ได้ทำให้ข้ามได้ — งานเว็บ/วิจัย/คอนเทนต์พังตรง requirement บ่อยกว่าตรงโค้ด |
| "เรียก canonical skill ตรงก็ได้" | ได้ — แต่ยังต้อง `focus_set` ไม่งั้นไม่มีใครรู้ว่าอยู่ phase ไหน |
| "pack นี้ควรมีเทคนิคของตัวเอง" | ไม่ — ถ้าต้องอธิบายวิธีทำ ให้ไปสร้าง canonical skill แล้ว bind มาแทน |

## Invocation

```
/A-Research "<งาน>"
```
