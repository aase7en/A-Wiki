# /A-Security — Evidence-led security audit

Maps to: `skills/awiki/a-security/SKILL.md` (adapted from Cloudflare's security-audit-skill, upstream pinned)

## When to use
- ตอบคำถาม security แบบ focused (auth, input validation, crypto, secrets)
- Full/comprehensive codebase security audit แบบ trust-boundary coverage
- ต้องการ machine-readable findings + independent verification ของ candidate vulnerabilities
- Source/local-only validation (bounded — ไม่ exploit production)

Auto-picks on: `security audit`, `vulnerability review`, `OWASP`, `secure code review`, `threat model`

## Flow
1. Scope + trust boundaries ก่อน (external input, authz, storage, network egress)
2. Recon → candidate findings พร้อม evidence (file:line)
3. Independent verification ต่อ candidate — ยืนยัน exploitability จริง ไม่เดา
4. Output: findings ระดับ severity + machine-readable ledger (`run-metadata.json` budget-aware)
5. Final clean pass ก่อนสรุป — นับ agent invocations ตาม budget ที่ตั้ง
