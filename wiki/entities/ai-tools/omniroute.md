---
type: entity
category: tool
tags: [ai-router, llm-proxy, mcp, token-compression, ai-tools, dev-tools, brain-improvement-gate]
sources: [github-omniroute, github-claude-code-router]
created: 2026-07-11
updated: 2026-07-11
last_verified: 2026-07-11
verify_tool: WebFetch
---

# OmniRoute

**ประเภท**: Local multi-provider LLM gateway/proxy (Node.js daemon) + request-side token-compression stack
**สถานะ**: ประเมินผ่าน brain-improvement-gate แล้ว — **REJECT-FOR-NOW, ไม่ติดตั้ง**
**License**: MIT — https://github.com/diegosouzapw/OmniRoute

## ภาพรวม

OmniRoute เป็น open-source local gateway ที่รวม LLM provider หลายร้อยเจ้าไว้หลัง OpenAI-compatible endpoint เดียว (`http://localhost:20128/v1`) พร้อม 17 routing strategies, auto-fallback ข้าม provider เมื่อ quota หมด, และ compression pipeline ชื่อ "RTK + Caveman" ที่อ้างว่าลด token ได้ 15-95%. Repo สร้างเมื่อ 2026-02-13 (~5 เดือนก่อนวันตรวจ) โดย diegosouzapw, ขึ้น GitHub Trending #1 เมื่อ 2026-06-30, ปัจจุบัน 15,138 ดาว / 2,312 fork / 241 open issues (จาก issue number สูงสุดที่พบคือ #6846 — แปลว่ามี issue ถูกเปิดไปแล้วกว่า 6,800 รายการในเวลาไม่ถึงครึ่งปี, churn สูงมาก) [verified 2026-07-11].

A-Wiki repo นี้**มี stack ที่ทำหน้าที่ทับซ้อนอยู่แล้ว 3 ชั้น**: (1) provider registry + cost-first pyramid (`wiki/context/providers.json`, `scripts/model-scout-current.py`, `scripts/swarm/delegate.sh`), และ (2) **claude-code-router (ccr) ที่ติดตั้งและ wire ไว้แล้วจริง** (`scripts/ccr/`, `scripts/gen-ccr-config.py`, `~/.claude-code-router/config.json` — commit ล่าสุด 2026-06-17). รายละเอียดเปรียบเทียบและเหตุผล reject อยู่ด้านล่าง.

## คุณสมบัติหลัก (ตามที่ OmniRoute claim)

- **Providers**: อ้าง 237 (ในคำอธิบาย task), แต่ README badge ของ repo เองเขียน "231+", และหน้า wiki เปรียบเทียบของโปรเจกต์เอง ("OmniRoute vs Alternatives", audited 2026-Q2) เขียน "207+" — **ตัวเลขไม่ตรงกันเองข้าม 3 หน้าในโปรเจกต์เดียวกัน** ถือเป็น marketing-velocity red flag ไม่ใช่ข้อมูลผิดร้ายแรง แต่บ่งชี้ว่าตัวเลขโปรโมทเปลี่ยนเร็วกว่าที่ maintainer sync เอกสาร
- **17 routing strategies**: priority, fill-first, weighted, round-robin, P2C, least-used, random/strict-random, cost-optimized, headroom, reset-window, reset-aware, context-relay, context-optimized, LKGP (last-known-good-path), auto (9-factor live scoring — default), fusion (fan-out หลาย model แล้วให้ judge model สังเคราะห์คำตอบ), quota-share (แบ่งโควตาทีม)
- **Compression "RTK + Caveman"**: pipeline 10 engine (session-dedup, CCR archive, RTK tool-output filter, headroom table-compaction, relevance extraction, Caveman rule-based prose compression, LLMLingua-2 ML pruning ผ่าน MobileBERT ONNX, lite whitespace trim, aggressive summarization, ultra heuristic pruning) — โหมด lite ~15% ถึง stacked RTK→Caveman 78-95%. อ้างว่า code block/URL/JSON ถูก "protect byte-perfect เสมอ" — **compress แบบ lossy เฉพาะ prose/tool-output ไม่ใช่ทั้ง prompt**, กลไกต่างจาก `/caveman` ของ A-Wiki (ดูหัวข้อเปรียบเทียบ)
- **MCP server ในตัว**: 95 tools, 3 transport (stdio/HTTP/SSE), 30 scope
- **รันเป็น always-on daemon**: Node.js 22/24 LTS process เดียวรวม CLI + web dashboard + API gateway บนพอร์ต 20128, streaming ผ่าน SSE + WebSocket; มี Electron desktop app แยกต่างหากด้วย
- **ขนาด repo**: 260,683 KB (~260MB) — รวม Next.js frontend, Electron app, test suite 21,000+ case ใน 2,586 ไฟล์ (ตัวเลขนี้ self-reported จาก README ไม่ได้ audit อิสระ)
- **Windows**: รองรับผ่าน npm / Docker / Electron — ใช้งานได้จริงบน Windows [training, ยังไม่ได้ทดสอบติดตั้งจริงในเครื่องนี้]

