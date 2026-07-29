"""Guard: raw-to-source.py must not duplicate a source page that already exists.

Root cause this encodes (observed on Mac, TODO [raw-to-source-dupe]):

  `source_exists()` matched only on the slug derived from the RAW FILENAME.
  A source page whose slug was chosen by a human does not collide with that
  derived slug, so the check missed it and a second page was created for the
  same raw document.

  Concretely: raw/`ตอน 3  สร้าง Dashboard Node-RED ... 📊.md` already had
  wiki/sources/3-dashboard-node-red.md (correct kebab-case English slug, with
  `original_file:` pointing at that raw file). Every `gen-index.py` run chained
  raw-to-source.py, which derived the slug `ตอน-3-สร้าง-dashboard-node-red-...`,
  found no page under that name, and wrote a duplicate — Thai filename
  (violating Core Rule #2) and a mangled title scraped from an <audio> tag.

The identity of a source page is its `original_file:` pointer, not its slug.
Two pages pointing at the same raw file are the same page.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# raw-to-source.py has a hyphen — load via importlib (same shape as test_gen_index.py)
_path = REPO_ROOT / "scripts" / "raw-to-source.py"
_spec = importlib.util.spec_from_file_location("raw_to_source", _path)
raw_to_source = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(raw_to_source)


def _write_source(sources_dir: Path, name: str, slug: str, original_file: str) -> Path:
    """Write a minimal source page with an `original_file:` pointer."""
    p = sources_dir / f"{name}.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        "---\n"
        "type: source\n"
        f'title: "test {slug}"\n'
        f"slug: {slug}\n"
        f"original_file: {original_file}\n"
        "tags: []\n"
        "---\n",
        encoding="utf-8",
    )
    return p


def test_matches_existing_page_with_a_different_slug(tmp_path, monkeypatch):
    """The regression: same raw file, human-chosen slug — must be recognised."""
    sources = tmp_path / "wiki" / "sources"
    sources.mkdir(parents=True)
    raw_rel = "raw/ตอน 3  สร้าง Dashboard Node-RED มอนิเตอร์และควบคุมทุกอย่าง 📊.md"
    _write_source(sources, "3-dashboard-node-red", "3-dashboard-node-red", raw_rel)

    monkeypatch.setattr(raw_to_source, "SOURCES_DIR", sources)

    assert raw_to_source.source_exists_for_raw(raw_rel) is True, (
        "a source page already points at this raw file — creating another one "
        "duplicates the document under a filename-derived slug"
    )


def test_finds_page_in_a_domain_subdir(tmp_path, monkeypatch):
    """Sources may live at wiki/sources/<domain>/<slug>.md — must still match."""
    sources = tmp_path / "wiki" / "sources"
    (sources / "iot").mkdir(parents=True)
    raw_rel = "raw/some-doc.md"
    _write_source(sources / "iot", "nested-slug", "nested-slug", raw_rel)

    monkeypatch.setattr(raw_to_source, "SOURCES_DIR", sources)

    assert raw_to_source.source_exists_for_raw(raw_rel) is True


def test_unrelated_raw_file_is_not_matched(tmp_path, monkeypatch):
    """Must not over-match — a genuinely new raw file still gets a page."""
    sources = tmp_path / "wiki" / "sources"
    sources.mkdir(parents=True)
    _write_source(sources, "existing", "existing", "raw/existing.md")

    monkeypatch.setattr(raw_to_source, "SOURCES_DIR", sources)

    assert raw_to_source.source_exists_for_raw("raw/brand-new.md") is False


@pytest.mark.parametrize(
    "written",
    [
        "raw/quoted.md",
        '"raw/quoted.md"',
        "'raw/quoted.md'",
        "  raw/quoted.md  ",
    ],
    ids=["bare", "double-quoted", "single-quoted", "padded"],
)
def test_pointer_is_read_regardless_of_quoting(tmp_path, monkeypatch, written):
    """Existing pages were written by several generators — quoting varies."""
    sources = tmp_path / "wiki" / "sources"
    sources.mkdir(parents=True)
    _write_source(sources, "quoted", "quoted", written)

    monkeypatch.setattr(raw_to_source, "SOURCES_DIR", sources)

    assert raw_to_source.source_exists_for_raw("raw/quoted.md") is True


# Duplicates accumulated in wiki/sources/ before the fix above landed. The fix
# stops NEW ones; merging the existing pages needs editorial judgement (which
# slug is canonical, does the auto-generated page hold unique content) and is
# tracked separately. This is a ratchet: the backlog may shrink, never grow.
# Measured 2026-07-29 on main.
KNOWN_DUPLICATE_RAW_DOCS = 34
KNOWN_REDUNDANT_PAGES = 51


def _duplicate_pointers() -> dict[str, list[str]]:
    """raw/ documents claimed by more than one source page.

    Only `raw/`-rooted pointers count. Placeholder pointers left by older
    ingest paths (`web-search`, `paste-text`) are not raw documents, so pages
    sharing one are not duplicates of each other.
    """
    seen: dict[str, list[str]] = {}
    for page in (REPO_ROOT / "wiki" / "sources").rglob("*.md"):
        if page.name == "CLAUDE.md":
            continue
        pointer = raw_to_source.read_original_file(page)
        if not pointer or not pointer.startswith("raw/"):
            continue
        seen.setdefault(pointer, []).append(str(page.relative_to(REPO_ROOT)))
    return {k: v for k, v in seen.items() if len(v) > 1}


def test_duplicate_source_pages_do_not_grow():
    """Ratchet: raw-to-source.py must never add a page for an already-claimed doc."""
    if not (REPO_ROOT / "wiki" / "sources").is_dir():
        pytest.skip("wiki/sources/ not present")

    dupes = _duplicate_pointers()
    redundant = sum(len(v) - 1 for v in dupes.values())

    assert len(dupes) <= KNOWN_DUPLICATE_RAW_DOCS and redundant <= KNOWN_REDUNDANT_PAGES, (
        f"duplicate source pages grew: {len(dupes)} raw docs / {redundant} redundant "
        f"pages (baseline {KNOWN_DUPLICATE_RAW_DOCS}/{KNOWN_REDUNDANT_PAGES}).\n"
        + "\n".join(
            f"  {raw}\n" + "".join(f"    - {p}\n" for p in pages)
            for raw, pages in sorted(dupes.items())
        )
    )
