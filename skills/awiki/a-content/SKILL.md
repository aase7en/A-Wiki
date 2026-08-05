---
name: a-content
description: "งานคอนเทนต์และการตลาด — ผูก 7-phase spine เข้ากับ article-writing, brand-voice, seo, content-engine, marketing-campaign, social-publisher, thai-social-caption. Trigger: 'คอนเทนต์', 'บทความ', 'การตลาด', 'content', 'marketing', 'seo'."
version: 1.0.0
author: A-Wiki
domain: [media, business]
lifecycle_phase: meta
category: pipeline
agents: [all]
status: canonical
invocation: manual
invocation_hint: "/A-Content"
a_phase: any
---

# A-Content — คอนเทนต์ · การตลาด

> **Dispatcher ล้วน** — ไม่มีเทคนิคเป็นของตัวเอง หน้าที่เดียวคือผูก 7-phase spine
> เข้ากับ canonical skill ที่มีอยู่แล้ว ถ้าต้อง *อธิบายวิธีทำ* แปลว่ามันควรเป็น
> canonical skill ไม่ใช่ pack

## เมื่อไหร่ใช้

✅ ใช้:
- เขียนบทความ / blog / newsletter
- วางแผน campaign การตลาด
- โพสต์โซเชียล (ไทย/อังกฤษ)

❌ ข้าม:
- เอกสารราชการ/โรงพยาบาล → `/A-Doc`
- README / docs ทางเทคนิค → เขียนตรง
- แค่แก้คำผิด → ทำเลย

## Iron Law

> **`focus_set` ก่อนเริ่มเสมอ** — pack ครอบทั้ง chain ถ้าไม่ประกาศ phase
> จะไหลจาก ASK ไป IMPLEMENT โดยไม่มีอะไรจับได้

```
focus_set({"skill": "a-content", "goal": "<done criteria>", "phase": "ask"})
```

## Phase → skill

| Phase | ใช้ | ทำอะไร |
|-------|-----|--------|
| ASK | `a-think` · `grill-with-docs` | ใครอ่าน? อยากให้เขาทำอะไรต่อ? |
| DESIGN | `brand-voice` · `brand-guidelines` · **`a-design`** (visual content: carousel/infographic/hero/card — ใช้ adapter social-carousel หรือ deck) | น้ำเสียง โทน ข้อห้ามของแบรนด์ + visual composition ของคอนเทนต์ |
| PLAN | `content-engine` · `marketing-campaign` | ปฏิทินคอนเทนต์ / โครง campaign |
| IMPLEMENT | `article-writing` · `thai-social-caption` | เขียนจริง |
| REVIEW | `a-council` · `seo` | รีวิวคุณภาพ + SEO |
| DEBUG | `a-debug` | ยอด engagement ตก → หาสาเหตุ |
| TEST | `social-publisher` · `crosspost` | เผยแพร่ + วัดผล |

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
/A-Content "<งาน>"
```