## Key Handling & ความเสี่ยง ToS — จุดที่ต้องระวังที่สุด

OmniRoute เข้ารหัส key/OAuth token ด้วย AES-256-GCM แบบ local-only ไม่มี cloud intermediary — ส่วนนี้ปลอดภัยดี. **แต่** โปรเจกต์มีฟีเจอร์ "stealth" (`docs/security/STEALTH_GUIDE.md`, `MITM-TPROXY-DECRYPT.md`) ที่ทำ:

- **TLS fingerprint impersonation (JA3/JA4)** — ปลอมลายนิ้วมือ TLS ให้เหมือน Chrome/Firefox client ตัวจริง
- **Header/body field reordering** ให้ตรงกับ fingerprint ของ CLI ทางการที่ capture ไว้
- **"Integrity token" generation** เช่น "Client Content Hash for Claude" — คือการปลอม token ยืนยันตัวตนที่ provider ใช้แยกแยะ client ทางการ
- **Obfuscation ด้วย zero-width joiners** สำหรับ identifier ที่ sensitive

เอกสารของโปรเจกต์เองระบุว่าทำไปเพื่อให้ "user-owned official accounts" ใช้งานผ่าน unified API ได้ต่อเนื่อง ไม่ใช่เพื่อ "evade fraud detection หรือละเมิด ToS" — **แต่กลไกที่อธิบายมาคือสิ่งเดียวกับการ evade bot-detection ในทางเทคนิค** ไม่ว่าเจตนาจะเป็นอย่างไร. นี่คือความเสี่ยงประเภทเดียวกับที่ A-Wiki เองเคยตัดสินใจหลีกเลี่ยงไปแล้วอย่างชัดเจน — ดูหมายเหตุใน `scripts/ccr/config.json` ปัจจุบัน: *"GLM Coding Plan is NOT routed here — Z.ai ToS forbids third-party proxies for the subscription."* การเอา stealth layer ของ OmniRoute มาใช้กับ traffic ของ Anthropic/OpenAI/Google จะขัดกับจุดยืนเดิมของ repo นี้โดยตรง [verified 2026-07-11, อ่านจาก `docs/security/STEALTH_GUIDE.md` ต้นทาง].

## claude-code-router (ccr) — ของเดิมที่ A-Wiki ติดตั้งและ wire ไว้แล้ว

