import pytest, sqlite3, pathlib
import sys

ROOT = pathlib.Path(__file__).parent.parent
sys.path.append(str(ROOT / "scripts"))
import pharmacy_lookup

def test_tonaf_matching():
    # Verify that TONAF1%แดง15g matches correctly in the database
    db_path = ROOT / "wiki/entities/pharmacy/drugs.db"
    assert db_path.exists(), "drugs.db must exist for this test"
    
    conn = sqlite3.connect(db_path)
    try:
        hits = pharmacy_lookup.search_db(conn, "TONAF1%แดง15g", top_n=3)
        assert len(hits) > 0, "Should find at least one match for TONAF"
        score, row = hits[0]
        # Check that the matched name contains TONAF
        assert "TONAF" in row[1], f"Top match {row[1]} should contain TONAF"
        # Check that it matched with high confidence (>= 0.80)
        assert score >= pharmacy_lookup.CONF_HIGH, f"Score {score} should be >= CONF_HIGH ({pharmacy_lookup.CONF_HIGH})"
    finally:
        conn.close()
