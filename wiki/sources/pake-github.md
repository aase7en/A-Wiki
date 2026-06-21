---
type: source
title: "Pake — Turn any webpage into a desktop app with Rust Tauri"
slug: pake-github
date_ingested: 2026-06-21
original_file: 
tags: [rust, tauri, desktop-app, web-wrapper, lightweight, github-actions]
---

# Pake — Webpage → Desktop App

**ประเภท**: open-source tool  
**ผู้สร้าง**: tw93  
**Stars**: 56k+  
**License**: GPL-3.0 (built apps are user-owned)  

## จุดเด่น

| คุณสมบัติ | รายละเอียด |
|-----------|-----------|
| เล็ก | ~5MB ต่อแพ็คเกจ (เล็กกว่า Electron ~20 เท่า) |
| เร็ว | Rust + Tauri v2 — ใช้ RAM น้อย |
| ง่าย | 1 คำสั่ง CLI หรือ build ผ่าน GitHub Actions |
| ปรับแต่งได้ | icon, window size, immersive mode, keyboard shortcuts |
| Cross-platform | macOS, Windows, Linux (รวม ARM64) |

## วิธีใช้สำหรับ A-Wiki

1. Fork repo → GitHub Actions → ป้อน URL + ชื่อ → ดาวน์โหลด
2. หรือใช้ CLI: `pnpm install -g pake-cli && pake <url> --name <name>`
3. รองรับ Linux ARM64 — ใช้บน Pi 5 ได้

## Use Cases สำหรับ A-Wiki

| ใช้กับ | URL |
|--------|-----|
| A-Wiki Live (Chat) | `https://aase7en.github.io/A-Wiki/awiki-live.html` |
| A-Wiki Showcase | `showcase/aie-architecture.html` (local) |
| Wiki Search | TBD |

## ข้อจำกัด

- ต้องใช้ web server หรือ static hosting ก่อน (Pake wrap URL เท่านั้น)
- ARM64 build ต้องใช้ GitHub Actions (cross-compile) หรือ build บน Pi โดยตรง
- Pi 5 ต้องติดตั้ง Rust + Node ก่อน (ถ้า build local)