- **ติดตั้ง global อยู่แล้วบนเครื่องนี้**: `@musistudio/claude-code-router@2.0.0` (ตรวจผ่าน `npm ls -g`) — **latest บน npm คือ 3.0.3** (`npm view` ตรง) → ของที่ติดตั้งอยู่ตกรุ่นไป 1 major version [verified 2026-07-11]
- **Repo**: สร้าง 2025-02-25 (~1.5 ปี, เก่ากว่า OmniRoute มาก), 35,732 ดาว, 2,943 fork, 995 open issues, MIT [verified 2026-07-11]
- **A-Wiki มี integration จริงอยู่แล้ว**: `scripts/ccr/config.template.json` (public-safe, placeholder `${SECRET_NAME}` เท่านั้น) → `scripts/gen-ccr-config.py` render เป็น `~/.claude-code-router/config.json` โดยดึงค่าจาก `drive/.secrets` on-demand → `scripts/launch-ccr.sh` / `.ps1` รัน `ccr code`. Commit ล่าสุดของชุดนี้คือ 2026-06-17 (Auto-commit session)
- **Router map ผูกกับ Cost-First pyramid อยู่แล้ว**: `background`→gemini-flash, `default`→deepseek-chat, `think`→deepseek-reasoner, `longContext`→gemini-pro (threshold 60k) — ตรงกับแนวคิด tier ของ `docs/protocols/model-switching.md`
- **จุดที่ A-Wiki ตัดสินใจไว้แล้วอย่างมีเหตุผล**: GLM Coding Plan **ไม่** ถูก route ผ่าน ccr เพราะ Z.ai ToS ห้าม third-party proxy กับ subscription — รัน GLM ตรงผ่าน `scripts/launch-glm.*` แทน. นี่คือตัวอย่างวินัยที่ OmniRoute (ด้วย stealth layer) จะขัดแย้งด้วยถ้านำมาใช้แทน
- **2.0 vs 3.0 feature gap** (จาก WebSearch): เวอร์ชัน 3.x เพิ่ม Electron desktop app, SQLite persistence, system tray, agent config สำหรับ Codex/ZCode multi-instance, fusion model (รวม base model + vision/web-search/MCP) — ของที่ติดตั้งอยู่ (2.0.0) ยังเป็นรุ่น CLI-centric ไม่มีของพวกนี้

## เปรียบเทียบ: OmniRoute vs claude-code-router vs A-Wiki native (model-scouter + delegate.sh)

| มิติ | OmniRoute | claude-code-router (installed 2.0.0 / latest 3.0.3) | model-scouter + delegate.sh (native, ไม่มี daemon) |
|---|---|---|---|
| Routing | 17 strategies, auto 9-factor live scoring, fusion fan-out+judge, quota-share | Scenario rules (default/background/think/longContext) + threshold, fallback config field | Task-type → tier (L1-L4) → capability-ranked provider จาก `providers.json` + `model-capability-scores.json` |
| Fallback | Circuit breaker, cooldown, model lockout, anti-thundering-herd | Basic fallback field ต่อ scenario | Self-healing: model-not-found → rescout → retry 1 ครั้ง; rate-limit → แนะนำ race mode |
| Compression | RTK+Caveman 10-engine, ทำงานบน request/tool-output stream จริง, lossy เฉพาะ prose, 15-95% | ไม่มี built-in — เป็น router/proxy ล้วน | `/caveman` = วินัยการตอบสั้นของ **assistant เอง** (output side) ไม่ใช่ pipeline บีบอัด conversation/tool-output ที่ส่งเข้า model — **คนละกลไก ไม่ควรเทียบตรง** |
| Key handling | AES-256-GCM local, **แต่มี TLS/JA3-JA4 stealth + integrity-token spoofing** เพื่อเลียนแบบ official client — ความเสี่ยง ToS | Plaintext ใน `~/.claude-code-router/config.json` (generate จาก `drive/.secrets`, ไม่มี stealth layer) | env var name เท่านั้นใน `providers.json` (public-safe), value ดึง on-demand จาก `drive/.secrets` |
| MCP | มี embedded server 95 tools/3 transport | ไม่ใช่ MCP server (Claude Code เองเป็น MCP client อยู่แล้ว) | ใช้ GitNexus/awiki MCP แยกชั้น ไม่ปนกับ routing |
| Cost tracking | Dashboard UI ในตัว, quota-share pool | ไม่มี live dashboard, ดูจาก config เท่านั้น | Live Dashboard `scripts/live-dashboard/server.py :7790` — auto-start ทุก platform, แสดง route_plan/model_active real-time |
| Maintenance burden | **Always-on Node daemon + Electron ทางเลือก, repo 260MB, Next.js frontend, 5 เดือนอายุ, 261 contributor, ตัวเลข provider ไม่ตรงกันเอง 3 จุด** | เบากว่า (CLI + Electron ทางเลือก), 1.5 ปีอายุ, mature, แต่ของที่ติดตั้งตกรุ่น 1 major version | Bash/Python script ล้วน ไม่มี daemon ใหม่, ผูกกับ hook/dashboard อยู่แล้ว |
| Windows | ได้ (npm/Docker/Electron) [training, ยังไม่ทดสอบจริง] | ได้ — ยืนยันแล้วว่าติดตั้งและรันได้บนเครื่องนี้ | ได้ — native, มี PowerShell mirror ของทุก script |

