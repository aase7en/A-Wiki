# Session Summary — 2026-06-24

> **Purpose**: สรุปสิ่งที่ทำใน session นี้
> **Sync**: Layer 1+2 cross-device sync
> **Platform**: Windows PC (WSL2 + Ubuntu)

---

## 🔥 Active TODOs (wiki-brain)

- [x] **[wiki-brain]** ทดสอบ ash scripts/delegate.sh search "test" บนเครื่องจริง (Mac/PC) — **สำเร็จ!** ใช้ WSL2 บน Windows PC, delegate.sh ทำงานได้ผ่าน Gemini 2.5 Flash
- [x] **[wiki-brain]** รัน ash scripts/update-model-roster.sh ครั้งแรกบนเครื่องจริง — **สำเร็จ!** ใช้ WSL2 บน Windows PC, scout ได้ 25 free models จาก OpenRouter
- [ ] **[wiki-brain]** เพิ่ม GEMINI_API_KEY ใน Project Settings (ปัจจุบันใช้ GOOGLE_AI_STUDIO_KEY alias — ใช้งานได้แล้ว แต่ชื่อ canonical ดีกว่า)

---

## 🗓️ Session 2026-06-24: Cross-Device Sync + WSL2 Setup

### Done

- **Cross-Device Sync Architecture**: ออกแบบ 3-Layer Sync (Wiki Brain, Hermes Context, Platform-specific)
  - Layer 1 (Wiki Brain): Git sync ผ่าน hooks ✅
  - Layer 2 (Hermes Context): Git sync ผ่าน scripts/hermes/sync-context.sh ✅
  - Layer 3 (KiloCode settings): Manual sync ผ่าน scripts/sync-kilo-settings.ps1 ✅
  - Created docs/protocols/cross-device-sync.md (full workflow guide)

- **WSL2 Setup**: ติดตั้ง WSL2 + Ubuntu บน Windows PC
  - Installed WSL2 v2.7.8 + Ubuntu
  - Created user aase7en + password
  - Tested: wsl → Ubuntu shell ✅

- **Model Roster Update**: รัน update-model-roster.sh ผ่าน WSL2
  - Scouted 25 free models จาก OpenRouter
  - Primary: nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free
  - Fallbacks: cohere/north-mini-code:free, nvidia/nemotron-3-ultra-550b-a55b:free, openrouter/owl-alpha:free
  - Committed + pushed to GitHub ✅

- **Delegate Test**: รัน delegate.sh search "test" ผ่าน WSL2
  - Route task → Tier 1 → gemini-2.5-flash
  - Response: "Test received! I'm here and ready to help." ✅
  - Confirmed: delegate.sh ใช้ GOOGLE_AI_STUDIO_KEY → GEMINI_API_KEY อัตโนมัติ

### Key Decisions

- **WSL2 > Option B (PowerShell)**: ใช้ WSL2 แทน PowerShell script
  - ไม่ต้องเขียนโค้ดใหม่
  - สคริปต์เดิมใช้ได้เลย
  - ง่ายสำหรับคนไม่เชี่ยวชาญ IT

- **Env var handling**: delegate.sh ใช้ GOOGLE_AI_STUDIO_KEY → GEMINI_API_KEY อัตโนมัติ

- **Cross-Device Workflow**: 
  - Windows PC → GitHub (git push)
  - Mac/Pi5 → GitHub (git pull)
  - Layer 1+2 sync อัตโนมัติผ่าน Git hooks
  - Layer 3 manual sync ผ่าน copy/PowerShell script

### Files Created

- scripts/hermes/sync-context.sh (Layer 2 sync)
- scripts/sync-kilo-settings.ps1 (Layer 3 sync)
- scripts/hooks/session-start-hermes-sync.sh
- scripts/hooks/session-stop-hermes-sync.sh
- docs/protocols/cross-device-sync.md
- .gitignore (Hermes .env files protection)
- wiki/context/model-roster.conf (25 free models)
- wiki/context/session-summary-2026-06-24.md (session summary)

### Commits

- d7f63e4: feat(ops): cross-device sync — Layer 2 + Layer 3
- 29213f4 → 03f577b: chore(wiki): update model roster via WSL2
- 4a75aa0: docs(session): WSL2 setup + cross-device sync + model roster update

### Open

- Layer 3 sync: KiloCode settings ระหว่าง Mac ↔ Windows (manual)
- Sunday Estate Cloudflare Tunnel
- Dream projects: Personal AI Agent, IoT Dashboard, Pharmacy App

