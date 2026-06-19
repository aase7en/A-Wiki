# Plan — Auto-Start Live Dashboard ในทุก Kilo Session

## ปัญหา
ทุกครั้งที่เปิด Kilo session ใหม่ Browser A-Wiki Live ไม่แสดงอัตโนมัติ เพราะ:
1. **Kilo ไม่มี hooks system** — Claude Code มี `SessionStart` hook ที่เรียก `session_start.py` → `_ensure_dashboard()` แต่ Kilo ทำไม่ได้
2. **ไม่มี `.vscode/tasks.json`** — ไม่มี VS Code task ที่ `runOn: folderOpen` เพื่อ start dashboard ตอนเปิด workspace

## สถานะปัจจุบัน
- `server.py` syntax OK (merge conflicts resolved แล้ว)
- `dashboard-ensure.sh` พร้อมใช้ (idempotent, PID-guarded, auto-opens browser)
- `.kilo/command/awiki-dashboard.md` มีแล้ว แต่ต้อง manual invoke
- **ยังไม่มี** `.vscode/` directory เลย

## วิธีแก้ — สร้าง `.vscode/tasks.json` (Phase 2b จากแผนใหญ่)

### ไฟล์ที่จะสร้าง

**`.vscode/tasks.json`** — VS Code task ที่ auto-run ตอนเปิด folder:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "A-Wiki: Live Dashboard (auto)",
      "type": "shell",
      "command": "bash scripts/dashboard-ensure.sh",
      "runOn": "folderOpen",
      "presentation": {
        "reveal": "silent",
        "panel": "shared",
        "close": true
      },
      "problemMatcher": []
    }
  ]
}
```

### ทำงานอย่างไร
1. VS Code เปิด workspace → trigger task `folderOpen`
2. `dashboard-ensure.sh` ทำงาน (idempotent — skip ถ้า running อยู่แล้ว)
3. `server.py --daemonize` start server บน port 7790
4. `server.py` เรียก `webbrowser.open("http://localhost:7790")` เปิด browser อัตโนมัติ (ครั้งแรกเท่านั้น)
5. Kilo session ใหม่อื่นๆ ใน VS Code เดียวกัน → dashboard already running → no-op

### ผลลัพธ์
- ทุกครั้งที่เปิด VS Code + Kilo → Dashboard เปิดอัตโนมัติใน browser
- เห็น real-time: model routing, subagent delegation, parallel lanes, cost-first pyramid
- ใช้ได้ทั้ง Kilo และ Cline (ทั้งคู่รันใน VS Code)
- ไม่กระทบ Claude Code / Codex / Gemini CLI (มี hook ของตัวเองอยู่แล้ว)

## ขอบเขต
- สร้าง `.vscode/tasks.json` 1 ไฟล์ — เสร็จใน step เดียว
- VS Code จะถาม "Allow folder-open tasks?" ครั้งแรก → กด Allow
- ไม่แก้ AGENTS.md, CLAUDE.md, หรือไฟล์อื่น