## Gate Verdict — REJECT-FOR-NOW

**Brain Gate fields** (`docs/protocols/brain-improvement-gate.md`):
- **Gain**: ต่ำ-ถึง-ลบ — ฟังก์ชันหลัก (multi-provider routing, fallback, cost-aware selection) ทับซ้อนเกือบสมบูรณ์กับ provider registry + delegate.sh + ccr ที่มีอยู่แล้ว. ส่วนที่ต่างจริง (RTK+Caveman compression pipeline) มีค่า **ในทางทฤษฎี** แต่ต้อง route Claude Code traffic จริงผ่าน daemon ของบุคคลที่สามถึงจะได้ใช้ — เสี่ยงกระทบ Iron Law #3 (Primary Agent/Senior Critic ต้องเป็น Claude ตัวจริง ไม่ใช่ถูกสลับโมเดลเงียบๆ โดย proxy)
- **Shape**: ไม่ผ่าน "lightest shape first" — ต้องมี always-on Node daemon ใหม่ + Electron ทางเลือก ซึ่ง task นี้ระบุชัดว่า "no new always-on daemon unless clearly earns it" และ gain ที่พิสูจน์ได้ไม่มากพอจะ earn มัน
- **Weight**: หนัก — repo 260MB, Next.js + Electron + 21k test file, เทียบกับ ccr ที่เบากว่าและมีอยู่แล้ว หรือ delegate.sh ที่เป็น bash/python ล้วน
- **Safety**: ❌ **จุดตัดสิทธิ์หลัก** — stealth layer (TLS/JA3-JA4 impersonation, integrity-token spoofing) คือกลไก evade bot-detection ในทางเทคนิคไม่ว่าเจตนาจะเป็นอะไร ขัดกับจุดยืนที่ A-Wiki ทำไว้แล้วเรื่อง Z.ai ToS ใน `scripts/ccr/config.json`. นำมาใช้กับ Anthropic/OpenAI/Google traffic เสี่ยง account ban ของ user
- **Verify**: ไม่มี command ตรวจสอบที่ทำให้ risk ข้างต้นหายไป — เป็น architectural risk ไม่ใช่ bug ที่ patch ได้

**เหตุผลสรุป**:
1. A-Wiki มี solution ที่ทับซ้อนอยู่แล้ว 2 ชั้น (provider registry/delegate.sh แบบ script-only + ccr แบบ proxy ที่ wire ไว้จริงตั้งแต่ 2026-06-17) — ไม่มีช่องว่างความสามารถที่ OmniRoute เติมเต็มได้ชัดเจนพอจะคุ้ม cost ของ daemon ใหม่
2. โปรเจกต์อายุ ~5 เดือน (สร้าง 2026-02-13) เทียบกับ ccr ที่อายุ ~1.5 ปี, mature กว่า (35.7k ดาว vs 15.1k), เลขโปรโมทของ OmniRoute เองไม่ตรงกันข้าม 3 หน้า (237 vs 231+ vs 207+) — สัญญาณ hype-velocity ที่ควรรอดูความนิ่งก่อน
3. Stealth/TLS-spoofing layer เป็นความเสี่ยง ToS ที่ A-Wiki เคยตัดสินใจหลีกเลี่ยงมาแล้วอย่างชัดเจนกับ provider อื่น (Z.ai) — นำ OmniRoute เข้ามาจะขัดกับวินัยเดิม
4. คำแนะนำเชิง action ที่แยกออกจาก OmniRoute โดยสิ้นเชิง: **อัปเดต ccr ที่ติดตั้งอยู่จาก 2.0.0 → 3.0.3** (`npm i -g @musistudio/claude-code-router@latest`) เพื่อได้ fusion model / agent config ใหม่ — เป็น "adopt-alongside" ของที่มีอยู่แล้ว ไม่ใช่ของใหม่

