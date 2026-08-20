"""Security scanner pattern-source contract (incident 2026-08-20, PR #17 CI).

Root cause this pins: `_scan_staged_diff._load_patterns()` silently falls
back to a small builtin pattern set when PyYAML is missing / the yaml file
is absent / malformed. A CI runner without deps therefore scanned with a
DIFFERENT pattern set → every baseline key mismatched → 20 phantom "new"
findings and a red PR, with no hint of the real cause.

Contract after this fix:
  - strict=True (CI mode): ANY pattern-source problem raises
    PatternSourceUnavailable — the scan fails LOUD, never quietly degrades.
  - strict=False (hook runtime): fallback survives (hooks must not wedge a
    machine), but it WARNS on stderr — never silent again.
"""
from __future__ import annotations

import builtins
import importlib
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "hooks"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "security"))

import _scan_staged_diff as sd  # noqa: E402


@pytest.fixture()
def no_yaml(monkeypatch):
    """Make `import yaml` raise ImportError like a dependency-less env."""
    real_import = builtins.__import__

    def fake_import(name, *a, **k):
        if name == "yaml":
            raise ImportError("no module named 'yaml' (test fixture)")
        return real_import(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", fake_import)


class TestStrictCiModeFailsLoud:
    def test_missing_yaml_raises_in_strict_mode(self, no_yaml):
        with pytest.raises(sd.PatternSourceUnavailable):
            sd._load_patterns(strict=True)

    def test_missing_patterns_file_raises_in_strict_mode(self, monkeypatch):
        monkeypatch.setattr(sd, "PATTERNS_FILE", Path("Z:/definitely/missing.yaml"))
        with pytest.raises(sd.PatternSourceUnavailable):
            sd._load_patterns(strict=True)

    def test_malformed_yaml_raises_in_strict_mode(self, monkeypatch, tmp_path):
        bad = tmp_path / "bad.yaml"
        bad.write_text("secret_patterns: [unclosed", encoding="utf-8")
        monkeypatch.setattr(sd, "PATTERNS_FILE", bad)
        with pytest.raises(sd.PatternSourceUnavailable):
            sd._load_patterns(strict=True)

    def test_empty_yaml_patterns_raise_in_strict_mode(self, monkeypatch, tmp_path):
        empty = tmp_path / "empty.yaml"
        empty.write_text("secret_patterns: []\nmachine_path_patterns: []\n",
                         encoding="utf-8")
        monkeypatch.setattr(sd, "PATTERNS_FILE", empty)
        with pytest.raises(sd.PatternSourceUnavailable):
            sd._load_patterns(strict=True)


class TestRuntimeFallbackIsLoudNotSilent:
    def test_fallback_returns_builtin_with_warning(self, no_yaml, capsys):
        patterns = sd._load_patterns(strict=False)
        names = {name for name, _re, _al in patterns}
        assert "sk- key" in names  # builtin subset survived
        err = capsys.readouterr().err
        assert "pattern source" in err.lower(), (
            "runtime fallback must WARN — a silent pattern-set swap is how "
            "the 2026-08-20 CI incident happened")

    def test_strict_mode_with_healthy_source_returns_full_set(self):
        patterns = sd._load_patterns(strict=True)
        names = {name for name, _re, _al in patterns}
        # the yaml source is materially larger than the builtin subset
        assert len(patterns) > 10
        assert any("macOS" in n or "home" in n for n in names)


class TestScanRepoCiWiresStrictMode:
    def test_scan_repo_uses_strict_loader(self):
        src = (REPO_ROOT / "scripts" / "security" / "scan_repo.py").read_text(encoding="utf-8")
        assert "strict=True" in src or "strict=args.ci" in src, (
            "scan_repo --ci must load patterns in strict mode")
