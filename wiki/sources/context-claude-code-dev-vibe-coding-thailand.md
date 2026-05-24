---
type: source
title: "(10) context ใน Claude Code ใกล้เต็ม dev... - Vibe Coding Thailand"
slug: context-claude-code-dev-vibe-coding-thailand
date_ingested: 2026-05-24
original_file: raw/(10) context ใน Claude Code ใกล้เต็ม dev... - Vibe Coding Thailand.md
---

```yaml
---
title: "(10) context ใน Claude Code ใกล้เต็ม dev... - Vibe Coding Thailand"
source: "https://www.facebook.com/vibecodingthailand/posts/pfbid05hh8Mun9cGqZogxvPQBLjaLmpEqQr4kmndpZNbhsERR5QG7dzum6sQL2xQkhNRW7l"
author: ""
published: ""
created: "2026-04-30"
description: ""
tags: ""
---
```

context ใน Claude Code ใกล้เต็ม dev ส่วนใหญ่กด /compact หรือ /clear แบบเดาๆ ว่าตัวไหนเหมาะ

จริงๆ Anthropic เขียน docs อธิบายไว้หมดแล้ว แต่กระจาย 6 หน้า โพสต์นี้สรุปให้จบในที่เดียว

พอเห็น mental model 4 ก้อนนี้แล้ว เรื่อง decision ว่าจะใช้ตอนไหนตามมาเองโดยไม่ต้องท่องจำ

.

 Mental model 4 ก้อนที่ต้องเห็นก่อน

 session = ไฟล์ JSONL plaintext บน disk ของเครื่องคุณเอง path คือ ~/.claude/projects//.jsonl เปิดด้วย cat ดูได้

 context = working memory ของ session ปัจจุบัน default 200K tokens แชร์กันระหว่าง system prompt, CLAUDE.md, skills, tool definitions และ message history

 /compact = summarize conversation ทำงานต่อ topic เดิม

 /clear = เริ่ม conversation ใหม่ context ว่างเปล่า ของเก่ายังอยู่ resume กลับมาได้

.

 /compact ทำอะไรจริงๆ และเก็บอะไรไว้

ตาม docs ของ Anthropic /compact คือ "Free up context by summarizing the conversation so far. Optionally pass focus instructions for the summary."

syntax ใช้ได้ 2 แบบ คือ /compact เฉยๆ สรุปทั่วไป หรือ /compact focus on the API changes บอกให้ focus topic ที่อยากเก็บเป็นพิเศษ

ของที่ Claude preserve คือ user requests กับ key code snippets ส่วนที่อาจหายคือ detailed instructions ตอนต้น conversation เพราะ Claude มองว่า request สำคัญกว่า rule รายละเอียด

 จุดที่ surprise dev หลายคนคือ skill descriptions listing จะไม่ re-inject หลัง /compact เฉพาะ skill ที่ invoke จริงในรอบที่ผ่านมาเท่านั้นที่ preserve

ถ้าอยาก control ว่า /compact เก็บอะไรเป็นพิเศษ ใส่ section ชื่อ "Compact Instructions" ใน CLAUDE.md ของโปรเจกต์ Claude จะอ่านเป็น guideline ตอน summarize ทุกครั้ง

.

 /clear ต่างจาก /compact ตรงไหน

quote เดียวจาก docs ตอบทุกอย่าง

"Start a new conversation with empty context. The previous conversation stays available in /resume. To free up context while continuing the same conversation, use /compact instead."

จุดสำคัญที่หลายคนเข้าใจผิดคือ /clear ไม่ได้ทำลาย session เก่า ของเดิมยังอยู่บน disk เสมอ คำว่า clear หมายถึง clear context window ของรอบปัจจุบัน ไม่ใช่ delete session

/clear มี alias /reset กับ /new ทั้ง 3 ตัวทำงานเหมือนกัน

.

 Decision rule 1 บรรทัด

ทำงานต่อ topic เดิม → /compact

สลับไป topic ใหม่ → /clear

.

 โบนัส 3 เรื่องที่ dev ใช้ Claude Code ทุกวันควรรู้

 subagent isolation : งานที่ค้นข้อมูลหรืออ่านไฟล์เยอะๆ ส่งให้ subagent ทำ ตัวอย่างจาก docs ถ้า subagent อ่านไฟล์ 6,100 tokens แล้วสรุปกลับมา 420 tokens main session โตแค่ 420 tokens เท่านั้น ส่วน 5,680 tokens ที่เหลือไม่กระทบ main เลย

 1M context tier : model ที่รองรับมี 3 ตัวคือ Opus 4.7, Opus 4.6 และ Sonnet 4.6 ใครใช้ Max, Team, Enterprise plans ได้ Opus 1M อัตโนมัติไม่ต้องตั้งค่า ส่วน Pro plan ต้อง extra usage ปิดทั้งหมดผ่าน env var CLAUDE\_CODE\_DISABLE\_1M\_CONTEXT=1

 session resume : claude -c ต่อ session ล่าสุดใน working directory ปัจจุบัน claude --resume เปิด picker เลือก session ที่อยากต่อ --fork-session สร้าง branch ใหม่เหมือน git branch แต่กับ conversation

.

 จุดที่หลุดบ่อย

CLAUDE.md กับ MEMORY.md auto load แค่ 200 บรรทัดแรกหรือ 25KB whichever comes first ถ้าไฟล์ยาวกว่านั้นบรรทัดที่ 201 ขึ้นไปไม่โหลด

session แต่ละตัวเป็นอิสระจากกัน session ใหม่เริ่มด้วย context ว่างเปล่าทุกครั้ง ของจาก session ก่อนหน้าไม่ติดมาด้วย

rule ที่อยากให้ persist ข้าม session ต้องอยู่ใน CLAUDE.md ไม่ใช่ฝากไว้ใน chat ของ Anthropic เขียนชัดว่า "Put persistent rules in CLAUDE.md rather than relying on conversation history"

.

อยากเห็นว่า session ปัจจุบันใช้ context ไปเท่าไหร่ ลองพิมพ์ /context ใน Claude Code จะเห็น grid สีของ usage จริงพร้อมคำแนะนำ optimization

อ่านฉบับเต็มมีตัวอย่าง syntax ครบ + diagram subagent isolation + decision tree /compact vs /clear ลิงก์อยู่ในคอมเมนต์แรก
