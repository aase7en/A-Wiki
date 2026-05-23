# Runbook: Setup Wiki บนเครื่องใหม่

> **วัตถุประสงค์**: ติดตั้ง InW-Wiki บนเครื่อง Mac/Windows ใหม่
> **Last updated**: 2026-05-17

---

## Prerequisites

- Git
- VS Code + Claude Code CLI (optional)

---

## ขั้นตอน

### 1. Clone repository

```bash
git clone https://github.com/aase7en/Aase7en-InW-Wiki.git
cd Aase7en-InW-Wiki
```

### 2. ติดตั้ง dotfiles (optional)

```bash
bash scripts/install-dotfiles.sh
```

### 3. ตั้งค่า Git mirror (optional)

```bash
bash scripts/setup-git-mirror.sh
```

### 4. ตั้งค่า Edit Protection (CLAUDE.md lock)

```bash
cp .claude/lock.example .claude/lock.txt
# แก้ .claude/lock.txt → ลบ comment ออก เหลือ password บรรทัดเดียว
chmod 600 .claude/lock.txt
```

### 5. ตรวจสอบ

```bash
git status
python3 scripts/gen-index.py   # regenerate wiki-overview.md
```

---

## Verification

```bash
# ตรวจว่า git metadata เป็น repo ปกติ
test -d .git && git status --short --branch
# ควรได้: ## main...origin/main
