#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pharmacy_aliases.py — คลังคำพ้อง "ชื่อที่พิมพ์มั่ว → รายการยาที่ยืนยันแล้ว"

ทำไมต้องมี
  ขั้นที่เสี่ยงที่สุดของ /A-Med-Order คือ "เดาว่า ยาคมแอนนา = Anna" ซึ่งต้องใช้ LLM ตัดสิน
  โมเดล free-tier บน Pi5 จะพลาดขั้นนี้บ่อยกว่า flagship มาก
  → ทุกครั้งที่เจ้าของร้าน "ยืนยัน" ชื่อ ให้จำไว้ รอบหน้าเจอสตริงเดิม = exact hit ไม่ต้องเดาอีก
  → สั่งซ้ำไม่กี่รอบ ลิสต์ส่วนใหญ่จะ resolve ได้โดยไม่ใช้ LLM เลย โมเดลเล็กกับใหญ่จึงให้ผลเท่ากัน

ที่เก็บ : <drive>/pharmacy/order-aliases.json   (ข้อมูลธุรกิจจริง → drive เท่านั้น, Iron Law #6)
คีย์    : token set แบบ normalize แล้ว เรียงตัวอักษร — ทนต่อการสลับคำ ตัวพิมพ์ใหญ่เล็ก
          วรรคตอน และหน่วยที่เขียนต่างกัน (15ml / 15 ML / 15 cc → คีย์เดียวกัน)

Usage:
    python3 scripts/pharmacy_aliases.py resolve "ยาคมมินนี่ 28" "betadine 15ml"
    python3 scripts/pharmacy_aliases.py learn --file confirmed_items.json
    python3 scripts/pharmacy_aliases.py stats
    python3 scripts/pharmacy_aliases.py list --grep คุม
    python3 scripts/pharmacy_aliases.py forget "ยาคมมินนี่ 28"
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

SCHEMA_VERSION = 1
FILENAME = "order-aliases.json"

# หน่วยที่เขียนได้หลายแบบ — ยุบให้เหลือรูปเดียวก่อนทำคีย์
UNIT_ALIAS = {
    "cc": "ml", "ซีซี": "ml", "มล": "ml", "มิลลิลิตร": "ml",
    "gm": "g", "gram": "g", "grams": "g", "กรัม": "g",
    "mgs": "mg", "มก": "mg",
    "tab": "s", "tabs": "s", "cap": "s", "caps": "s",
    "เม็ด": "s", "แคปซูล": "s",
    "mcg": "mcg", "microgram": "mcg", "micrograms": "mcg",
}


def tokens(text: str) -> list[str]:
    """แตกคำ → แยกตัวเลขออกจากหน่วย → ยุบหน่วยพ้องรูป. '15ml' และ '15 CC' ให้ผลเท่ากัน."""
    out: list[str] = []
    for chunk in re.split(r"[^0-9A-Za-z฀-๿]+", (text or "").lower()):
        if not chunk:
            continue
        for part in re.findall(r"\d+(?:\.\d+)?|[^\W\d_]+", chunk, flags=re.UNICODE):
            if not part:
                continue
            part = part.rstrip(".")
            out.append(UNIT_ALIAS.get(part, part))
    return out


def normalize_key(text: str) -> str:
    """คีย์ที่ไม่สนลำดับคำ — 'Minny 28' == '28 minny' == 'MINNY  28.'."""
    return " ".join(sorted(set(tokens(text))))


def _store_path(create: bool = False) -> pathlib.Path:
    try:
        from drive_path import get_pharmacy_dir  # type: ignore
        base = get_pharmacy_dir(create=create)
    except Exception:
        base = ROOT / "drive" / "pharmacy"
    return base / FILENAME


def load() -> dict:
    p = _store_path()
    if not p.exists():
        return {"schema_version": SCHEMA_VERSION, "updated": None, "aliases": {}}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"❌ {p} เสียหาย: {exc}")
    data.setdefault("aliases", {})
    return data


def save(data: dict) -> pathlib.Path:
    p = _store_path(create=True)
    data["schema_version"] = SCHEMA_VERSION
    data["updated"] = f"{date.today():%Y-%m-%d}"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return p


FIELDS = ("category", "name", "strength", "pack", "unit", "note")


def resolve(raw: str, data: dict | None = None) -> dict | None:
    """คืน record ที่ยืนยันแล้ว ถ้าเคยเรียนคำนี้ไว้ — ไม่งั้น None."""
    data = data if data is not None else load()
    rec = data["aliases"].get(normalize_key(raw))
    if not rec:
        return None
    return {**{k: rec.get(k, "") for k in FIELDS},
            "_alias_hit": True, "_confirmed_at": rec.get("confirmed_at"),
            "_hits": rec.get("hits", 0)}


