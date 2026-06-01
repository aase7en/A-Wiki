from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "game" / "build_phaser_loader_ts.py"
spec = importlib.util.spec_from_file_location("build_phaser_loader_ts", SCRIPT)
assert spec and spec.loader
build_phaser_loader_ts = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = build_phaser_loader_ts
spec.loader.exec_module(build_phaser_loader_ts)


def write_payload(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def sample_payload() -> dict:
    return {
        "summary": {"manifest_count": 1, "preload_count": 2, "animation_count": 2},
        "manifests": [
            {
                "path": "game-assets/manifests/characters/captain-trader-01.json",
                "asset_key": "character.captain.captain-trader-01.base.8dir.64",
                "asset_type": "character",
                "texture_key": "character.captain.captain-trader-01",
            }
        ],
        "preload": [
            {
                "kind": "spritesheet",
                "key": "character.captain.captain-trader-01.idle",
                "path": "game-assets/characters/captain/captain-trader-01/idle/captain-trader-01--idle--8dir--64.png",
                "frame_config": {"frameWidth": 64, "frameHeight": 64},
                "asset_key": "character.captain.captain-trader-01.base.8dir.64",
                "sheet": "idle",
            },
            {
                "kind": "spritesheet",
                "key": "character.captain.captain-trader-01.walk",
                "path": "game-assets/characters/captain/captain-trader-01/walk/captain-trader-01--walk--8dir--64.png",
                "frame_config": {"frameWidth": 64, "frameHeight": 64},
                "asset_key": "character.captain.captain-trader-01.base.8dir.64",
                "sheet": "walk",
            },
        ],
        "animations": [
            {
                "key": "captain-trader-01:idle:south",
                "sheet": "idle",
                "texture_key": "character.captain.captain-trader-01.idle",
                "asset_key": "character.captain.captain-trader-01.base.8dir.64",
            },
            {
                "key": "captain-trader-01:walk:south",
                "sheet": "walk",
                "texture_key": "character.captain.captain-trader-01.walk",
                "asset_key": "character.captain.captain-trader-01.base.8dir.64",
                "start": 0,
                "end": 5,
                "frameRate": 8,
                "repeat": -1,
            },
        ],
    }


def test_render_typescript_includes_preload_and_animation_functions():
    text = build_phaser_loader_ts.render_typescript(sample_payload(), module_name="captain_assets")

    assert "export const captain_assetsSummary" in text
    assert "export function preloadPhaserAssets" in text
    assert 'scene.load.spritesheet("character.captain.captain-trader-01.idle"' in text
    assert 'key: "captain-trader-01:walk:south"' in text
    assert 'scene.anims.generateFrameNumbers("character.captain.captain-trader-01.walk"' in text


def test_render_typescript_skips_duplicate_animation_registration():
    text = build_phaser_loader_ts.render_typescript(sample_payload())

    assert 'if (scene.anims.exists("captain-trader-01:idle:south"))' in text
    assert 'if (scene.anims.exists("captain-trader-01:walk:south"))' in text


def test_cli_renders_typescript_from_json_file(tmp_path):
    payload_file = tmp_path / "payload.json"
    write_payload(payload_file, sample_payload())

    result = subprocess.run(
        [sys.executable, str(SCRIPT), str(payload_file), "--module-name", "captain_assets"],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "export const captain_assetsSummary" in result.stdout
    assert 'scene.load.spritesheet("character.captain.captain-trader-01.walk"' in result.stdout


def test_cli_supports_stdin(tmp_path):
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "-", "--module-name", "captain_assets"],
        input=json.dumps(sample_payload(), ensure_ascii=False),
        check=True,
        capture_output=True,
        text=True,
    )

    assert "captain_assetsSummary" in result.stdout
    assert "registerPhaserAnimations" in result.stdout
