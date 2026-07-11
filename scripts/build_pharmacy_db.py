#!/usr/bin/env python3
"""
Build pharmacy SQLite database from JSON source files.
Run automatically by SessionStart hook when DB is stale.

Sources:
  raw/pharmacy/sp_drugs_full_3760.json         → source = 'sp_2020'
  drive/pharmacy/alternative-source-items.json → source = 'verified_search'
Output:
  wiki/entities/pharmacy/drugs.db              (SQLite + FTS5)
"""
import json, sqlite3, pathlib, sys, time

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from drive_path import get_pharmacy_dir, DriveNotLinkedError  # noqa: E402

DB_PATH  = ROOT / "wiki/entities/pharmacy/drugs.db"
SP_JSON  = ROOT / "raw/pharmacy/sp_drugs_full_3760.json"

try:
    ALT_JSON = get_pharmacy_dir() / "alternative-source-items.json"
except DriveNotLinkedError as e:
    print(f"⚠️  {e}", file=sys.stderr)
    print("⚠️  Continuing without verified-search items (drive/ not linked).", file=sys.stderr)
    ALT_JSON = None

SCHEMA = """
PRAGMA journal_mode=WAL;

DROP TABLE IF EXISTS drugs_fts;
DROP TABLE IF EXISTS drugs;

CREATE TABLE drugs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    name_th       TEXT DEFAULT '',
    name_en       TEXT DEFAULT '',
    aliases       TEXT DEFAULT '[]',   -- JSON array
    category_code TEXT DEFAULT '',
    category_name TEXT DEFAULT '',
    strength      TEXT DEFAULT '',
    package_size  TEXT DEFAULT '',
    unit          TEXT DEFAULT '',
    supplier      TEXT DEFAULT '',
    where_to_buy  TEXT DEFAULT '',
    note          TEXT DEFAULT '',
    source        TEXT DEFAULT 'sp_2020',  -- sp_2020 | verified_search | manual
    verified_date TEXT DEFAULT ''
);

CREATE INDEX idx_drugs_source ON drugs(source);

CREATE VIRTUAL TABLE drugs_fts USING fts5(
    name, name_th, name_en, aliases,
    content=drugs,
    content_rowid=id,
    tokenize='unicode61 remove_diacritics 1'
);

CREATE TRIGGER drugs_ai AFTER INSERT ON drugs BEGIN
    INSERT INTO drugs_fts(rowid, name, name_th, name_en, aliases)
    VALUES (new.id, new.name, new.name_th, new.name_en, new.aliases);
END;

CREATE TRIGGER drugs_ad AFTER DELETE ON drugs BEGIN
    INSERT INTO drugs_fts(drugs_fts, rowid, name, name_th, name_en, aliases)
    VALUES ('delete', old.id, old.name, old.name_th, old.name_en, old.aliases);
END;
"""


def build():
    t0 = time.time()
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)

    # ── SP Drugstore 2020 ────────────────────────────────────────────────────
    with open(SP_JSON, encoding="utf-8") as f:
        sp_data = json.load(f)

    sp_rows = [
        (
            item.get("name", ""),
            "", "",                          # name_th, name_en
            "[]",                            # aliases
            item.get("category_code", ""),
            item.get("category_name", ""),
            item.get("strength", ""),
            "",                              # package_size (not in SP schema)
            item.get("unit", ""),
            item.get("supplier", "เอสพีดรักสโตร์ 2020"),
            "", "",                          # where_to_buy, note
            "sp_2020", "",
        )
        for item in sp_data
    ]
    conn.executemany(
        "INSERT INTO drugs(name,name_th,name_en,aliases,category_code,category_name,"
        "strength,package_size,unit,supplier,where_to_buy,note,source,verified_date)"
        " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        sp_rows,
    )

    # ── Verified-search items ────────────────────────────────────────────────
    alt_count = 0
    if ALT_JSON is not None and ALT_JSON.exists():
        with open(ALT_JSON, encoding="utf-8") as f:
            alt_data = json.load(f)

        alt_rows = []
        for item in alt_data:
            aliases = item.get("aliases", [])
            alt_rows.append((
                item.get("name", ""),
                item.get("name_th", ""),
                item.get("name_en", ""),
                json.dumps(aliases, ensure_ascii=False),
                item.get("category_code", ""),
                item.get("category_name", ""),
                item.get("strength", ""),
                item.get("package_size", ""),
                item.get("unit", ""),
                "",                          # supplier
                item.get("where_to_buy", ""),
                item.get("note", ""),
                "verified_search",
                item.get("verified_date", ""),
            ))
        conn.executemany(
            "INSERT INTO drugs(name,name_th,name_en,aliases,category_code,category_name,"
            "strength,package_size,unit,supplier,where_to_buy,note,source,verified_date)"
            " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            alt_rows,
        )
        alt_count = len(alt_rows)

    conn.commit()
    conn.close()

    sp_count = len(sp_rows)
    elapsed = time.time() - t0
    print(f"✅ drugs.db built: {sp_count} SP + {alt_count} verified-search items ({elapsed:.1f}s)")
    print(f"   Path: {DB_PATH}")


if __name__ == "__main__":
    build()
