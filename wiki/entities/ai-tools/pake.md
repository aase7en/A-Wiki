---
type: entity
category: tool
tags: [rust, tauri, desktop-app, web-wrapper, lightweight, pake]
sources: [pake-github]
created: 2026-06-21
updated: 2026-06-21
last_verified: 2026-06-21
verify_tool: WebFetch
---

# Pake — Webpage to Desktop App

**ประเภท**: Open-source packaging tool  
**สร้างโดย**: tw93 (56k+ GitHub stars)  
**License**: GPL-3.0 core, built apps = user-owned  
**Tech Stack**: Rust + Tauri v2 (แทน Electron)

## ภาพรวม

Pake แปลงหน้าเว็บใดๆ ให้เป็น native desktop app (.dmg/.exe/.AppImage) ขนาด ~5MB — เล็กกว่า Electron 20 เท่า — ด้วยคำสั่งเดียว

## ความสามารถ

| ความสามารถ | รายละเอียด |
|-----------|-----------|
| CLI build | `pake <url> --name <name>` |
| GitHub Actions | Build ออนไลน์ ไม่ต้องติดตั้งอะไร |
| Custom icon | กำหนด icon จาก URL หรือไฟล์ |
| Window control | กำหนดขนาด ซ่อน title bar immersive mode |
| Shortcuts | ปุ่มลัดในตัว — back/forward/refresh/zoom |
| Cross-platform | macOS, Windows, Linux (ARM64 ด้วย) |
| Ad removal | กรองโฆษณาออกจากหน้าเว็บ |

## การใช้งานกับ A-Wiki

| แอป | URL | หมายเหตุ |
|-----|-----|---------|
| A-Wiki Live Chat | `https://aase7en.github.io/A-Wiki/awiki-live.html` | แอปแชท Hermes |
| A-Wiki Showcase | `showcase/aie-architecture.html` | ต้องการ static server |

### วิธีสร้าง (GitHub Actions)

1. Fork `tw93/Pake` → GitHub Actions → `Build App With Pake CLI`
2. กรอก: URL + Name + Icon + Window size
3. รอ ~5-10 นาที → ดาวน์โหลด artifact

### วิธีสร้าง (CLI — ต้องใช้ Mac/PC)

```bash
pnpm install -g pake-cli
pake https://aase7en.github.io/A-Wiki/awiki-live.html --name "A-Wiki Live" --width 480 --height 720
```

## ข้อดีสำหรับ A-Wiki

- **เบา**: 5MB vs Electron 100MB+
- **เร็ว**: Tauri ใช้ system webview ไม่ต้อง bund Chromium
- **ฟรี**: GPL-3.0 แต่ app ที่ build ออกมาเป็นของเรา
- **ARM64**: รันบน Pi 5 ได้

## ข้อจำกัด

- ต้องใช้ Node + Rust ถ้า build local
- บน Pi 5 ใน Docker container: ไม่มี GUI → build ผ่าน GitHub Actions แทน
- Webview ต้องมีใน OS (Linux ต้องการ WebKit2GTK)

## ความสัมพันธ์

- ใช้ร่วมกับ: [[entities/ai-tools/hermes-agent]] (wrap chat interface)
- ใช้ร่วมกับ: [[entities/ai-tools/a-wiki]] (search + showcase)
