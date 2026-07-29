#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
import_medi_list.py — สร้าง medi_list.db จาก 'รายการยาทั้งหมด.xls' (stock report ปัจจุบันของร้าน)

ที่มาไฟล์  : drive/pharmacy/medi.list/รายการยาทั้งหมด.xls  (TIS-620 / cp874, .xls แบบ OLE2)
ปลายทาง    : wiki/entities/pharmacy/medi_list.db  (SQLite + FTS5, gitignored)

ต่างจาก drugs.db อย่างไร
  drugs.db      = แคตตาล็อก SP ปี 2020 (3,760 SKU) + รายการที่ verify จาก web search
  medi_list.db  = สต๊อกจริง ณ ปัจจุบัน + "ทุน" (ราคาต้นทุนต่อหน่วย) + "คงเหลือ"
  → ใช้ medi_list.db เป็นแหล่งหลักเวลาทำใบสั่งซื้อ เพราะมีต้นทุนและหน่วยที่ร้านใช้จริง

Usage:
    python3 scripts/import_medi_list.py                # auto-discover ไฟล์ล่าสุดใน drive
    python3 scripts/import_medi_list.py --xls <path>   # ระบุไฟล์เอง
    python3 scripts/import_medi_list.py --stats        # ดูสถิติ DB ที่มีอยู่
"""
from __future__ import annotations

import argparse
import pathlib
import re
import sqlite3
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

DB_PATH = ROOT / "wiki/entities/pharmacy/medi_list.db"

# ชื่อคอลัมน์ที่คาดหวังในแถว header ของ stock report
COL = {"no": 0, "code": 2, "name": 3, "unit": 6, "on_hand": 7,
       "min": 8, "max": 9, "short": 10, "cost": 11}


def _pharmacy_dir() -> pathlib.Path:
    """ใช้ resolver กลางของ repo — ห้าม hardcode path ส่วนตัว (Iron Law #6)."""
    try:
        from drive_path import get_pharmacy_dir  # type: ignore
        return get_pharmacy_dir(create=False)
    except Exception:
        return ROOT / "drive" / "pharmacy"


def discover_xls() -> pathlib.Path | None:
    base = _pharmacy_dir() / "medi.list"
    if not base.exists():
        return None
    cands = sorted(base.glob("*.xls*"), key=lambda p: p.stat().st_mtime, reverse=True)
    return cands[0] if cands else None


def norm_name(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"\s+", " ", s)
    return s


def read_rows(xls: pathlib.Path) -> list[dict]:
    import xlrd  # .xls แบบเก่าเท่านั้น — pandas/openpyxl อ่านไม่ได้

    bk = xlrd.open_workbook(str(xls), encoding_override="cp874")
    sh = bk.sheet_by_index(0)

    rows: list[dict] = []
    for r in range(sh.nrows):
        try:
            no = sh.cell_value(r, COL["no"])
        except IndexError:
            continue
        if not isinstance(no, float):          # แถวข้อมูลจริงมีเลขลำดับเป็นตัวเลข
            continue
        name = norm_name(str(sh.cell_value(r, COL["name"])))
        if not name:
            continue

        def num(key: str) -> float | None:
            v = sh.cell_value(r, COL[key])
            return float(v) if isinstance(v, float) else None

        rows.append({
            "code": str(sh.cell_value(r, COL["code"])).strip(),
            "name": name,
            "unit": norm_name(str(sh.cell_value(r, COL["unit"]))),
            "on_hand": num("on_hand"),
            "min_qty": num("min"),
            "max_qty": num("max"),
            "short_qty": num("short"),
            "cost": num("cost"),
        })
    return rows


SCHEMA = """
DROP TABLE IF EXISTS medi;
CREATE TABLE medi (
    id        INTEGER PRIMARY KEY,
    code      TEXT,
    name      TEXT NOT NULL,
    name_norm TEXT,
    unit      TEXT,
    on_hand   REAL,
    min_qty   REAL,
    max_qty   REAL,
    short_qty REAL,
    cost      REAL,
    source    TEXT DEFAULT 'medi_list',
    imported  TEXT
);
CREATE INDEX idx_medi_code ON medi(code);
CREATE INDEX idx_medi_short ON medi(short_qty);
DROP TABLE IF EXISTS medi_fts;
CREATE VIRTUAL TABLE medi_fts USING fts5(
    name, name_norm, code, content='medi', content_rowid='id',
    tokenize='unicode61 remove_diacritics 0'
);
"""


def build(rows: list[dict], db_path: pathlib.Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    conn.executemany(
        "INSERT INTO medi (code,name,name_norm,unit,on_hand,min_qty,max_qty,short_qty,cost,imported)"
        " VALUES (?,?,?,?,?,?,?,?,?,?)",
        [(r["code"], r["name"], r["name"].lower(), r["unit"], r["on_hand"],
          r["min_qty"], r["max_qty"], r["short_qty"], r["cost"], stamp) for r in rows],
    )
    conn.execute("INSERT INTO medi_fts(rowid,name,name_norm,code) "
                 "SELECT id,name,name_norm,code FROM medi")
    conn.commit()
    conn.close()


def stats(db_path: pathlib.Path) -> None:
    if not db_path.exists():
        print(f"❌ ยังไม่มี DB: {db_path}")
        return
    conn = sqlite3.connect(db_path)
    total, = conn.execute("SELECT COUNT(*) FROM medi").fetchone()
    priced, = conn.execute("SELECT COUNT(*) FROM medi WHERE cost > 0").fetchone()
    short, = conn.execute("SELECT COUNT(*) FROM medi WHERE short_qty > 0").fetchone()
    when, = conn.execute("SELECT MAX(imported) FROM medi").fetchone()
    conn.close()
    print(f"📦 {db_path}")
    print(f"   รายการทั้งหมด : {total:,}")
    print(f"   มีราคาทุน     : {priced:,}")
    print(f"   ติดลบ/ขาด     : {short:,}")
    print(f"   นำเข้าเมื่อ    : {when}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--xls", help="path ของ stock report (.xls)")
    ap.add_argument("--db", default=str(DB_PATH), help="ปลายทาง SQLite")
    ap.add_argument("--stats", action="store_true", help="แสดงสถิติ DB แล้วออก")
    args = ap.parse_args()

    db_path = pathlib.Path(args.db)
    if args.stats:
        stats(db_path)
        return 0

    xls = pathlib.Path(args.xls) if args.xls else discover_xls()
    if not xls or not xls.exists():
        print("❌ ไม่พบไฟล์ stock report — ระบุด้วย --xls หรือเช็คว่า drive/ ลิงก์อยู่", file=sys.stderr)
        print("   คาดว่าอยู่ที่: <drive>/pharmacy/medi.list/*.xls", file=sys.stderr)
        return 1

    print(f"📖 อ่าน: {xls.name}")
    rows = read_rows(xls)
    if not rows:
        print("❌ อ่านไม่ได้ 0 แถว — ตรวจ layout คอลัมน์ใน COL dict", file=sys.stderr)
        return 1

    build(rows, db_path)
    print(f"✅ นำเข้า {len(rows):,} รายการ")
    stats(db_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
