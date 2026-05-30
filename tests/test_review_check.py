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


def test_link_resolver_understands_repo_and_wiki_prefixed_paths(monkeypatch, tmp_path):
    wiki = tmp_path / "wiki"
    target = wiki / "concepts" / "ai-tools" / "local-llm-routing.md"
    target.parent.mkdir(parents=True)
    target.write_text("# Target\n", encoding="utf-8")
    script = tmp_path / "scripts" / "setup-cloud-link.sh"
    script.parent.mkdir()
    script.write_text("#!/bin/sh\n", encoding="utf-8")
    origin = wiki / "concepts" / "ai-tools" / "origin.md"
    origin.write_text("[[wiki/concepts/ai-tools/local-llm-routing]] [[scripts/setup-cloud-link.sh]]\n", encoding="utf-8")

    review_check = load_review_check()
    monkeypatch.setattr(review_check, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(review_check, "WIKI_DIR", wiki)

    assert review_check.check_wiki_links(origin) == []


def test_non_http_markdown_schemes_are_not_treated_as_files(tmp_path, monkeypatch):
    wiki = tmp_path / "wiki"
    page = wiki / "sources" / "demo.md"
    page.parent.mkdir(parents=True)
    page.write_text("[share](fb-messenger://share/?link=https://example.com)\n", encoding="utf-8")

    review_check = load_review_check()
    monkeypatch.setattr(review_check, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(review_check, "WIKI_DIR", wiki)

    assert review_check.check_wiki_links(page) == []


def test_malformed_multiline_link_from_clipped_generated_text_is_ignored(tmp_path, monkeypatch):
    wiki = tmp_path / "wiki"
    page = wiki / "context" / "wiki-overview.md"
    page.parent.mkdir(parents=True)
    page.write_text("[[entities/io… |\n| row | still clipped [[entities/iot/ds18b20]]\n", encoding="utf-8")
    target = wiki / "entities" / "iot" / "ds18b20.md"
    target.parent.mkdir(parents=True)
    target.write_text("# DS18B20\n", encoding="utf-8")

    review_check = load_review_check()
    monkeypatch.setattr(review_check, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(review_check, "WIKI_DIR", wiki)

    assert review_check.check_wiki_links(page) == []


def test_generated_profile_reviews_only_generated_context(monkeypatch, tmp_path):
    wiki = tmp_path / "wiki"
    context = wiki / "context"
    concepts = wiki / "concepts"
    context.mkdir(parents=True)
    concepts.mkdir()

    (context / "review-report.md").write_text("[[missing-from-report]]\n", encoding="utf-8")
    (context / "wiki-overview.md").write_text("[[missing-generated]]\n", encoding="utf-8")
    (concepts / "real-page.md").write_text("[[missing-real]]\n", encoding="utf-8")

    review_check = load_review_check()
    monkeypatch.setattr(review_check, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(review_check, "WIKI_DIR", wiki)
    monkeypatch.setattr(review_check, "ACTIVE_PROFILE", "generated")

    _passed, _warned, failed = review_check.run_l3()

    assert len(failed) == 1
    assert "missing-generated" in failed[0]
    assert "missing-from-report" not in failed[0]
    assert "missing-real" not in failed[0]


def test_content_profile_downgrades_frontmatter_noise(monkeypatch, tmp_path):
    wiki = tmp_path / "wiki"
    page = wiki / "concepts" / "demo.md"
    page.parent.mkdir(parents=True)
    page.write_text("# Demo\n", encoding="utf-8")

    review_check = load_review_check()
    monkeypatch.setattr(review_check, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(review_check, "WIKI_DIR", wiki)
    monkeypatch.setattr(review_check, "ACTIVE_PROFILE", "content")

    _passed, warned, failed = review_check.run_l2()

    assert warned
    assert not failed


def test_report_includes_profile_and_top_actionable():
    review_check = load_review_check()
    report = review_check.write_report(
        {"L2": ([], ["wiki/a.md: missing title"], ["wiki/b.md: broken"])},
        {"L2": "Frontmatter"},
        profile="content",
    )

    assert "Profile" in report
    assert "Top Actionable Issues" in report
    assert "wiki/b.md: broken" in report
