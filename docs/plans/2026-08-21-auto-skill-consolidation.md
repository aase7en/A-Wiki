# แผน: Auto-Skill Consolidation — สมองชาญฉลาดแบบ Pattern เดียว

> สร้าง 2026-08-21 (ก่อน context compaction) · ผู้อนุมัติ: user (วิสัยทัศน์ต้นฉบับฝังในนี้)
> สถานะ: PLANNED — ยังไม่ implement · อ่านคู่กับ `docs/architecture/SYSTEM-ARCHITECTURE.md`

## 1. วิสัยทัศน์ของ user (บันทึกตรงตามเดิม)

สมองต้องทำงานเป็น **pattern เดียวอัตโนมัติ** — user แทบไม่ต้องเลือก skill:

```
วางแผน/คิดวิเคราะห์ถี่ถ้วน (Plan+Think)
  → GRILL: AI ถามกลับ "ตรงไหนควรเสริม/แก้/ไอเดียจริงเป็นแบบไหน?"
  → BRAINSTORM sub-agents ช่วยกันคิด/เช็ค
  → IMPLEMENT → Loop Engineer หา bug
  → เปิด PR → ตรวจละเอียด → loop จน Production ใช้ได้จริง
```

ครอบคลุม 7 โดเมน: **Design · เว็บ · แอป · แต่งรูป · เอกสารราชการ · กฎหมาย · ธุรกิจ**
ส่วน skill ที่ต้อง active เอง เหลือเฉพาะงานเฉพาะตัว user (เอกสาร รพ./ราชการไทย/ธุรกิจส่วนตัว)

## 2. ข้อค้นพบหลัก: pattern นี้มีอยู่แล้ว ~90% ใน A-Suite

| ขั้นตามวิสัยทัศน์ | ของที่มีอยู่แล้ว | ช่องว่างจริง |
|---|---|---|
| Plan+Think | `a-think` (7-step loop) + `a-plan` (chain บังคับ grill) | ต้องจำชื่อคำสั่งเยอะ |
| Grill ถามกลับ | `grill-with-docs` + `grill-me` (mattpocock) | อยู่ใน chain a-plan แล้ว แต่ไม่ auto ถ้าไม่เรียก /A-Plan |
| Brainstorm ช่วยกันคิด | `a-council` (4 personas + block-ship) + superpowers `brainstorming` | ยังแยกกัน |
| Loop หา bug | `a-debug` (debug-mantra+TDD) + `a-loop` | พร้อม |
| PR + review loop | review-flow rule #11 (draft PR ก่อน review) + verify gate | พร้อม |

**ดังนั้นงานจริง = รวมเป็น ONE ENTRY** (`/A <objective>` หรือ reinforcement ของ a-router ให้ default เข้า spine เสมอ) + จัด tier ของ 243 skills

## 3. ข้อเสนอจัด Tier (เป้าหมาย: user ใช้น้อยที่สุด)

