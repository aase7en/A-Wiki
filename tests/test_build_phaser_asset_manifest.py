from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "game" / "build_phaser_asset_manifest.py"
spec = importlib.util.spec_from_file_location("build_phaser_asset_manifest", SCRIPT)
assert spec and spec.loader
build_phaser_asset_manifest = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = build_phaser_asset_manifest
spec.loader.exec_module(build_phaser_asset_manifest)


def write_manifest(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_discover_manifest_files_supports_single_file_and_directory(tmp_path):
    one = tmp_path / "manifests" / "a.json"
    two = tmp_path / "manifests" / "nested" / "b.json"
    write_manifest(one, {"asset_key": "one"})
    write_manifest(two, {"asset_key": "two"})

    single = build_phaser_asset_manifest.discover_manifest_files(one)
    many = build_phaser_asset_manifest.discover_manifest_files(tmp_path / "manifests")

    assert single == [one]
    assert many == [one, two]


def test_build_export_creates_preload_entries_and_animation_texture_keys(tmp_path):
    manifest = tmp_path / "manifests" / "captain.json"
    write_manifest(
        manifest,
        {
            "asset_key": "character.captain.captain-trader-01.base.8dir.64",
            "asset_type": "character",
            "files": {
                "spritesheets": {
                    "idle": "characters/captain/captain-trader-01/idle/captain-trader-01--idle--8dir--64.png",
                    "walk": "characters/captain/captain-trader-01/walk/captain-trader-01--walk--8dir--64.png",
                }
            },
            "phaser": {
                "texture_key": "character.captain.captain-trader-01",
                "frame_config": {"frameWidth": 64, "frameHeight": 64},
                "animations": [
                    {"key": "captain-trader-01:idle:south", "sheet": "idle"},
                    {"key": "captain-trader-01:walk:south", "sheet": "walk", "start": 0, "end": 5, "frameRate": 8, "repeat": -1},
                ],
            },
            "tags": ["captain"],
        },
    )

    export = build_phaser_asset_manifest.build_export([manifest], root=tmp_path)

    assert [item["key"] for item in export["preload"]] == [
        "character.captain.captain-trader-01.idle",
        "character.captain.captain-trader-01.walk",
    ]
    assert export["preload"][0]["frame_config"] == {"frameWidth": 64, "frameHeight": 64}
    assert export["animations"][0]["texture_key"] == "character.captain.captain-trader-01.idle"
    assert export["animations"][1]["end"] == 5


def test_build_export_handles_non_animated_object_manifest(tmp_path):
    manifest = tmp_path / "manifests" / "ship.json"
    write_manifest(
        manifest,
        {
            "asset_key": "object.ship.sloop-01.base.8dir.96",
            "asset_type": "object",
            "files": {},
            "phaser": {
                "texture_key": "object.ship.sloop-01",
                "frame_config": {"frameWidth": 96, "frameHeight": 96},
                "animations": [],
            },
        },
    )

    export = build_phaser_asset_manifest.build_export([manifest], root=tmp_path)

    assert export["preload"] == []
    assert export["animations"] == []
    assert export["manifests"][0]["asset_key"] == "object.ship.sloop-01.base.8dir.96"


def test_cli_emits_json_for_directory(tmp_path):
    manifest = tmp_path / "manifests" / "captain.json"
    write_manifest(
        manifest,
        {
            "asset_key": "character.captain.captain-trader-01.base.8dir.64",
            "files": {
                "spritesheets": {
                    "idle": "characters/captain/captain-trader-01/idle/captain-trader-01--idle--8dir--64.png"
                }
            },
            "phaser": {
                "texture_key": "character.captain.captain-trader-01",
                "frame_config": {"frameWidth": 64, "frameHeight": 64},
                "animations": [{"key": "captain-trader-01:idle:south", "sheet": "idle"}],
            },
        },
    )

    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(tmp_path / "manifests"), "--root", str(tmp_path)],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(result.stdout)
    assert payload["summary"]["manifest_count"] == 1
    assert payload["animations"][0]["key"] == "captain-trader-01:idle:south"
