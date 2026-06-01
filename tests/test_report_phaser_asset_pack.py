from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "game" / "report_phaser_asset_pack.py"
spec = importlib.util.spec_from_file_location("report_phaser_asset_pack", SCRIPT)
assert spec and spec.loader
report_phaser_asset_pack = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = report_phaser_asset_pack
spec.loader.exec_module(report_phaser_asset_pack)


def write_manifest(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def valid_manifest(root: Path, asset_path: str = "assets/captain-idle.png") -> dict:
    (root / asset_path).parent.mkdir(parents=True, exist_ok=True)
    (root / asset_path).write_bytes(b"png")
    return {
        "asset_key": "character.captain.captain-trader-01.base.8dir.64",
        "asset_type": "character",
        "files": {"spritesheets": {"idle": asset_path}},
        "phaser": {
            "texture_key": "character.captain.captain-trader-01",
            "frame_config": {"frameWidth": 64, "frameHeight": 64},
            "animations": [{"key": "captain-trader-01:idle:south", "sheet": "idle"}],
        },
    }


def test_analyze_pack_reports_ready_for_valid_manifest(tmp_path):
    manifest = tmp_path / "manifests" / "captain.json"
    write_manifest(manifest, valid_manifest(tmp_path))

    report = report_phaser_asset_pack.analyze_pack(tmp_path / "manifests", root=tmp_path, check_files=True)

    assert report["status"] == "ready"
    assert report["summary"]["manifest_count"] == 1
    assert report["summary"]["preload_count"] == 1
    assert report["issues"] == []


def test_analyze_pack_reports_missing_asset_file_when_requested(tmp_path):
    manifest = tmp_path / "manifests" / "captain.json"
    payload = valid_manifest(tmp_path, asset_path="assets/missing.png")
    (tmp_path / "assets" / "missing.png").unlink()
    write_manifest(manifest, payload)

    report = report_phaser_asset_pack.analyze_pack(tmp_path / "manifests", root=tmp_path, check_files=True)

    assert report["status"] == "blocked"
    assert "missing asset file" in report["issues"][0]


def test_analyze_pack_reports_duplicate_animation_keys(tmp_path):
    one = tmp_path / "manifests" / "one.json"
    two = tmp_path / "manifests" / "two.json"
    payload = valid_manifest(tmp_path)
    write_manifest(one, payload)
    write_manifest(two, {**payload, "asset_key": "character.captain.other.base.8dir.64"})

    report = report_phaser_asset_pack.analyze_pack(tmp_path / "manifests", root=tmp_path)

    assert report["status"] == "blocked"
    assert "duplicate animation key: captain-trader-01:idle:south" in report["issues"]


def test_analyze_pack_reports_invalid_nested_shape_without_crashing(tmp_path):
    manifest = tmp_path / "manifests" / "broken.json"
    write_manifest(
        manifest,
        {
            "asset_key": "character.captain.broken.base.8dir.64",
            "files": {"spritesheets": {"idle": "assets/missing.png"}},
            "phaser": ["not", "an", "object"],
        },
    )

    report = report_phaser_asset_pack.analyze_pack(tmp_path / "manifests", root=tmp_path)

    assert report["status"] == "blocked"
    assert any("invalid manifest object shape" in issue for issue in report["issues"])


def test_format_markdown_includes_status_and_manifest_table(tmp_path):
    manifest = tmp_path / "manifests" / "captain.json"
    write_manifest(manifest, valid_manifest(tmp_path))
    report = report_phaser_asset_pack.analyze_pack(tmp_path / "manifests", root=tmp_path)

    text = report_phaser_asset_pack.format_markdown(report)

    assert "Status: **READY**" in text
    assert "| Manifests | 1 |" in text
    assert "captain-trader-01" in text


def test_cli_json_and_fail_on_issues(tmp_path):
    manifest = tmp_path / "manifests" / "captain.json"
    write_manifest(manifest, {"asset_key": ""})

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(tmp_path / "manifests"),
            "--root",
            str(tmp_path),
            "--format",
            "json",
            "--fail-on-issues",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["status"] == "blocked"
