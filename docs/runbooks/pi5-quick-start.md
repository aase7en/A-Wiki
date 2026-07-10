# Pi5 Quick-Start Card (SSH Host)

> **เก็บไว้ดูตอน SSH เข้า Pi5 แล้วลืมคำสั่ง.** ทุกคำสั่งรันบน **host** (`umbrel` user), ไม่ใช่ใน Hermes app UI.
>
> เหตุผล: Hermes รันใน Docker container (`/opt/data`), แต่ `git`, `cron`, `sudo docker` อยู่บน host. App Hermes UI มองไม่เห็นสิ่งเหล่านี้.

---

## เข้ายังไง

```bash
# จากเครื่องคุณ (ต้องลง Tailscale และเชื่อมต่อ Pi5 แล้ว):
ssh umbrel@umbrel-1.tail<id>.ts.net
# ใส่รหัสผ่าน umbrel
```

หรือผ่าน Umbrel Web UI → คลิก **Terminal** widget (เทียบเท่า SSH host shell)

เข้ามาแล้ว prompt จะเป็น `umbrel@umbrel:~ $`

---

## คำสั่งที่ใช้บ่อย (copy-paste ได้)

### ตรวจสถานะทั้งหมด
```bash
cd ~/A-Wiki
git log --oneline -3                          # ดูว่าอยู่ commit ล่าสุดไหม
sudo docker ps | grep hermes                  # container รันอยู่ไหม
crontab -l | grep auto-sync                   # cron 6h active ไหม
```

### Manual sync (ไม่รอ cron 6h)
```bash
cd ~/A-Wiki
bash scripts/hermes/awiki-pi5-sync.sh
# จะถามรหัสผ่าน sudo (สำหรับ docker exec) — ใส่รหัสผ่าน umbrel
# = host git pull + FF clone ใน container + gateway rescan + verify
```

### ถ้า skills ยังหายหลัง sync
```bash
# 1. Restart container (บังคับ rescan ทั้งหมด)
sudo docker restart hermes-agent_web_1

# 2. ตรวจ logs
sudo docker logs --tail 50 hermes-agent_web_1

# 3. นับ skills ใน container
sudo docker exec hermes-agent_web_1 bash -c 'ls /opt/data/skills/ | wc -l'
```

### ตั้ง/แก้ cron (ถ้าหาย)
```bash
crontab -e
# เพิ่มบรรทัดนี้ (sync ทุก 6 ชั่วโมง):
0 */6 * * * cd ~/A-Wiki && bash scripts/hermes/auto-sync-from-git.sh
```

---

## ⚠️ ห้ามทำบน Pi5

```bash
# ห้ามรันสิ่งนี้บน Pi5 — มันสร้าง host symlinks ที่ container มองไม่เห็น:
bash scripts/link-agent-configs.sh    # ❌ ห้าม
# ใช้สิ่งนี้แทน:
bash scripts/hermes/awiki-pi5-sync.sh # ✅ ถูกต้อง
```

---

## Architecture สั้น ๆ (ทำไมถึงเป็นแบบนี้)

```
host (umbrel@umbrel)           ← คุณอยู่ที่นี่เมื่อ SSH
├── ~/A-Wiki/                  ← git clone (GitHub = source of truth)
│   └── scripts/hermes/
│       ├── auto-sync-from-git.sh   ← cron 6h เรียกสคริปต์นี้
│       ├── pi5-brain-sync.py       ← ตัว FF clone ใน container (dry-run ได้)
│       └── awiki-pi5-sync.sh       ← manual sync สคริปต์นี้
│
└── Docker: hermes-agent_web_1 ← Hermes รันอยู่ข้างในนี้
    ├── /opt/data/A-Wiki/      ← canonical clone (สมองที่ Hermes ใช้จริง — config cwd ชี้ที่นี่)
    ├── /opt/data/skills/      ← symlinks → canonical clone
    └── (sudo docker exec เพื่อเข้าถึง)
```

**Flow (rewritten 2026-07-10):** host `git pull` → `docker exec` เข้า container → `git fetch` + FF `/opt/data/A-Wiki` (stash/pop กัน device-only files, auto-gen conflict คืนจาก HEAD) → SIGHUP gateway → skills เนื้อหาใหม่ถูกโหลด
> flow เก่า (docker cp tarball + profile import) ตายโดยดีไซน์ — `.gitignore` กัน `*.tar.gz` ทำให้ package ไม่เคยมาถึงผ่าน git; tarball ยังใช้เฉพาะ provisioning ครั้งแรก (ดู IMPORT-NOTES.md)

### One-time setup สำหรับ cron (จำเป็น — sudo บน Pi5 ต้องใส่รหัสผ่าน)

```bash
# cron ไม่มี stdin ให้พิมพ์รหัสผ่าน → ต้องอนุญาต docker exec แบบ NOPASSWD ครั้งเดียว:
echo 'umbrel ALL=(root) NOPASSWD: /usr/bin/docker exec *' | sudo tee /etc/sudoers.d/awiki-hermes-sync
# ยังไม่ตั้ง = cron จะ fail เร็วพร้อม error ชัดเจน (ไม่ hang) — manual sync ใช้ได้ปกติ
```

---

## ติดต่อข้ามเครื่อง

| อยาก... | ทำบนเครื่องไหน |
|---|---|
| แก้ skill แล้วให้ Pi5 เห็น | Windows/Mac: แก้ → `git push` → Pi5 auto-pull ใน 6h (หรือ SSH เข้า Pi5 รัน `awiki-pi5-sync.sh`) |
| ดู Hermes chat | App Hermes UI บนเบราว์เซอร์ (`http://umbrel.local` หรือ Tailscale URL) |
| ตรวจ sync logs | SSH host: `sudo docker logs hermes-agent_web_1` |
| แก้ cron | SSH host: `crontab -e` |

---

## เกี่ยวกับรหัสผ่าน sudo

`umbrel` user **ไม่ได้อยู่ใน `docker` group** → ทุกคำสั่ง `docker` ต้อง `sudo` (มีรหัสผ่าน = รหัสผ่าน `umbrel` เดียวกับ SSH login)

สคริปต์ `awiki-pi5-sync.sh` ใช้ `sudo -S -p ''` (อ่าน password จาก stdin) แต่ตอนรัน manual ใน terminal จะถามตรง ๆ — แค่ใส่รหัสผ่าน `umbrel` ตอนถูกถาม

---

## เห็น "Already up to date" หลัง git pull บน Pi5?

แปลว่า Pi5 มี commit ล่าสุดแล้ว — ปกติถ้า cron ทำงานปกติจะเป็นแบบนี้เสมอ. ถ้า skills ยังหายอยู่แม้ pull แล้ว ปัญหาอยู่ที่ import/rescan ไม่ใช่ git — รัน `awiki-pi5-sync.sh` (มัน force gateway rescan) หรือ `sudo docker restart hermes-agent_web_1`
