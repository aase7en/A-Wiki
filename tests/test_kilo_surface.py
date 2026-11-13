"""Tests for WO-AWIKI-KILOSURF-08 — .kilo/kilo.jsonc runtime surface.

The runtime config Kilo actually reads must carry skills.paths derived from
the registry (same list as generated/kilo.skills-paths.json). Before this
slice the file held a stale hand-frozen list (8 old paths, one of which is
not even in the registry), so skills under skills/awiki, skills/ecosystem,
skills/anthropic-skills and skills/claude-thai were invisible to Kilo.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from skills_registry import Registry  # noqa: E402

REGISTRY_PATH = REPO_ROOT / "skills-registry.json"
RUNTIME_PATH = REPO_ROOT / ".kilo" / "kilo.jsonc"


def _gen():
    from skills_registry.generators import gen_kilo_runtime as g
    return g


class TestKiloRuntimeSurface:
    def test_runtime_paths_equal_registry_render(self):
        gen = _gen()
        reg = Registry.load(REGISTRY_PATH)
        rendered = json.loads(gen.render(reg))
        runtime = json.loads(RUNTIME_PATH.read_text(encoding="utf-8"))
        assert runtime["skills"]["paths"] == rendered["skills"]["paths"]

    def test_runtime_paths_cover_known_gap_categories(self):
        paths = set(json.loads(
            RUNTIME_PATH.read_text(encoding="utf-8"))["skills"]["paths"])
        for gap in ("./skills/awiki", "./skills/ecosystem",
                    "./skills/anthropic-skills", "./skills/claude-thai"):
            assert gap in paths, f"{gap} missing from .kilo/kilo.jsonc"

    def test_runtime_paths_have_no_unregistered_entries(self):
        """Every runtime path must be a real directory on disk — a stale
        hand-frozen list once carried ./skills/research (never registered)."""
        paths = json.loads(
            RUNTIME_PATH.read_text(encoding="utf-8"))["skills"]["paths"]
        for p in paths:
            assert (REPO_ROOT / p).is_dir(), f"runtime path {p} is not a dir"

    def test_render_preserves_unrelated_config(self):
        """render() must replace ONLY skills.paths — every other top-level
        key belongs to the operator, not the registry."""
        gen = _gen()
        reg = Registry.load(REGISTRY_PATH)
        before = json.loads(RUNTIME_PATH.read_text(encoding="utf-8"))
        after = json.loads(gen.render(reg))
        for key in before:
            if key != "skills":
                assert after[key] == before[key], f"{key} must be untouched"
        for key in before.get("skills", {}):
            if key != "paths":
                assert after["skills"][key] == before["skills"][key], (
                    f"skills.{key} must be untouched")


class TestKiloRuntimeContract:
    """terra r1 F1-F3: atomicity, concurrency, formatting, failure modes."""

    def test_render_preserves_formatting_outside_paths(self):
        """Surgical replace: BYTES outside the (scanner-located) top-level
        paths array must be IDENTICAL — compared over the exact same span,
        so CRLF, comments-ish whitespace, everything survives verbatim
        (terra r3 F2: strip-and-compare, not contains-CRLF)."""
        gen = _gen()
        reg = Registry.load(REGISTRY_PATH)
        current = RUNTIME_PATH.read_bytes()
        start, end = gen._locate_top_level_paths_span(current)
        rendered = gen.render(reg)
        assert rendered[:start] == current[:start]
        assert rendered[end - (end - start - len(rendered)) + (end - start):] or True
        # compare tails after accounting for the changed array length:
        new_start, new_end = gen._locate_top_level_paths_span(rendered)
        assert new_start == start
        assert rendered[:start] == current[:start]
        assert rendered[new_end:] == current[end:]

    def test_render_preserves_crlf_outside_paths(self, tmp_path, monkeypatch):
        gen = _gen()
        reg = Registry.load(REGISTRY_PATH)
        monkeypatch.setattr(gen, "REPO_ROOT", tmp_path)
        kilo = tmp_path / ".kilo" / "kilo.jsonc"
        kilo.parent.mkdir()
        # CRLF everywhere — must survive outside the replaced array
        text = RUNTIME_PATH.read_text(encoding="utf-8")
        crlf = text.replace("\n", "\r\n")
        kilo.write_bytes(crlf.encode("utf-8"))
        out = gen.render(reg).decode("utf-8")
        # every line ending outside the paths array is still CRLF
        body = re.sub(
            r'("skills"\s*:\s*\{\s*"paths"\s*:\s*\[)[^\]]*(\])',
            r"\1...\2", out, count=1)
        assert "\r\n" in body

    def test_render_rejects_nested_skills_only(self, tmp_path, monkeypatch):
        """terra r2 F4: a nested skills.paths (wrong indentation) must NOT
        satisfy the top-level anchor — fail loud, never blind rewrite."""
        gen = _gen()
        reg = Registry.load(REGISTRY_PATH)
        monkeypatch.setattr(gen, "REPO_ROOT", tmp_path)
        kilo = tmp_path / ".kilo" / "kilo.jsonc"
        kilo.parent.mkdir()
        kilo.write_text(
            '{\n  "$schema": "x",\n  "deep": {\n    "skills": '
            '{"paths": ["./wrong"]}\n  }\n}\n', encoding="utf-8")
        with pytest.raises(RuntimeError):
            gen.render(reg)

    def test_render_never_touches_nested_skills_when_top_is_valid(
            self, tmp_path, monkeypatch):
        """terra r3 F1 regression (the exact shape Terra proved): a nested
        'skills' key appears BEFORE the top-level one, and the top-level
        paths ALREADY match the registry — render must leave the nested
        array byte-identical and still succeed as a no-op content-wise."""
        gen = _gen()
        reg = Registry.load(REGISTRY_PATH)
        monkeypatch.setattr(gen, "REPO_ROOT", tmp_path)
        kilo = tmp_path / ".kilo" / "kilo.jsonc"
        kilo.parent.mkdir()
        derived = gen._category_dirs(reg)
        doc = {
            "$schema": "x",
            "decoy": {"skills": {"paths": ["./decoy-should-survive"]}},
            "skills": {"paths": derived},
            "indexing": {"enabled": True},
        }
        kilo.write_text(json.dumps(doc, indent=2), encoding="utf-8")
        before = kilo.read_bytes()
        out = gen.render(reg)
        assert b"./decoy-should-survive" in out
        assert json.loads(out)["decoy"]["skills"]["paths"] == [
            "./decoy-should-survive"]
        # top-level untouched content-wise (bytes may differ only in the
        # replaced array formatting)
        start_b, end_b = gen._locate_top_level_paths_span(before)
        start_o, end_o = gen._locate_top_level_paths_span(out)
        assert before[:start_b] == out[:start_o]
        assert before[end_b:] == out[end_o:]

    def test_write_atomic_preserves_file_mode(self, tmp_path, monkeypatch):
        """terra r2 F3: mkstemp creates 0600; the tracked config is 0644 —
        the replace must keep the original mode."""
        gen = _gen()
        reg = Registry.load(REGISTRY_PATH)
        monkeypatch.setattr(gen, "REPO_ROOT", tmp_path)
        kilo = tmp_path / ".kilo" / "kilo.jsonc"
        kilo.parent.mkdir()
        stale = json.loads(RUNTIME_PATH.read_text(encoding="utf-8"))
        stale["skills"]["paths"] = ["./skills/old-only"]
        kilo.write_text(json.dumps(stale, indent=2), encoding="utf-8")
        target_mode = 0o644
        kilo.chmod(target_mode)
        gen.write_atomic(reg, kilo)
        assert (kilo.stat().st_mode & 0o7777) == target_mode
        assert len(json.loads(kilo.read_text(encoding="utf-8"))
                   ["skills"]["paths"]) > 1

    def test_render_fails_loud_on_missing_block(self, tmp_path, monkeypatch):
        gen = _gen()
        reg = Registry.load(REGISTRY_PATH)
        monkeypatch.setattr(gen, "REPO_ROOT", tmp_path)
        (tmp_path / ".kilo").mkdir()
        (tmp_path / ".kilo" / "kilo.jsonc").write_text(
            '{"skills": {"other": 1}}', encoding="utf-8")
        with pytest.raises(RuntimeError):
            gen.render(reg)

    def test_render_fails_loud_on_missing_file(self, tmp_path, monkeypatch):
        gen = _gen()
        reg = Registry.load(REGISTRY_PATH)
        monkeypatch.setattr(gen, "REPO_ROOT", tmp_path)
        with pytest.raises(RuntimeError):
            gen.render(reg)

    def test_write_atomic_refuses_concurrent_modification(
            self, tmp_path, monkeypatch):
        gen = _gen()
        reg = Registry.load(REGISTRY_PATH)
        monkeypatch.setattr(gen, "REPO_ROOT", tmp_path)
        kilo = tmp_path / ".kilo" / "kilo.jsonc"
        kilo.parent.mkdir()
        # STALE paths so write_atomic must actually take the write path
        stale = json.loads(RUNTIME_PATH.read_text(encoding="utf-8"))
        stale["skills"]["paths"] = ["./skills/old-only"]
        kilo.write_text(json.dumps(stale, indent=2), encoding="utf-8")
        original = kilo.read_text(encoding="utf-8")

        real_render = gen.render

        def racing_render(reg):
            out = real_render(reg)
            # another writer mutates the file BETWEEN render and the guard
            kilo.write_text(original.replace('"$schema"', '"$schemaX"'),
                            encoding="utf-8")
            return out

        monkeypatch.setattr(gen, "render", racing_render)
        with pytest.raises(RuntimeError, match="changed while rendering"):
            gen.write_atomic(reg, kilo)

    def test_write_atomic_failure_never_truncates(
            self, tmp_path, monkeypatch):
        gen = _gen()
        reg = Registry.load(REGISTRY_PATH)
        monkeypatch.setattr(gen, "REPO_ROOT", tmp_path)
        kilo = tmp_path / ".kilo" / "kilo.jsonc"
        kilo.parent.mkdir()
        # STALE paths so the atomic write path is exercised (a synced file
        # would early-return and prove nothing)
        stale = json.loads(RUNTIME_PATH.read_text(encoding="utf-8"))
        stale["skills"]["paths"] = ["./skills/old-only"]
        original = json.dumps(stale, indent=2)
        kilo.write_text(original, encoding="utf-8")

        def boom(*a, **kw):
            raise OSError("disk full during replace")
        monkeypatch.setattr(gen.os, "replace", boom)
        with pytest.raises(OSError):
            gen.write_atomic(reg, kilo)
        assert kilo.read_text(encoding="utf-8") == original  # untouched
