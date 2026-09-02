#!/usr/bin/env python3
"""awiki guide — quick interactive pointers (Slice F).

  awiki guide            สรุป 30 วินาที + ไปต่อที่ไหน
  awiki guide install    วิธีติดตั้ง (clone / pip)
  awiki guide daily      งานประจำวัน (/A + ปุ่มเฉพาะ)
  awiki guide skills     ระบบทักษะอัตโนมัติ (pipeline)
  awiki guide adopt      ฝังสมองเข้าโปรเจ็คอื่น
  awiki guide troubleshoot
"""
import sys

def _configure_utf8_stdio() -> None:
    """Pin CLI byte streams to UTF-8 without mutating host stdio on import."""
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError, ValueError):
            pass


GUIDE = {
    "": """
🧠 A-Wiki ใน 30 วินาที
  เริ่มงาน:      /A <objective>        (ทางเข้าเดียว — สมองเดิน spine เอง)
  ถามสมอง:      awiki search "คำถาม"   · awiki status
  งานเฉพาะตัว:  /A-Doc · /A-Med-Order · /A-Rabies-Report (+9 ปุ่ม)
  สุขภาพสมอง:  awiki doctor
  คู่มือเต็ม:    docs/getting-started.md (TH) / getting-started-en.md (EN)
หัวข้อละเอียด: install · daily · skills · adopt · troubleshoot
""",
    "install": """
ติดตั้ง
  ทางที่ 1 (เต็มระบบ): git clone https://github.com/aase7en/A-Wiki.git
                        cd A-Wiki && bash scripts/setup-local.sh
  ทางที่ 2 (CLI เท่านั้น): pip install git+https://github.com/aase7en/A-Wiki.git
                        awiki status   (ต้องอยู่ใน clone หรือตั้ง AWIKI_ROOT)
""",
    "daily": """
งานประจำวัน
  เริ่ม:      /A <objective> — route อัตโนมัติ (trigger→description→spine)
  ระหว่างทาง: ตอบคำถาม grill (≥3 ข้อ) — ตอบสั้นได้
  จบ task:    review-bus ต้อง READY ก่อน (commit ใหม่ = รีวิวใหม่เสมอ)
  ค้น/จำ:     awiki search · awiki recall — ความจำจดอัตโนมัติทุก session
""",
    "skills": """
ระบบทักษะอัตโนมัติ (ไม่จำกัด)
  แหล่ง: wiki ที่ promote · ค้นเจอภายนอก · pattern ที่พบซ้ำ
  คิว:   awiki skill list        (draft → ready → approved)
  ประเมิน: awiki skill eval <id>  (suite อัตโนมัติ ไม่ใช้ LLM)
  อนุมัติ: awiki skill approve <id> — ปุ่มเดียว คุณคือ Senior Critic
  หาเพิ่ม: awiki skill scout "<gap>"  (ค้น GitHub ตามช่องว่าง)
""",
    "adopt": """
ฝังสมองเข้าโปรเจ็คอื่น
  awiki adopt <path/to/repo>
  ได้อะไร: hooks gates 3 ค่าย (Claude/ZCode/Codex) · MCP ชี้กลับสมอง
           · BRAIN-ENTRY · COLLAB · claims แยกต่อ repo — idempotent
  ตรวจสุขภาพ: awiki adopt <repo> --check
""",
    "troubleshoot": """
เจอปัญหา?
  1) awiki doctor --full          (registry/hooks/mcp/specs/CI)
  2) awiki search "<อาการ>"        (สมองเคยเจออะไรมาแล้ว)
  3) .tmp/review-bus/*.json       (งานค้างรีวิว: blockers = สิ่งที่ต้องแก้)
  4) docs/getting-started.md §8
""",
}


def main(argv=None) -> int:
    _configure_utf8_stdio()
    topic = (argv or sys.argv[1:])[0] if (argv or sys.argv[1:]) else ""
    print(GUIDE.get(topic, GUIDE[""]))
    if topic not in GUIDE:
        print(f"(ไม่รู้จักหัวข้อ {topic!r} — ดูรายการด้านบน)")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
