#!/bin/bash
# SessionStart hook — auto-rebuild drugs.db when JSON sources are newer
# Level 0: free, runs every session, ~2-3 seconds

DB="wiki/entities/pharmacy/drugs.db"
SP_JSON="raw/pharmacy/sp_drugs_full_3760.json"
ALT_JSON="wiki/entities/pharmacy/alternative-source-items.json"

needs_rebuild() {
    [ ! -f "$DB" ] && return 0
    [ -f "$SP_JSON"  ] && [ "$SP_JSON"  -nt "$DB" ] && return 0
    [ -f "$ALT_JSON" ] && [ "$ALT_JSON" -nt "$DB" ] && return 0
    return 1
}

if needs_rebuild; then
    echo "🔄 Pharmacy DB: rebuilding from JSON sources..."
    python3 scripts/build_pharmacy_db.py 2>&1
else
    ITEMS=$(python3 -c \
        "import sqlite3; c=sqlite3.connect('$DB'); \
         sp=c.execute(\"SELECT COUNT(*) FROM drugs WHERE source='sp_2020'\").fetchone()[0]; \
         vs=c.execute(\"SELECT COUNT(*) FROM drugs WHERE source='verified_search'\").fetchone()[0]; \
         print(f'SP={sp} verified={vs}')" 2>/dev/null || echo "?")
    echo "✅ Pharmacy DB current | $ITEMS"
fi
