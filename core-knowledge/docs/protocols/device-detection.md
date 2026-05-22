# Device Detection Protocol

> **วัตถุประสงค์**: ทุก session ที่เปิด wiki นี้ (Claude Code, Codex, หรือ CLI อื่นๆ)
> จะรู้ทันทีว่ากำลังทำงานอยู่บน device ไหน และเห็น history ข้ามเซสชันได้

---

## One-time Setup Per Device

### Work PC (hospital Linux)

```bash
echo "work-pc" > ~/.wiki-device
```

### Home Mac (MacBook M1)

```bash
echo "home-mac" > ~/.wiki-device
```

### iPhone (via claude.ai/code)

ไม่ต้องทำอะไร — hook auto-detect ว่าเป็น ephemeral container

---

## Detection Logic

| Priority | Condition | Device |
|----------|-----------|--------|
| 1 | `~/.wiki-device` exists | ใช้ค่าในไฟล์ (highest accuracy) |
| 2 | `uname -s` = Darwin | `home-mac` |
| 3 | Linux + container signals* | `web-mobile` |
| 4 | Linux + no container | `work-pc` |

*Container signals (any one triggers `web-mobile`):
- `$CLAUDE_CODE_SESSION_ID` env var is set
- hostname matches `^[0-9a-f]{12,}$` (random hash)
- `/proc/1/cgroup` contains `docker`, `kubepods`, `lxc`, or `containerd`

---

## What Gets Written

`wiki/context/device-session.md` — git-tracked, updated every SessionStart.

เนื่องจาก `session-start-git-pull.sh` รันก่อน → ได้ history ล่าสุดจากทุก device
แล้วค่อย detect + prepend row ใหม่ → rolling 10-session history

ตัวอย่าง output:
```
📱 Device: web-mobile (Linux x86_64, hostname: a3f2b1c9d4e5, detect: auto:container-linux)
```

---

## Hook Location

- Claude Code: `.claude/hooks/session-start-device.sh`
- Codex CLI: `.codex/hooks/session-start-device.sh`

Hook เพิ่มใน `SessionStart` (ลำดับที่ 3 หลัง git-pull และ wiki-context-check)

---

## Verification

```bash
# Test บน Mac (มี ~/.wiki-device = "home-mac"):
bash .claude/hooks/session-start-device.sh
# → 💻 Device: home-mac (Darwin arm64, hostname: ..., detect: ~/.wiki-device)

# Test fallback (ไม่มี ~/.wiki-device บน Mac):
mv ~/.wiki-device ~/.wiki-device.bak
bash .claude/hooks/session-start-device.sh
# → 💻 Device: home-mac (Darwin arm64, ..., detect: auto:Darwin)
mv ~/.wiki-device.bak ~/.wiki-device

# ดู output file:
cat wiki/context/device-session.md
```
