"""Tests for WO-AWIKI-KILOSURF-08 — .kilo/kilo.jsonc runtime surface.

The runtime config Kilo actually reads must carry skills.paths derived from
the registry (same list as generated/kilo.skills-paths.json). Before this
slice the file held a stale hand-frozen list (8 old paths, one of which is
not even in the registry), so skills under skills/awiki, skills/ecosystem,
skills/anthropic-skills and skills/claude-thai were invisible to Kilo.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from skills_registry import Registry  # noqa: E402


REGISTRY_PATH = REPO_ROOT / "skills-registry.json"
RUNTIME_PATH = REPO_ROOT / ".kilo" / "kilo.jsonc"


class TestKiloRuntimeSurface:
    def test_runtime_paths_equal_registry_render(self):
        from skills_registry.generators import gen_kilo_runtime as gen
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
        """Every runtime path must exist on disk — a stale hand-frozen list
        once carried ./skills/research (never registered)."""
        paths = json.loads(
            RUNTIME_PATH.read_text(encoding="utf-8"))["skills"]["paths"]
        for p in paths:
            assert (REPO_ROOT / p).is_dir(), f"runtime path {p} is not a dir"

    def test_render_preserves_unrelated_config(self):
        """render() must replace ONLY skills.paths — the model, permission and
        indexing blocks belong to the operator, not the registry."""
        from skills_registry.generators import gen_kilo_runtime as gen
        reg = Registry.load(REGISTRY_PATH)
        before = json.loads(RUNTIME_PATH.read_text(encoding="utf-8"))
        after = json.loads(gen.render(reg))
        for key in before:
            if key != "skills":
                assert after[key] == before[key], f"{key} must be untouched"
