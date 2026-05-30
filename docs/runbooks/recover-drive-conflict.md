# Runbook: กู้คืนเมื่อ Drive Sync พัง

> **วัตถุประสงค์**: เมื่อ Google Drive sync ทำให้ `.git/` เสียหาย หรือเกิด `.git (1)/` conflict
> **Last updated**: 2026-05-17

> **Legacy only**: Wiki หลักปัจจุบันควรเป็น Git working copy ปกติ และไม่ควรวาง `.git/` ไว้ใน Google Drive sync. ใช้ runbook นี้เฉพาะกรณีกู้ repo เก่าที่เคยอยู่ใน Google Drive เท่านั้น.

---

## อาการ

- `git status` error: `fatal: not a git repository`
- มีโฟลเดอร์ `.git (1)/` หรือ `.git (2)/` ใน repo
- Drive sync error: "Can't sync .git"

---

## ขั้นตอนกู้คืน

### 1. หยุด Drive sync ทันที

- คลิก Drive icon → Pause
- หรือปิด Drive app ชั่วคราว

### 2. ตรวจสอบสภาพ .git

```bash
ls -la .git*
# ถ้าเห็น .git (1)/ หรือ .git (2)/ → มี conflict
```

### 3. ลบ .git ที่เสียหาย

```bash
# backup ก่อน
cp -r .git .git_BACKUP

# ลบเฉพาะ .git ที่เสีย (ไม่ใช่ของจริง)
rm -rf ".git (1)" ".git (2)"
```

### 4. รัน Drive redirect script

```bash
bash scripts/setup-drive-redirect.sh
```

### 5. ตรวจสอบ

```bash
git status
git log --oneline -3
```

### 6. ลบ .git_BACKUP (เมื่อมั่นใจว่าทุกอย่างปกติ)

```bash
rm -rf .git_BACKUP
```

### 7. Resume Drive sync

- Drive icon → Resume

---

## Prevention

- อย่า sync โฟลเดอร์ Wiki หลักผ่าน Google Drive
- ใช้ GitHub เป็น sync หลัก: `git pull` / `git push origin main`
- ตรวจสอบ repo ปกติด้วย `test -d .git && git status --short --branch`