| Tier | จำนวนเป้า | ตัวอย่าง | กลไก |
|---|---|---|---|
| **AUTO** (agent ดึงเองตาม intent) | ~40 | a-think/plan/flow/council/debug/loop + domain dispatchers (a-web/a-design/a-content/a-agent/a-backend) + lifecycle skills + render/pdf/docx ฯลฯ | tier-2 fallback (ทำแล้ว PR#24) + a-router spine |
| **MANUAL** (user เรียกเอง — งานเฉพาะตัว) | ~15 | a-doc/a-med-order/a-rabies-report/thai-gov forms/thai-invoice/a-rabies | คง registry + trigger ชัด |
| **ARCHIVE** | ~190 | ecosystem ซ้ำ/ไม่เคยใช้/vendor-specific | ย้าย `skills/_archive/` + status: archived ใน registry (ห้ามลบ — ยัง grep ได้) |

วิธี: registry-driven (แก้ `skills-registry.json` + `consolidate.py` มีอยู่แล้ว) → regen → ทุก agent surface ลดลงตาม

## 4. ข้อบกพร่องจริงจาก audit (2026-08-21 — ต้องแก้ก่อน/พร้อมแผน)

| # | ความรุนแรง | สิ่งที่พบ (evidence ใน memory ledger) |
|---|---|---|
| 1 | 🔴 HIGH | ~~**ZCode ไม่มี PreToolUse wiring เลย**~~ **✅ FIXED 2026-08-22** — เพิ่ม `zcode` adapter ใน `scripts/hooks/providers.py` (Claude-shaped, verified live) + generator `scripts/setup-zcode-config.py` (merge hooks section, preserve mcp) + `.zcode/config.json` เครื่องนี้ wire แล้วทั้ง 6 events (sweep ไม่ใช่ named dispatch) — 17 hard gates live บน ZCode ตั้งแต่ session ถัดไป (config อ่านตอน startup) |
| 2 | 🔴 HIGH | Gemini ขาด PostToolUse/Stop/UserPromptSubmit (19/29 live) |
| 3 | 🟡 MED | registry 30/243 paths ชี้ `~/.claude/...` = machine-dependent พังบน clone อื่น |
| 4 | 🟡 MED | 2 skills description ว่าง (assessment-generator, word-generator) + gate ไม่ตรวจ + ใช้ `# Skill:` แทน frontmatter |
| 5 | 🟡 MED | Gemini wrapper แปลง exit ทุกตัวที่ ≠0 เป็น block (ล้นเจตนา) |
| 6 | 🟢 LOW | scan.py เงียบ/รันตรงไม่ได้ · draft.json drift 331 vs 243 · council `cb839d5d` ยังเปิด |

## 5. ไอเดียจาก community (สำรวจ GitHub 2026-08-21 — รับมาพัฒนาต่อ)

| ไอเดีย | ที่มา | ปรับใช้กับ A-Wiki ยังไง |
|---|---|---|
| Self-maintaining wiki loop | llm-wiki-agent (3.4k★) | ต่อยอด a-loop Phase 9: agent อ่าน source ที่หล่นใน raw/ → อัป wiki เอง (ผ่าน promotion gate เท่านั้น) |
| Graph-of-Thought จัด mind-map | Neurite (2.1k★) | brain-map.canvas มีแล้ว — เพิ่ม conductor `graph-path` (BFS 2 concept) |
| Rollbackable graph memory | nocturne_memory (1.3k★) | L1 ledger + .tmp-sync มีแล้ว — เพิ่ม rollback marker ต่อ entry |
| Self-evolving context DB | OpenViking | เป็นเป้าเฟส 8+ (eval loop) ฝั่งสมอง |
| Content→Skill pipeline | cangjie-skill / book-to-skill | ต่อ `ingest-source` → เสนอ skill ใหม่ผ่าน A-Loop Phase 4 (มี mechanism พอดี) |

### 5.1 สำรวจ Social (2026-08-22 — X/TikTok/Facebook/YouTube ผ่าน Brave search; DDG โดน CAPTCHA, YouTube direct JS-rendered)

**X/Twitter** — @milesdeutscher: second brain Claude+Obsidian trained on years of knowledge · @0xkkai: kepano (Obsidian creator) ปล่อย official Claude Skills pack — 44k installs · @oikon48: subagents persistent memory ผ่าน frontmatter + agent-memory dir · @NickSpisak_: skill trio `/second-brain` `/ingest` `/query` (scaffold vault + process sources → wiki pages) · @Av1dlive: Karpathy wiki-based second brain (claude-obsidian plugin) — notes queryable + **compound over time** · @Bober_smart: 20-min second-brain folder setup

**TikTok** — @techtiff: port ChatGPT memory เข้า Claude + JSON-file external brain สำหรับ business · @willfrancis24: **nightly memory synthesis** + built-in RAG chat search + import ChatGPT memories · @jaredrhod: ย้าย memory ไป Obsidian + disable native memory → "memory vault" บน GitHub · @taki.gpt: Claude Code + Obsidian pairing

**Facebook** — กลุ่ม Claude AI Community / Claude Community: ถาม "second brain คุ้มไหม?", tutorial markdown-for-Claude — สัญญาณ = คนทั่วไปยังสับสนเริ่มยังไง (ไม่มีไอเดียเทคนิคใหม่)

**YouTube** — "How To Build The ULTIMATE AI Second Brain (Obsidian + Claude Code)" (58:33, เม.ย.) · "Claude Built the Ultimate Second Brain" (ก.ค.) · "Every Way To Set Up A Claude Second Brain Explained" (มิ.ย.) — แนวทาง setup-guide ยาว ไม่มี architecture ใหม่

### 5.2 ไอเดียที่รับมาใช้ได้จริง (distilled)

| ไอเดีย | ที่มา | ปรับใช้กับ A-Wiki |
|---|---|---|
| Skill trio เดียวจบ: ingest + query ใน entry เดียว | @NickSpisak_ (X) | ยืนยัน `/A` one-entry (§6.2) — community มาถึง conclusion เดียวกัน |
| **Nightly memory synthesis** (cron) | @willfrancis24 (TikTok) | a_loop_distill ตอน Stop มีแล้ว — เพิ่ม nightly cron กลั่น ledger → เสนอ promotion (เฟส 8+) |
| Subagent memory แยกต่อ persona | @oikon48 (X) | a-council personas ยังไร้ memory ส่วนตัว — บันทึกเป็นไอเดีย follow-up |
| Cross-vendor memory import (ChatGPT → Claude) | @techtiff (TikTok) | cross-device sync มีแล้ว — cross-**vendor** import เป็นช่องใหม่ (low priority) |
| "Compound over time" เป็น metric | @Av1dlive (Karpathy) | วัด graph growth + recall hit-rate ต่อเดือน = evidence ว่าสมองโตจริง |
| Markdown-first vault เป็น standard | kepano 44k installs (X) | ยืนยัน wiki/ markdown ใช้ถูกทาง — อย่าเปลี่ยน schema |

## 6. ลำดับงาน (เมื่อ implement รอบหน้า)

1. **แก้ defect #1–#2 ก่อน** (hook wiring ZCode/Gemini) — งานเล็ก ผลใหญ่ ผ่าน gate ทุกชั้น
2. `/A` one-entry: แก้ a-router ให้ default เข้า spine (จุดเดียว ไม่ต้องแตะ skills อื่น)
3. Consolidation ตาม tier (§3) ผ่าน registry + consolidate.py + regen ทุก surface
4. แก้ defect #3–#5 ระหว่างทาง
5. E2E: user พิมพ์ `/A ทำเว็บ X` → คาดหวัง think→grill(ถามกลับ)→council→implement→debug→PR→verify→พร้อม production — บันทึก evidence

## 7. Memory checkpoint (สำหรับ compaction)

- บันทึกแล้วใน `.tmp/memory-ledger.jsonl` 3 entries (decision/lesson/idea, session `zcode-p5to7-20260821`)
- สถานะ repo: main `7f9881c3` CI ✅ · HOLD เฟส 8–11 ยังอยู่ · A-Conductor ทำ WO-052 อยู่
- Session ถัดไป: อ่านไฟล์นี้ + SYSTEM-ARCHITECTURE.md + COLLAB = รู้ครบทุกบริบท
