#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
med_order_telegram.py — เลนสั่งยาแบบ "ไม่ใช้ browser" สำหรับ Pi5 / Hermes / ZCode / โมเดล free-tier

ทำไมต้องมีเลนนี้
  เลนปกติของ /A-Med-Order ต้องเปิด Google Sheet ผ่านเบราว์เซอร์ ซึ่ง Pi5 ทำไม่ได้
  เลนนี้ตัด Sheet ออกทั้งหมด → คุยผ่าน Telegram อย่างเดียว จบใน 3 ข้อความ

  1. draft   : ลิสต์ยาหมด → resolve (alias → สต๊อก → unknown) → ส่งรายการเลขกำกับกลับไปถามจำนวน
  2. qty     : ผู้ใช้ตอบ "1=12 2=5 ..." → อัปเดต session
  3. finish  : ออก .xlsx เก็บประวัติ + ข้อความ LINE พร้อม copy + เรียน alias ที่ยืนยันแล้ว

หลักการออกแบบ
  * สคริปต์นี้ **ไม่มี secret ไม่ต่อเน็ต ไม่เรียก LLM** — เป็น state machine ล้วน
    บอท Telegram (private, อยู่ใน drive/personal-tools) แค่ pipe ข้อความเข้า/ออก
  * งานที่ต้อง "ตัดสินใจ" มีจุดเดียวคือ ตั้งชื่อยาให้รายการ status=unknown
    → ให้ LLM ทำผ่านคำสั่ง `set` เท่านั้น ที่เหลือ deterministic ทั้งหมด
    โมเดลเล็กจึงพลาดได้น้อยลงมาก และยิ่งเรียน alias มาก ยิ่งไม่ต้องใช้ LLM เลย

Session : <drive>/pharmacy/order-sessions/<id>.json

Usage:
  python3 scripts/med_order_telegram.py draft  list.txt [--session s01]
  python3 scripts/med_order_telegram.py set    s01 7 --name "Nizoral ครีม" --strength "Ketoconazole 2%" --pack "10 g" --unit หลอด --category "3. ยาปฏิชีวนะ / ต้านเชื้อรา"
  python3 scripts/med_order_telegram.py qty    s01 "1=12 2=5 7=3"
  python3 scripts/med_order_telegram.py status s01
  python3 scripts/med_order_telegram.py finish s01 --po PO-2026-08-01
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from datetime import date, datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_order_sheet as bos  # noqa: E402

try:
    import pharmacy_aliases as aliases  # type: ignore  # noqa: E402
except Exception:                       # pragma: no cover
    aliases = None


def _pharmacy_dir(create: bool = True) -> pathlib.Path:
    try:
        from drive_path import get_pharmacy_dir  # type: ignore
        return get_pharmacy_dir(create=create)
    except Exception:
        p = ROOT / "drive" / "pharmacy"
        if create:
            p.mkdir(parents=True, exist_ok=True)
        return p


def _sessions_dir(create: bool = True) -> pathlib.Path:
    d = _pharmacy_dir(create) / "order-sessions"
    if create:
        d.mkdir(parents=True, exist_ok=True)
    return d


def _session_path(sid: str) -> pathlib.Path:
    return _sessions_dir() / f"{sid}.json"


def _load(sid: str) -> dict:
    p = _session_path(sid)
    if not p.exists():
        raise SystemExit(f"❌ ไม่พบ session '{sid}' — ดูรายการด้วย `list`")
    return json.loads(p.read_text(encoding="utf-8"))


