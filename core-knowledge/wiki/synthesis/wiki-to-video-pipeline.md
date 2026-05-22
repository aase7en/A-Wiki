---
type: synthesis
tags: [wiki, hyperframes, video-rendering, notebooklm, ai-tools, knowledge-management, media-pipeline]
sources: [hyperframes-official-docs]
created: 2026-05-17
updated: 2026-05-17
---

# Wiki-to-Video Pipeline

## คำถามที่ตอบ

จะใช้ [[entities/ai-tools/hyperframes]] ร่วมกับ A-Wiki และ HyperFrames Catalog เพื่อเปลี่ยนหน้า wiki/synthesis ให้เป็นวิดีโอสั้นได้อย่างไร?

## สรุป

ใช้ wiki เป็น **knowledge source**, NotebookLM หรือ agent เป็น **script/storyboard layer**, และ HyperFrames เป็น **render layer**. ผลลัพธ์คือวิดีโอสั้นที่อธิบาย entity, concept, หรือ architecture จาก wiki โดยยังเก็บ source traceability ผ่าน wikilinks และ source pages.

เหมาะที่สุดกับงานที่ต้องสื่อสารซ้ำ เช่น IoT architecture, pharmacy order checker, environmental health report, AI tool explainer, หรือ onboarding ให้ตัวเอง/ทีม.

## Pipeline แนะนำ

```text
wiki page / synthesis
  -> extract key claims + sources
  -> write 30-90s script
  -> storyboard scenes
  -> choose HyperFrames catalog blocks
  -> render preview
  -> lint/inspect
  -> export video
  -> store artifact outside tracked wiki or under exports/ with care
```

## Mapping กับงานใน Wiki นี้

| Wiki content | HyperFrames block/pattern | วิดีโอที่ได้ |
|---|---|---|
| [[synthesis/iot-lora-architecture]] | `flowchart`, animated arrows, device cards | LoRa node -> gateway -> server walkthrough |
| [[synthesis/pharmacy-order-checker]] | process timeline, lower third, OCR before/after | Demo ขั้นตอนรับรายการยา -> validate -> export |
| [[synthesis/appsheet-to-webapp-pi5]] | dashboard mock + data chart | อธิบาย migration จาก AppSheet เป็น web app |
| [[synthesis/env-webapp-schema-wastewater]] | schema/table animation + charts | Data model briefing สำหรับระบบน้ำเสีย |
| [[concepts/ai-tools/openrouter-api]] | code card + routing diagram | Explainer เรื่อง model routing/cost-first |
| [[entities/ai-tools/hyperframes]] | catalog showcase + CLI terminal scene | Tool explainer ของ HyperFrames เอง |

## Catalog Strategy

| Catalog group | ใช้เมื่อ | ตัวอย่างใน wiki |
|---|---|---|
| Data | ต้องเล่า trend, KPI, quantity | น้ำเสีย, PM2.5, ขยะ, ยอดสั่งยา |
| Blocks / Flowchart | ต้องอธิบายระบบหรือ workflow | IoT pipeline, pharmacy validation |
| Social Overlays | ทำ short-form clip หรือ update สั้น | release note, tool tip, announcement |
| Shader/CSS Transitions | ทำ chapter break | เปลี่ยนจาก problem -> solution |
| Showcases / HTML-in-Canvas | โชว์ web app หรือ device UI | Supabase/PocketBase demo, dashboard mock |

## Workflow แบบประหยัด Token

1. ใช้ `wiki/context/wiki-overview.md` หา page ที่เกี่ยวข้องก่อน
2. ถ้าต้อง synthesize หลายหน้า ให้ export/ใช้ NotebookLM summary ก่อน
3. ให้ agent เขียน script ภาษาไทยสั้น ๆ พร้อม scene list
4. ให้ HyperFrames ทำ composition จาก scene list ไม่ใช่ให้โหลด wiki ทั้งก้อน
5. Render draft ด้วย low worker count ก่อน แล้วค่อยเพิ่ม quality/format

## Folder Policy

วิดีโอและ frame output มักใหญ่กว่า markdown มาก จึงไม่ควร commit ทุกไฟล์เข้า repo โดยตรง.

แนวทางที่ปลอดภัย:

- เก็บ source composition เป็น code/text ในโปรเจกต์ย่อย เช่น `experiments/hyperframes/<slug>/` ถ้าต้องการ version control
- เก็บ output video ไว้ใน `exports/hyperframes/` หรือ external storage แล้ว commit เฉพาะ manifest/link
- ถ้าเป็นไฟล์ใหญ่หรือ binary ให้ทำตาม policy `raw/` และ `wiki/context/local-sources.md` แทนการยัดไฟล์เข้า git

## Dependency Status

ตรวจเครื่อง local วันที่ 2026-05-17:

| Dependency | สถานะ | ผลต่อ pipeline |
|---|---|---|
| Node.js | `v24.15.0` | พร้อมใช้ HyperFrames CLI |
| npm | `11.12.1` | พร้อมเรียก `npx hyperframes` |
| FFmpeg | ยังไม่พบ | ยัง render video local ไม่ได้จนกว่าจะติดตั้ง |

## Next Experiment

ทดลองเล็กที่สุดที่คุ้ม:

```bash
brew install ffmpeg
npx hyperframes init wiki-hyperframes-demo --example blank --tailwind
cd wiki-hyperframes-demo
npx hyperframes add flowchart
npx hyperframes preview
npx hyperframes render --output wiki-hyperframes-demo.mp4
```

หัวข้อทดลองแรกที่เหมาะ: [[synthesis/iot-lora-architecture]] เพราะมี flow ของ sensor node -> gateway -> server ที่แปลงเป็น animated flowchart ได้ชัด.

## แหล่งข้อมูลที่ใช้

- [[sources/hyperframes-official-docs]]
- [[entities/ai-tools/hyperframes]]