**อะไรจะเปลี่ยนคำตัดสินนี้ในอนาคต**: ถ้า RTK/Caveman compression engine ถูกแยกออกมาเป็น library/CLI ที่ไม่ต้องมี always-on daemon และไม่มี stealth layer (เช่น pipe ผ่าน stdin/stdout ครั้งเดียวต่อ session) ก็ควรพิจารณาใหม่เฉพาะส่วนนั้น — แต่ต้อง re-run gate นี้อีกครั้งเมื่อถึงจุดนั้น ไม่ผูกกับ verdict ปัจจุบัน.

## ความสัมพันธ์

- แข่งขันกับ/ทับซ้อนกับ: [[zai-glm]], `wiki/context/providers.json`, `agent-skills/swarm-intelligence/model-scouter.md`, `scripts/swarm/delegate.sh` — ชั้น routing/cost-first ที่ A-Wiki ใช้อยู่แล้ว
- เกี่ยวข้องกับ: [[live-dashboard]] — cost tracking UI ที่ A-Wiki มีอยู่แล้วแทน dashboard ของ OmniRoute
- เกี่ยวข้องกับ: [[model-capability-bench]] — capability scoring ที่ A-Wiki ใช้จัดอันดับ model ภายใน cost tier เดียวกัน
- เกี่ยวข้องกับแต่คนละกลไก: `skills/claude-code/token-optimization/SKILL.md` (`/caveman` = output-brevity discipline, ไม่ใช่ request-compression pipeline แบบ OmniRoute)
- ใกล้เคียงกันในหมวด "external router ที่ยังไม่ adopt": ไม่มีหน้าเทียบเท่ามาก่อน — นี่คือหน้าแรกที่บันทึก claude-code-router ไว้ใน wiki แม้จะติดตั้งอยู่แล้วในเครื่อง

## แหล่งข้อมูล

- GitHub: https://github.com/diegosouzapw/OmniRoute — [verified 2026-07-11] WebFetch, 15,138 ดาว, สร้าง 2026-02-13, MIT
- `docs/security/STEALTH_GUIDE.md` (OmniRoute repo) — [verified 2026-07-11] WebFetch ตรง, ยืนยันกลไก TLS/JA3-JA4 impersonation
- `wiki/OmniRoute-vs-Alternatives` (OmniRoute repo wiki, audited 2026-Q2) — [verified 2026-07-11] WebFetch, แหล่งของเลข "207+ providers" ที่ไม่ตรงกับ README
- GitHub: https://github.com/musistudio/claude-code-router — [verified 2026-07-11] WebFetch, 35,732 ดาว, สร้าง 2025-02-25, MIT
- Local: `npm ls -g` / `npm view @musistudio/claude-code-router version` บนเครื่องนี้ — [verified 2026-07-11] Bash โดยตรง, ยืนยัน installed 2.0.0 vs latest 3.0.3
- Local: `scripts/ccr/README.md`, `scripts/gen-ccr-config.py`, `scripts/ccr/config.template.json`, `~/.claude-code-router/config.json`, `git log -- scripts/ccr/` (commit `7112cb7`, 2026-06-17) — [verified 2026-07-11] อ่านตรงจาก repo/เครื่อง
- WebSearch ทั่วไปเรื่อง claude-code-router 2026 features/สถิติ — [verified 2026-07-11], อ้างอิง ClaudeLog, DeepWiki, npm registry (บางตัวเลขจาก npm registry fetch ไม่นิ่ง/ขัดแย้งกันเอง — ใช้ local `npm view` เป็นหลักแทน)
