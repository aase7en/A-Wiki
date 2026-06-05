from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "game" / "sync_sunday_invest_moon_roadmap.py"
spec = importlib.util.spec_from_file_location("sync_sunday_invest_moon_roadmap", SCRIPT)
assert spec and spec.loader
sync_sunday_invest_moon_roadmap = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = sync_sunday_invest_moon_roadmap
spec.loader.exec_module(sync_sunday_invest_moon_roadmap)


def test_roadmaps_match_only_when_bytes_are_identical(tmp_path: Path):
    canonical = tmp_path / "canonical.md"
    mirror = tmp_path / "project" / "ROADMAP.md"
    canonical.write_text("# Roadmap\n", encoding="utf-8")

    assert not sync_sunday_invest_moon_roadmap.roadmaps_match(canonical, mirror)

    mirror.parent.mkdir()
    mirror.write_text("# Old roadmap\n", encoding="utf-8")
    assert not sync_sunday_invest_moon_roadmap.roadmaps_match(canonical, mirror)

    mirror.write_bytes(canonical.read_bytes())
    assert sync_sunday_invest_moon_roadmap.roadmaps_match(canonical, mirror)


def test_sync_roadmap_creates_parent_and_exact_mirror(tmp_path: Path):
    canonical = tmp_path / "canonical.md"
    mirror = tmp_path / "project" / "nested" / "ROADMAP.md"
    canonical.write_text("# Sunday Invest Moon\n", encoding="utf-8")

    sync_sunday_invest_moon_roadmap.sync_roadmap(canonical, mirror)

    assert mirror.read_bytes() == canonical.read_bytes()


def test_default_mirror_uses_pwq_root_env(tmp_path: Path, monkeypatch):
    product_root = tmp_path / "product" / "pixel-wealth-quest"
    monkeypatch.setenv("PWQ_ROOT", str(product_root))

    assert sync_sunday_invest_moon_roadmap.default_mirror() == product_root / "ROADMAP.md"


def test_cli_check_fails_on_drift_then_sync_repairs_it(tmp_path: Path):
    canonical = tmp_path / "canonical.md"
    mirror = tmp_path / "ROADMAP.md"
    canonical.write_text("# Canonical\n", encoding="utf-8")
    mirror.write_text("# Drifted\n", encoding="utf-8")
    command = [
        sys.executable,
        str(SCRIPT),
        "--canonical",
        str(canonical),
        "--mirror",
        str(mirror),
    ]

    check_before = subprocess.run(command, capture_output=True, text=True)
    sync = subprocess.run([*command, "--sync"], capture_output=True, text=True)
    check_after = subprocess.run(command, capture_output=True, text=True)

    assert check_before.returncode == 2
    assert "DRIFT" in check_before.stdout
    assert sync.returncode == 0
    assert "SYNCED" in sync.stdout
    assert check_after.returncode == 0
    assert "MATCH" in check_after.stdout
