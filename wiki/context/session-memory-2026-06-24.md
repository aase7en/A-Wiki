## [2026-06-24] Cross-Device Sync + WSL2 Setup + Model Roster Update

### Done
- **Cross-Device Sync Architecture**: 3-Layer Sync (Wiki Brain, Hermes Context, Platform-specific)
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
  - Fallbacks: cohere/north-mini-code, nvidia/nemotron-3-ultra-550b-a55b, openrouter/owl-alpha
  - Commit 29213f4 → push 03f577b ✅

- **Delegate Test**: รัน delegate.sh search "test" ผ่าน WSL2
  - Route task → Tier 1 → gemini-2.5-flash
  - Response: "Test received! I'm here and ready to help." ✅
  - Confirmed: GOOGLE_AI_STUDIO_KEY → GEMINI_API_KEY อัตโนมัติ

### Key Decisions
- **WSL2 > Option B (PowerShell)**: ใช้ WSL2 แทน PowerShell script
  - ไม่ต้องเขียนโค้ดใหม่
  - สคริปต์เดิมใช้ได้เลย
  - ง่ายสำหรับคนไม่เชี่ยวชาญ IT

- **Env var handling**: delegate.sh ใช้ GOOGLE_AI_STUDIO_KEY → GEMINI_API_KEY อัตโนมัติ

### Files Created
- scripts/hermes/sync-context.sh (Layer 2 sync)
- scripts/sync-kilo-settings.ps1 (Layer 3 sync)
- scripts/hooks/session-start-hermes-sync.sh
- scripts/hooks/session-stop-hermes-sync.sh
- docs/protocols/cross-device-sync.md

### Commits
- d7f63e4: feat(ops): cross-device sync — Layer 2 + Layer 3
- 29213f4 → 03f577b: chore(wiki): update model roster via WSL2

### Open
- Layer 3 sync: KiloCode settings ระหว่าง Mac ↔ Windows (manual)
- Sunday Estate Cloudflare Tunnel
- Dream projects: Personal AI Agent, IoT Dashboard, Pharmacy App
