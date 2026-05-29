from __future__ import annotations

import importlib.util
from pathlib import Path


def load_review_check():
    script = Path(__file__).resolve().parents[1] / "scripts" / "review-check.py"
    spec = importlib.util.spec_from_file_location("review_check", script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_link_review_skips_generated_context(monkeypatch, tmp_path):
    wiki = tmp_path / "wiki"
    context = wiki / "context"
    context.mkdir(parents=True)
    (wiki / "concepts").mkdir()

    (context / "review-report.md").write_text("[[missing-from-generated-report]]\n", encoding="utf-8")
    (context / "wiki-overview.md").write_text("[[missing-from-generated-overview]]\n", encoding="utf-8")
    (wiki / "concepts" / "real-page.md").write_text("[[missing-from-real-page]]\n", encoding="utf-8")

    review_check = load_review_check()
    monkeypatch.setattr(review_check, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(review_check, "WIKI_DIR", wiki)

    _passed, _warned, failed = review_check.run_l3()

    assert len(failed) == 1
    assert failed[0].replace("\\", "/") == (
        "wiki/concepts/real-page.md: broken link: [[missing-from-real-page]]"
    )
