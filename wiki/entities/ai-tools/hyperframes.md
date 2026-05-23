---
type: entity
category: framework
tags: [hyperframes, heygen, ai-tools, video-rendering, html, cli, catalog, open-source, ffmpeg]
sources: [hyperframes-official-docs]
created: 2026-05-17
updated: 2026-05-17
last_verified: 2026-05-17
verify_tool: WebSearch
---

# HyperFrames

**ประเภท**: Open-source HTML-to-video rendering framework  
**สถานะ**: Active — เหมาะกับ AI agent workflow, local video rendering, และ wiki-to-video pipeline

## ภาพรวม

HyperFrames คือ framework สำหรับเขียนวิดีโอด้วย HTML/CSS และ animation runtime แล้ว render เป็นวิดีโอหรือ image sequence ได้ [verified 2026-05-17]. จุดขายสำคัญคือ **AI-first authoring**: agent อย่าง Claude Code, Codex, Gemini CLI หรือ Cursor สามารถสร้าง composition จาก prompt ได้ เพราะอินพุตหลักเป็น HTML ไม่ใช่ DSL เฉพาะทางหรือ React-only component model.

ในบริบท wiki นี้ HyperFrames เหมาะเป็น **media layer** สำหรับแปลงความรู้ที่อยู่ใน `wiki/`, synthesis, หรือ NotebookLM summary ให้กลายเป็นวิดีโอสั้นสำหรับทบทวน, นำเสนอ, หรืออธิบาย workflow.

## คุณสมบัติหลัก

- **HTML-native composition**: เขียน scene เป็น HTML พร้อม `data-*` attributes สำหรับ timeline, duration, track, audio/video/image layer
- **CLI workflow**: `init`, `preview`, `lint`, `inspect`, `snapshot`, `doctor`, `render`
- **Agent-friendly**: command มี flag ชัดเจน, รองรับ JSON/parseable output ในบางคำสั่ง, และมี skills/plugin surface สำหรับ Claude/Codex/Cursor/Gemini
- **Deterministic rendering**: ออกแบบให้ timeline seek ได้และ render ซ้ำได้สม่ำเสมอ เมื่อ input และ environment เหมือนเดิม
- **Frame Adapter pattern**: ใช้งานร่วมกับ GSAP, Anime.js, CSS animations, Lottie, Three.js, Web Animations API
- **Catalog/Registry**: เพิ่ม block สำเร็จรูปด้วย `npx hyperframes add <block>` เช่น `data-chart`, `flowchart`, `youtube-lower-third`
- **หลาย output format**: MP4 สำหรับใช้งานทั่วไป, MOV/WebM/PNG sequence สำหรับงาน transparent/compositing

## การใช้งานใน Wiki

HyperFrames ช่วยต่อยอด wiki จาก text knowledge base ไปเป็น reusable video artifacts:

| งานใน wiki | Pattern ที่ใช้ | ผลลัพธ์ |
|---|---|---|
| สรุป entity/concept | ใช้ lower third + caption + screenshot/card | วิดีโอ recap 30-60 วินาที |
| Architecture เช่น LoRa/Pi gateway | ใช้ `flowchart` block + animated path | อธิบาย topology ให้เห็นภาพ |
| Dashboard/IoT data | ใช้ `data-chart` + screen capture | วิดีโออธิบาย trend หรือ demo dashboard |
| Pharmacy workflow | scene ขั้นตอน OCR -> validation -> export order | สื่อ requirement ก่อนลงมือ build |
| Env health report | chart + flow + narration | training/briefing video จาก synthesis |
| NotebookLM summary | summary script -> storyboard -> render | วิดีโอทบทวน snapshot แต่ละ domain |

## สถานะบนเครื่องนี้

ตรวจเมื่อ 2026-05-17:

| รายการ | สถานะ | หมายเหตุ |
|---|---|---|
| Node.js | พร้อม: `v24.15.0` | ผ่าน requirement `node >=22` |
| npm | พร้อม: `11.12.1` | ใช้ `npx hyperframes` ได้ |
| FFmpeg | ยังไม่พบ | ต้องติดตั้งก่อน render video local |
| npm latest | `hyperframes@0.6.14` | ตรวจจาก `npm view hyperframes version` |
| GitHub latest release | `v0.6.13` | release page ที่ตรวจวันที่ 2026-05-17 |

> [!WARNING] ก่อนใช้งาน render จริง
> ติดตั้ง FFmpeg ก่อน เช่น `brew install ffmpeg` บน macOS แล้วรัน `npx hyperframes doctor` เพื่อตรวจ dependency อีกครั้ง.

## Quick Commands

```bash
# ติดตั้ง skill ให้ AI agent
npx skills add heygen-com/hyperframes

# สร้างโปรเจกต์วิดีโอใหม่
npx hyperframes init wiki-video --example blank --tailwind
cd wiki-video

# Preview / lint / render
npx hyperframes preview
npx hyperframes lint
npx hyperframes render --output output.mp4

# เพิ่ม block จาก catalog
npx hyperframes add data-chart
npx hyperframes add flowchart
```

## ข้อดี / ข้อจำกัด

| ข้อดี | ข้อจำกัด |
|---|---|
| AI เขียนได้ง่ายเพราะใช้ HTML/CSS | ต้องมี FFmpeg และ browser/Chrome runtime |
| เหมาะกับวิดีโอสั้นจาก wiki/synthesis | ยังต้องจัดการ asset, font, audio, timing เอง |
| Catalog ช่วยลดเวลาทำ chart/flow/overlay | Version เปลี่ยนเร็ว ควร pin ในโปรเจกต์จริง |
| Apache-2.0 ใช้งานเชิงพาณิชย์ได้ | Render ใช้ CPU/Chrome/FFmpeg ค่อนข้างหนัก |
| รองรับ transparent video สำหรับ overlay | ไฟล์ output อาจใหญ่ ไม่ควร commit วิดีโอทุกไฟล์เข้า repo |

## ความสัมพันธ์

- ใช้ร่วมกับ: [[concepts/ai-tools/vibe-coding]]
- ใช้ร่วมกับ: [[concepts/ai-tools/openrouter-claude-code]]
- ใช้ร่วมกับ: [[synthesis/dual-ai-workflow]]
- ใช้ร่วมกับ: [[synthesis/wiki-to-video-pipeline]]
- แปลงความรู้จาก: [[synthesis/iot-lora-architecture]], [[synthesis/pharmacy-order-checker]], [[synthesis/appsheet-to-webapp-pi5]]
- แนวคิดใกล้เคียง: Remotion, Manim, After Effects scripting, browser-based video rendering

## แหล่งข้อมูล

- [[sources/hyperframes-official-docs]] — Official repo/docs/catalog + local environment check [verified 2026-05-17]