def learn(raw: str, record: dict, data: dict | None = None,
          source: str = "user-confirmed") -> tuple[dict, bool]:
    """
    จำ 'ข้อความดิบที่ผู้ใช้พิมพ์' → 'รายการที่ยืนยันแล้ว'
    คืน (data, is_new). เรียนซ้ำ = merge raw variant + นับ hits ไม่เขียนทับข้อมูลที่ดีกว่าด้วยค่าว่าง
    """
    data = data if data is not None else load()
    if not raw or not record.get("name"):
        return data, False

    key = normalize_key(raw)
    if not key:
        return data, False

    cur = data["aliases"].get(key)
    is_new = cur is None
    if cur is None:
        cur = {"raw": [], "hits": 0}

    for f in FIELDS:
        val = (record.get(f) or "").strip()
        if val:                       # ค่าว่างไม่ทับของเดิม
            cur[f] = val
    raws = cur.setdefault("raw", [])
    if raw.strip() and raw.strip() not in raws:
        raws.append(raw.strip())
    cur["hits"] = int(cur.get("hits", 0)) + 1
    cur["source"] = source
    cur["confirmed_at"] = f"{date.today():%Y-%m-%d}"

    data["aliases"][key] = cur
    return data, is_new


def learn_many(items: list[dict], source: str = "user-confirmed") -> dict:
    """items ต้องมี 'raw' (สิ่งที่ผู้ใช้พิมพ์) + 'name' (ชื่อที่ยืนยันแล้ว)."""
    data = load()
    new = updated = skipped = 0
    for it in items:
        raw = it.get("raw") or ""
        if not raw or not it.get("name"):
            skipped += 1
            continue
        # ถ้า raw ตรงกับชื่อจริงอยู่แล้ว ไม่ต้องจำ (ไม่ได้ช่วยอะไร)
        if normalize_key(raw) == normalize_key(it["name"]) and not it.get("force"):
            skipped += 1
            continue
        data, is_new = learn(raw, it, data, source=source)
        new += is_new
        updated += (not is_new)
    path = save(data)
    return {"new": new, "updated": updated, "skipped": skipped,
            "total": len(data["aliases"]), "path": str(path)}


# ------------------------------------------------------------------ cli

def _cmd_resolve(a) -> int:
    data = load()
    for raw in a.texts:
        hit = resolve(raw, data)
        if hit:
            print(f"✅ {raw:32s} → {hit['name']} | {hit.get('strength','')} | "
                  f"{hit.get('pack','')} ({hit['_hits']} ครั้ง, ยืนยัน {hit['_confirmed_at']})")
        else:
            print(f"— {raw:32s} → ยังไม่เคยเรียน")
    return 0


def _cmd_learn(a) -> int:
    raw_text = pathlib.Path(a.file).read_text(encoding="utf-8") if a.file != "-" else sys.stdin.read()
    items = json.loads(raw_text)
    if isinstance(items, dict):
        items = items.get("items", [])
    info = learn_many(items, source=a.source)
    print(json.dumps(info, ensure_ascii=False, indent=2))
    return 0


def _cmd_stats(a) -> int:
    data = load()
    al = data["aliases"]
    if not al:
        print("ยังไม่มี alias — ใช้ learn หลังยืนยันชื่อยาครั้งแรก")
        return 0
    hits = sum(int(v.get("hits", 0)) for v in al.values())
    top = sorted(al.items(), key=lambda kv: -int(kv[1].get("hits", 0)))[:5]
    print(f"📚 {_store_path()}")
    print(f"   alias ทั้งหมด : {len(al):,}")
    print(f"   ถูกใช้รวม     : {hits:,} ครั้ง")
    print(f"   อัปเดตล่าสุด  : {data.get('updated')}")
    print("   ใช้บ่อยสุด:")
    for k, v in top:
        print(f"     {v.get('hits',0):>3}× {v.get('name','?')}  ← {', '.join(v.get('raw', [])[:3])}")
    return 0


def _cmd_list(a) -> int:
    data = load()
    for k, v in sorted(data["aliases"].items(), key=lambda kv: kv[1].get("name", "")):
        line = f"{v.get('name','?')} | {v.get('strength','')} | {v.get('pack','')} ← {', '.join(v.get('raw', []))}"
        if a.grep and a.grep.lower() not in line.lower():
            continue
        print(line)
    return 0


def _cmd_forget(a) -> int:
    data = load()
    n = 0
    for raw in a.texts:
        if data["aliases"].pop(normalize_key(raw), None) is not None:
            n += 1
            print(f"🗑  ลบแล้ว: {raw}")
        else:
            print(f"— ไม่พบ: {raw}")
    if n:
        save(data)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("resolve", help="ค้นว่าเคยเรียนคำนี้ไว้ไหม")
    r.add_argument("texts", nargs="+")
    r.set_defaults(fn=_cmd_resolve)

    l = sub.add_parser("learn", help="เรียนจากรายการที่ยืนยันแล้ว (JSON ต้องมี raw + name)")
    l.add_argument("--file", default="-")
    l.add_argument("--source", default="user-confirmed")
    l.set_defaults(fn=_cmd_learn)

    s = sub.add_parser("stats", help="สถิติคลังคำพ้อง")
    s.set_defaults(fn=_cmd_stats)

    ls = sub.add_parser("list", help="ดู alias ทั้งหมด")
    ls.add_argument("--grep")
    ls.set_defaults(fn=_cmd_list)

    f = sub.add_parser("forget", help="ลบ alias ที่จำผิด")
    f.add_argument("texts", nargs="+")
    f.set_defaults(fn=_cmd_forget)

    a = ap.parse_args()
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
