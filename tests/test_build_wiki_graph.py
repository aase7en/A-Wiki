from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "build-wiki-graph.py"
spec = importlib.util.spec_from_file_location("build_wiki_graph", SCRIPT)
assert spec and spec.loader
build_wiki_graph = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = build_wiki_graph
spec.loader.exec_module(build_wiki_graph)


def test_external_markdown_urls_are_not_local_broken_links():
    assert build_wiki_graph.is_external_url("https://github.com/org/repo/blob/main/API.md")
    assert build_wiki_graph.is_external_url("http://example.com/readme.md")
    assert build_wiki_graph.is_external_url("mailto:team@example.com")
    assert not build_wiki_graph.is_external_url("wiki/sources/example.md")


def test_build_reports_full_orphan_domain_counts(tmp_path, monkeypatch):
    wiki = tmp_path / "wiki"
    for path in (
        wiki / "context" / "now.md",
        wiki / "sources" / "source-one.md",
        wiki / "entities" / "iot" / "esp32.md",
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# {path.stem}\n", encoding="utf-8")

    monkeypatch.setattr(build_wiki_graph, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(build_wiki_graph, "WIKI_DIR", wiki)
    monkeypatch.setattr(build_wiki_graph, "PARSE_SKIP_DIRS", (wiki / "context",))

    graph = build_wiki_graph.build()

    assert graph["stats"]["orphans"] == 3
    assert graph["stats"]["orphan_by_domain"] == {
        "context": 1,
        "iot": 1,
        "sources": 1,
    }
