---
type: source
title: "HyperFrames official repository, documentation, and catalog"
slug: hyperframes-official-docs
date_ingested: 2026-05-17
original_file: https://github.com/heygen-com/hyperframes
url: multiple official URLs
tags: [hyperframes, heygen, ai-tools, video-rendering, html, catalog, cli, open-source]
---

# HyperFrames official repository, documentation, and catalog

**ประเภท**: official repository / documentation / package registry check  
**วันที่**: 2026-05-17  
**ผู้เขียน**: HeyGen / heygen-com

## ประเด็นหลัก

1. HyperFrames เป็น open-source video rendering framework สำหรับสร้าง, preview, lint, และ render วิดีโอจาก HTML-based compositions โดยออกแบบให้ AI agents เขียนได้ง่าย [verified 2026-05-17].
2. โครงหลักใช้ HTML, CSS, timeline/animation runtime เช่น GSAP, Lottie, CSS animation, Three.js, Web Animations API แล้ว render ผ่าน browser/Chrome + FFmpeg.
3. CLI รองรับ workflow หลักคือ `init`, `preview`, `lint`, `inspect`, `snapshot`, `doctor`, และ `render` สำหรับแปลง composition เป็น MP4 หรือรูปแบบอื่น.
4. Catalog มี block/component สำเร็จรูปมากกว่า 50 รายการ เช่น social overlays, shader transitions, data visualization, effects, showcase, และ flowchart.
5. Repo ระบุ requirement เป็น Node.js >= 22 และ FFmpeg; เครื่อง local ตรวจพบ Node.js `v24.15.0` + npm `11.12.1` แต่ยังไม่พบ `ffmpeg` ใน PATH.
6. License ของ repo เป็น Apache-2.0; ใช้เชิงพาณิชย์ได้ตามเงื่อนไข license โดยไม่มี per-render fee จากตัว open-source project.

## ข้อมูลที่น่าสนใจ / สถิติ

- GitHub release page แสดง `v0.6.13` เป็น latest release วันที่ 2026-05-16.
- npm registry check วันที่ 2026-05-17 แสดง `hyperframes@0.6.14` เป็น `latest` และระบุ engine `node >=22`.
- Package surface หลักที่ repo ระบุ: `hyperframes` CLI, `@hyperframes/core`, `@hyperframes/engine`, `@hyperframes/producer`, `@hyperframes/studio`, `@hyperframes/player`, และ `@hyperframes/shader-transitions`.
- Catalog groups ที่เหมาะกับ wiki workflow: `Data Chart`, `Flowchart`, `YouTube Lower Third`, `macOS Notification`, `Reddit Post Card`, `Logo Outro`, shader transitions, และ visual effects.

## ข้อโต้แย้งหรือความขัดแย้ง

- ไม่มี contradiction กับ wiki เดิม แต่เป็น tool ใหม่ใน domain AI Tools ที่เติม capability ด้าน **knowledge-to-video** ซึ่ง wiki ยังไม่มีหน้าเฉพาะ.
- Version source มีความต่างกันเล็กน้อย: GitHub release page เห็น `v0.6.13` ส่วน npm registry เห็น `0.6.14` เป็น latest. สำหรับการติดตั้งจริงควรยึด `npm view hyperframes version` หรือ pin version ใน project.
- เครื่อง local พร้อมด้าน Node.js/npm แล้ว แต่ยังไม่พร้อม render video จนกว่าจะติดตั้ง FFmpeg.

## แหล่งข้อมูลต้นทาง

- GitHub repo: https://github.com/heygen-com/hyperframes
- Catalog: https://hyperframes.heygen.com/catalog
- CLI docs: https://hyperframes.heygen.com/packages/cli
- Rendering docs: https://hyperframes.heygen.com/guides/rendering
- Releases: https://github.com/heygen-com/hyperframes/releases
- npm package check: `npm view hyperframes version engines --json`

## หน้า Wiki ที่ได้รับการอัปเดต

- [[entities/ai-tools/hyperframes]]
- [[synthesis/wiki-to-video-pipeline]]
- [[index-ai-tools]]
