---
type: entity
category: tool
tags: [claude-code, skill, presentation, html, frontend, design, zero-dependency]
sources: [github-frontend-slides]
created: 2026-05-28
updated: 2026-05-28
last_verified: 2026-05-28
verify_tool: WebFetch
---

# Frontend Slides — Zero-Dependency HTML Presentations

**ประเภท**: Claude Code skill (visual design generator)
**สถานะ**: integrated at `skills/ecosystem/frontend-slides/` — synced from upstream v2.1.0 (2026-05-26)
**License**: MIT (© Zara Zhang 2025)
**Upstream**: https://github.com/zarazhangrui/frontend-slides (⭐19.4k / 🍴1.6k)

## ภาพรวม

Skill สร้าง presentation HTML แบบ zero-dependency (no npm, no build tools) ที่รันใน browser เปล่าได้เลย — เน้น **fixed 16:9 stage (1920×1080)** scaled-uniform-to-viewport (letterbox/pillarbox แทน reflow) + visual exploration workflow ("show, don't tell") ช่วยให้ user ที่ไม่ใช่ designer เลือกสไตล์จาก preview จริง ไม่ใช่จากคำถามแบบนามธรรม

## คุณสมบัติหลัก

| Component | Count | Role |
|---|---:|---|
| **Core docs** | 4 | SKILL.md, STYLE_PRESETS.md, animation-patterns.md, html-template.md |
| **Base CSS** | 1 | viewport-base.css — mandatory fixed-stage scaling |
| **Bold templates** | 34 | bold-template-pack/ — preview.md + design.md per template |
| **Web component** | 1 | deck-stage.js — keyboard/wheel/touch nav, scale, print-to-PDF |
| **Scripts** | 2 | extract-pptx.py (python-pptx), export-pdf.sh (Playwright) |
| **Selection index** | 1 | selection-index.json — progressive disclosure metadata |

**Curated style presets** (จาก STYLE_PRESETS.md): Bold Signal, Electric Studio, Neon Cyber, Terminal Green + 30 bold templates (8-Bit Orbit, Biennale Yellow, Editorial Forest, Emerald Editorial, ...)

## การใช้งานใน A-Wiki

- **Path**: `skills/ecosystem/frontend-slides/` (1.8MB, MIT-licensed copy)
- **Trigger**: เมื่อ user ขอ "สร้าง slides / deck / pitch / presentation / convert PPTX → web"
- **Refresh upstream**: sparse-clone จาก `https://github.com/zarazhangrui/frontend-slides`
  ```bash
  # ผ่าน ECC vendor (ECC อาจ lag — ไม่ใช่ source of truth สำหรับ skill นี้)
  bash scripts/refresh-ecosystem.sh
  # หรือ sync จาก upstream ตรง (recommended for this skill)
  cd /tmp && git clone --depth 1 --sparse https://github.com/zarazhangrui/frontend-slides
  ```
- **Scope ที่ A-Wiki รับ**:
  - ✅ 4 core docs + viewport-base.css
  - ✅ bold-template-pack/ (34 templates)
  - ✅ scripts/{extract-pptx.py, export-pdf.sh}
  - ✅ LICENSE
  - ❌ `scripts/deploy.sh` (Vercel) — ขัด offline-first policy
  - ❌ `plugins/` + `.claude-plugin/marketplace.json` — A-Wiki ใช้ skill route (เบากว่า plugin marketplace)

## Setup

ไม่ต้อง install อะไร — skill auto-loaded เมื่อ context match. Optional dependencies:
```bash
pip install python-pptx              # สำหรับ PPTX conversion
npm install -g @playwright/cli       # สำหรับ export-pdf.sh
```

Fonts โหลดจาก Google Fonts / Fontshare / jsdelivr CDN (เป็น runtime fetch ใน browser เท่านั้น — zero install)

## Security audit (2026-05-28)

- ✅ ไม่พบ `eval()`, `Function()`, `XMLHttpRequest`, `document.write`, `atob/btoa`, network exfil
- ✅ `innerHTML` 1 จุดใน `deck-stage.js:365` — เป็น controlled template literal (author-supplied UI overlay) — ไม่เป็น XSS sink
- ✅ Outbound URL ทั้งหมดเป็น **Google Fonts / Fontshare / jsdelivr Chinese fonts CDN** เท่านั้น (zero data exfil)
- ✅ Python `extract-pptx.py` ใช้ stdlib + `python-pptx` library (well-maintained, no shell exec)
- ⚠️ `export-pdf.sh` spawn `node` subprocess + run local Playwright server — ปลอดภัยใน trusted env
- ✅ MIT license — commercial use + modification + distribution อนุญาตเต็มที่
- Iron Laws ของ A-Wiki: ไม่ละเมิด — skill เป็น output generator, ไม่กระทบ raw/, CLAUDE.md, secrets

## ข้อดี / ข้อเสีย

| ข้อดี | ข้อเสีย |
|---|---|
| Zero npm dependencies — portable, audit-friendly | ผูกกับ font CDN (Google/Fontshare) — offline ใช้ไม่ได้เต็ม |
| 34 ready-to-use bold templates + 12 light presets | bold-template-pack 1.8MB เพิ่ม repo size |
| Fixed 1920×1080 stage — predictable, print/PDF clean | "no responsive reflow" ขัด mobile-first บางครั้ง |
| Web component (`<deck-stage>`) reusable | Web component อาจไม่ compat กับ React/Vue tooling บางตัว |
| MIT + active maintenance (last commit 2026-05-26) | Single maintainer (bus factor 1) |

## ความสัมพันธ์

- vendor ผ่าน: [[ecc]] — ECC vendor มาเป็น snapshot เก่า (v ก่อน 2.1.0) — A-Wiki sync จาก upstream ตรง
- ใช้ร่วมกับ: [[liquid-glass-design]] — Apple glass aesthetic สำหรับ slides ที่ต้องการ depth effect
- ใช้ร่วมกับ: [[motion-patterns]] — animation/interaction reference
- เกี่ยวข้องกับ: [[ui-to-vue]], [[frontend-design-direction]] — frontend skill cluster
- เกี่ยวข้องกับ: [[remotion-video-creation]] — video output alternative

## แหล่งข้อมูล

- GitHub: https://github.com/zarazhangrui/frontend-slides
- Author: Zara Zhang (@zarazhangrui)
- License: MIT (LICENSE file copied to skill dir)
- Upstream snapshot date: 2026-05-26 (commit `24e420e` "Bump plugin version to 2.1.0")
- [verified 2026-05-28] WebFetch + git sparse-clone + security scan
