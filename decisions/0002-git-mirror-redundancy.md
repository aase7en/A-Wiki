---
adr: 0002
title: Git mirror หลาย host (GitHub + GitLab + Codeberg) เพื่อ redundancy
status: Accepted
date: 2026-04-30
tags: [git, infrastructure, backup, redundancy, digital-legacy]
related_journal: [journal/2026/2026-04-30]
supersedes: []
superseded_by: []
---

# ADR-0002: Git mirror หลาย host (GitHub + GitLab + Codeberg)

## Status
**Accepted** (2026-04-30)

## Context

Wiki + journal + decisions = digital DNA ของเรา (ดู [[decisions/0001-digital-legacy-strategy]])
ปัจจุบันเก็บไว้ที่ GitHub เพียงเจ้าเดียว → single point of failure

**ความเสี่ยง:**
- Microsoft (เจ้าของ GitHub) เปลี่ยน policy/ปิดบัญชี
- การเมือง / sanctions / ban region
- Account compromise
- ค่าธรรมเนียมเพิ่ม (อนาคตอาจ paid-only)

**ข้อจำกัด:**
- งบ: ฟรี
- เวลา setup: <30 นาที
- Maintenance: ต้อง push หลายครั้งหรือตั้ง auto

---

## Decision

ใช้ **single git remote with multiple URLs** — push command เดียวอัปเดตทุกที่

```bash
# Setup (ครั้งเดียว)
git remote set-url --add --push origin git@github.com:<owner>/<repo>.git
git remote set-url --add --push origin git@gitlab.com:<owner>/<repo>.git
git remote set-url --add --push origin git@codeberg.org:<owner>/<repo>.git

# ใช้งานปกติ
git push origin main   # → push ขึ้นทั้ง 3 host
```

**Hosts ที่เลือก:**
1. **GitHub** (primary) — เครือข่าย dev ใหญ่สุด, integration ดี
2. **GitLab.com** (mirror) — บริษัทแยก, อยู่ Netherlands → diverse jurisdiction
3. **Codeberg.org** (mirror) — non-profit (Codeberg e.V., Germany), focused on FOSS — รอดยาวที่สุดถ้า ecosystem ล่ม

---

## Alternatives Considered

### Option A: ใช้ GitHub อย่างเดียว
- Pros: ง่ายสุด ไม่ต้องดูแลเพิ่ม
- Cons: SPOF — ถ้า GitHub มีปัญหา = หาย
- ทำไมไม่เลือก: ขัดเป้า legacy

### Option B: Self-hosted Gitea/Forgejo บน Pi5
- Pros: เป็นเจ้าของจริง 100%
- Cons:
  - Pi5 ตาย → ข้อมูลหาย (ถ้าไม่มี backup อื่น)
  - ต้องดูแล server, security updates, SSL
  - ครอบครัวจะ maintain ไม่ไหวตอนเราไม่อยู่
- ทำไมไม่เลือก: complexity เกิน, แต่ **อาจเพิ่มเป็น tier 4** ในอนาคต

### Option C (chosen): Multi-host cloud git
- Pros:
  - Setup ครั้งเดียว
  - Push เดียวกระจายทุกที่
  - แต่ละเจ้าดูแล security ให้
  - ถ้าเจ้าหนึ่งล่ม → อีก 2 เจ้ายังอยู่
  - ฟรีทั้งหมด
- Cons:
  - ยังพึ่ง 3rd party
  - ต้องสมัคร 2 บัญชีเพิ่ม
- ทำไมเลือก: balance ระหว่าง redundancy กับ effort

### Option D: Multi-host + IPFS pinning
- Pros: Truly decentralized
- Cons: ความซับซ้อน, IPFS pinning service ก็มี cost
- ทำไมไม่เลือก: overkill ตอนนี้, revisit ภายหลังถ้าจะ public archive

---

## Consequences

### Positive
- 3-way redundancy — ต้องล่ม 3 เจ้าพร้อมกันถึงจะหายข้อมูล
- Push command เดียวเหมือนเดิม (ไม่ต้องเปลี่ยน workflow)
- Diverse jurisdiction (US + Netherlands + Germany)
- Codeberg เป็น non-profit → ไม่มีแรง commercial ให้ปิด

### Negative / Trade-offs
- ต้อง sync บัญชีทั้ง 3 เจ้า (settings, SSH keys)
- Push ช้าลง 3x (3 push parallel จริงๆ ก็เร็วอยู่)
- ถ้า GitHub-specific feature (Actions, Pages) ใช้แค่ GitHub
- Issues/PR แยกกันแต่ละเจ้า — ใช้ GitHub เป็นหลัก mirror อ่านได้อย่างเดียว

### Risks
- Push fail บาง host แล้วไม่รู้ตัว → ต้องตรวจ `git remote -v` เป็นครั้งคราว
- 2FA recovery codes ต้องเก็บแยก 3 ที่
- ถ้าเปลี่ยน private→public บางที่ accidentally → ข้อมูลส่วนตัวรั่ว

---

## Revisit Conditions

- 🔥 **ถ้าเจ้าใดเจ้าหนึ่งล่ม/มีปัญหา**: เพิ่ม mirror ที่ 4 (เช่น sourcehut, BitBucket, Gitea self-hosted)
- 🏠 **เมื่อตั้ง Mac Mini/NAS ที่บ้าน**: เพิ่ม self-hosted Gitea เป็น tier 4 (offline)
- 🌐 **ถ้าทำ public archive**: พิจารณา IPFS pin
- 👥 **เมื่อมี heir**: ส่ง credential 3 เจ้าให้ heir + วิธีตรวจสอบ

---

## Implementation

ดู `scripts/setup-git-mirror.sh` (รันครั้งเดียว setup ทั้ง 3 hosts)

---

## References

- [[journal/2026/2026-04-30]]
- [[decisions/0001-digital-legacy-strategy]]
- Codeberg: https://codeberg.org (non-profit, FOSS-focused)
- GitLab: https://about.gitlab.com/handbook/values/ (open core)
- Git docs: https://git-scm.com/docs/git-remote