def _save(s: dict) -> pathlib.Path:
    p = _session_path(s["id"])
    s["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    p.write_text(json.dumps(s, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return p


# ---------------------------------------------------------------- formatting

STATUS_ICON = {"alias": "✅", "stock": "🟡", "unknown": "❓", "manual": "✍️"}


def render_ask(s: dict) -> str:
    """ข้อความถามจำนวน — สั้นพอสำหรับ Telegram หนึ่งข้อความ"""
    out = [f"🧾 ใบสั่งยา #{s['id']} — {len(s['items'])} รายการ",
           "ตอบจำนวนแบบ  1=12 2=5 7=3   (ข้ามได้ ไม่ตอบ = ไม่สั่ง)", ""]
    unknown = []
    for i, it in enumerate(s["items"], start=1):
        icon = STATUS_ICON.get(it["status"], "•")
        if it["status"] == "unknown":
            unknown.append(i)
            out.append(f"{i}. {icon} {it['raw']}  ← ยังไม่รู้จัก")
            continue
        bits = [it["name"]]
        if it.get("strength"):
            bits.append(it["strength"])
        if it.get("pack"):
            bits.append(it["pack"])
        qty = it.get("qty")
        tail = f"= {qty} {it.get('unit','')}".strip() if qty else f"= ___ {it.get('unit','')}".strip()
        out.append(f"{i}. {icon} {' '.join(bits)} {tail}")
    out.append("")
    out.append(f"✅ จากคำพ้องที่ยืนยันแล้ว {s['summary'].get('alias',0)} · "
               f"🟡 เดาจากสต๊อก {s['summary'].get('stock',0)} · "
               f"❓ ยังไม่รู้จัก {s['summary'].get('unknown',0)}")
    if unknown:
        out.append(f"⚠️ ข้อ {', '.join(map(str,unknown))} ต้องยืนยันชื่อก่อนถึงจะสั่งได้")
    return "\n".join(out)


# ---------------------------------------------------------------- qty parsing

_PAIR = re.compile(r"(\d{1,3})\s*(?:=|:|->|→|\s)\s*(\d{1,4})")


def parse_qty_reply(reply: str, n_items: int) -> tuple[dict[int, int], list[str]]:
    """
    รองรับ: '1=12 2=5' · '1:12, 2:5' · บรรทัดละ '1 12' · 'all 12' · 'ทั้งหมด 12'
    คืน ({index1based: qty}, [คำเตือน])
    """
    warn: list[str] = []
    reply = (reply or "").strip()
    if not reply:
        return {}, ["ข้อความว่าง"]

    m_all = re.match(r"^(?:all|ทั้งหมด|ทุกตัว)\s+(\d{1,4})$", reply, flags=re.IGNORECASE)
    if m_all:
        q = int(m_all.group(1))
        return {i: q for i in range(1, n_items + 1)}, []

    out: dict[int, int] = {}
    for idx, qty in _PAIR.findall(reply):
        i, q = int(idx), int(qty)
        if not 1 <= i <= n_items:
            warn.append(f"ข้อ {i} ไม่มีในรายการ (มี 1-{n_items})")
            continue
        if i in out and out[i] != q:
            warn.append(f"ข้อ {i} ระบุซ้ำ {out[i]} → {q} ใช้ค่าหลัง")
        out[i] = q

    if not out:
        warn.append("อ่านไม่ออก — ใช้รูปแบบ 1=12 2=5")
    return out, warn


# ---------------------------------------------------------------- commands


def cmd_draft(a) -> int:
    text = sys.stdin.read() if a.file == "-" else pathlib.Path(a.file).read_text(encoding="utf-8")
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    if not lines:
        raise SystemExit("❌ ลิสต์ว่าง")

    res = bos.resolve_lines(lines)
    sid = a.session or f"{date.today():%Y%m%d}-{len(list(_sessions_dir().glob('*.json'))) + 1:02d}"
    items = []
    for it in res["items"]:
        it["qty"] = None
        items.append(it)

    s = {"id": sid, "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
         "po": a.po or f"PO-{date.today():%Y-%m}-01", "date": f"{date.today():%d/%m/%Y}",
         "state": "await_qty", "summary": res["summary"], "items": items}
    _save(s)
    print(render_ask(s))
    print(f"\n[session: {sid}]", file=sys.stderr)
    return 0


def cmd_set(a) -> int:
    s = _load(a.session)
    i = a.index
    if not 1 <= i <= len(s["items"]):
        raise SystemExit(f"❌ ข้อ {i} ไม่มี (มี 1-{len(s['items'])})")
    it = s["items"][i - 1]
    for f in ("name", "strength", "pack", "unit", "category", "note"):
        v = getattr(a, f)
        if v is not None:
            it[f] = v
    if it.get("name"):
        it["status"] = "manual"
        if it.get("cost") is None:
            c = bos.lookup_cost(it["name"])
            if c and c.get("cost"):
                it["cost"] = round(float(c["cost"]), 2)
                it["unit"] = it.get("unit") or (c.get("unit") or "")
    s["summary"] = _recount(s)
    _save(s)
    print(f"✓ ข้อ {i} → {it.get('name')} | {it.get('strength','')} | {it.get('pack','')}")
    return 0


def _recount(s: dict) -> dict:
    c: dict[str, int] = {}
    for it in s["items"]:
        c[it["status"]] = c.get(it["status"], 0) + 1
    return c


def cmd_qty(a) -> int:
    s = _load(a.session)
    mapping, warn = parse_qty_reply(a.reply, len(s["items"]))
    for i, q in mapping.items():
        s["items"][i - 1]["qty"] = q
    s["state"] = "qty_set"
    _save(s)
    for w in warn:
        print(f"⚠️ {w}")
    filled = sum(1 for it in s["items"] if it.get("qty"))
    print(f"✓ กรอกจำนวนแล้ว {filled}/{len(s['items'])} รายการ\n")
    print(render_ask(s))
    return 0


def cmd_status(a) -> int:
    s = _load(a.session)
    print(render_ask(s))
    return 0


def cmd_list(a) -> int:
    d = _sessions_dir(create=False)
    if not d.exists():
        print("ยังไม่มี session")
        return 0
    for p in sorted(d.glob("*.json"), reverse=True)[: a.limit]:
        s = json.loads(p.read_text(encoding="utf-8"))
        n = len(s["items"])
        filled = sum(1 for it in s["items"] if it.get("qty"))
        print(f"{s['id']:>14}  {s.get('state','?'):10s}  {filled}/{n} กรอกแล้ว  {s.get('created','')}")
    return 0


def cmd_finish(a) -> int:
    s = _load(a.session)
    ordered = [it for it in s["items"] if it.get("qty")]
    if not ordered:
        raise SystemExit("❌ ยังไม่มีรายการที่ระบุจำนวน — ใช้ `qty` ก่อน")

    blocked = [i + 1 for i, it in enumerate(s["items"])
               if it.get("qty") and it["status"] == "unknown"]
    if blocked and not a.force:
        raise SystemExit(f"❌ ข้อ {blocked} ยังไม่รู้จักชื่อยา — ใช้ `set` ยืนยันก่อน "
                         f"(หรือ --force ถ้าจะสั่งด้วยชื่อดิบ)")

    # เรียงตามหมวด แล้วค่อยตามลำดับเดิม เพื่อให้ xlsx/LINE จัดกลุ่มถูก
    ordered.sort(key=lambda it: (it.get("category") or "zz", s["items"].index(it)))

    po = a.po or s.get("po")
    out = pathlib.Path(a.out) if a.out else (
        _pharmacy_dir() / "order-history" / f"{po}_{s['id']}.xlsx")
    info = bos.build(ordered, out, po, s.get("date", f"{date.today():%d/%m/%Y}"), a.buyer)

    learned = None
    if aliases is not None and not a.no_learn:
        learned = aliases.learn_many(
            [{**it, "raw": it.get("raw", "")} for it in ordered if it["status"] in ("manual", "alias")],
            source=f"telegram:{s['id']}")

    s["state"] = "done"
    s["output"] = str(out)
    _save(s)

    print(bos.to_line(out, skip_zero=True))
    print("", file=sys.stderr)
    print(json.dumps({"xlsx": str(out), "items": info["items"],
                      "cost_filled": info["cost_filled"], "learned": learned},
                     ensure_ascii=False), file=sys.stderr)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("draft", help="ลิสต์ยาหมด → session + ข้อความถามจำนวน")
    d.add_argument("file", nargs="?", default="-")
    d.add_argument("--session")
    d.add_argument("--po")
    d.set_defaults(fn=cmd_draft)

    st = sub.add_parser("set", help="ยืนยันชื่อยาให้รายการที่ยังไม่รู้จัก (จุดเดียวที่ต้องใช้ LLM/คน)")
    st.add_argument("session")
    st.add_argument("index", type=int)
    for f in ("name", "strength", "pack", "unit", "category", "note"):
        st.add_argument(f"--{f}")
    st.set_defaults(fn=cmd_set)

    q = sub.add_parser("qty", help="อัปเดตจำนวนจากข้อความตอบกลับ")
    q.add_argument("session")
    q.add_argument("reply")
    q.set_defaults(fn=cmd_qty)

    s_ = sub.add_parser("status", help="ดูสถานะ session")
    s_.add_argument("session")
    s_.set_defaults(fn=cmd_status)

    ls = sub.add_parser("list", help="ดู session ล่าสุด")
    ls.add_argument("--limit", type=int, default=10)
    ls.set_defaults(fn=cmd_list)

    f = sub.add_parser("finish", help="ออก xlsx + ข้อความ LINE + เรียน alias")
    f.add_argument("session")
    f.add_argument("--po")
    f.add_argument("--out")
    f.add_argument("--buyer", default="ศุภศิษฎิ์ คงสุวรรณ")
    f.add_argument("--force", action="store_true", help="สั่งทั้งที่ยังมีรายการ unknown")
    f.add_argument("--no-learn", action="store_true")
    f.set_defaults(fn=cmd_finish)

    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
