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
        """Surgical replace: bytes outside the paths array must be identical,
        including any unusual whitespace an operator keeps there."""
        gen = _gen()
        reg = Registry.load(REGISTRY_PATH)
        rendered = gen.render(reg)
        current = RUNTIME_PATH.read_text(encoding="utf-8")

        def without_paths(t):
            return re.sub(
                r'("skills"\s*:\s*\{\s*"paths"\s*:\s*\[)[^\]]*(\])',
                r"\1...\2", t, count=1)

        assert without_paths(rendered) == without_paths(current)

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
