from __future__ import annotations

import importlib.util
import sqlite3
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "search-wiki.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("awiki_search_wiki", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _make_fts_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.execute("CREATE VIRTUAL TABLE wiki USING fts5(path, title, tags, body)")
        conn.execute(
            "INSERT INTO wiki(path, title, tags, body) VALUES (?, ?, ?, ?)",
            ("wiki/entities/ai-tools/agent-reach.md", "Agent-Reach", "research", "Agent-Reach social research adapter"),
        )
        conn.commit()
    finally:
        conn.close()


def test_normalize_query_quotes_bare_hyphenated_term():
    module = _load_module()
    assert module.normalize_query("Agent-Reach") == '"Agent-Reach"'


def test_normalize_query_preserves_plain_term_and_semantics():
    module = _load_module()
    assert module.normalize_query("MQTT esp32") == '"MQTT" "esp32"'


def test_normalize_query_preserves_explicit_fts_syntax():
    module = _load_module()
    for query in ('title:MQTT', 'MQTT OR LoRa', '"agent reach"'):
        assert module.normalize_query(query) == query


def test_hyphenated_literal_search_does_not_raise(tmp_path, monkeypatch):
    module = _load_module()
    db_path = tmp_path / "wiki.db"
    _make_fts_db(db_path)
    monkeypatch.setattr(module, "DB_PATH", db_path)

    rows = module.search(module.normalize_query("Agent-Reach"), 5, None)

    assert rows
    assert rows[0][0] == "wiki/entities/ai-tools/agent-reach.md"
