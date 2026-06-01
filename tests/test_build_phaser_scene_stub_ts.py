from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "game" / "build_phaser_scene_stub_ts.py"
spec = importlib.util.spec_from_file_location("build_phaser_scene_stub_ts", SCRIPT)
assert spec and spec.loader
build_phaser_scene_stub_ts = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = build_phaser_scene_stub_ts
spec.loader.exec_module(build_phaser_scene_stub_ts)


def sample_payload() -> dict:
    return {
        "summary": {"manifest_count": 1, "preload_count": 1, "animation_count": 1},
        "preload": [
            {
                "kind": "spritesheet",
                "key": "character.captain.captain-trader-01.idle",
                "path": "game-assets/characters/captain/captain-trader-01/idle/captain-trader-01--idle--8dir--64.png",
                "frame_config": {"frameWidth": 64, "frameHeight": 64},
            }
        ],
        "animations": [
            {
                "key": "captain-trader-01:idle:south",
                "texture_key": "character.captain.captain-trader-01.idle",
            }
        ],
    }


def write_payload(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_render_scene_stub_includes_loader_calls_and_preview():
    text = build_phaser_scene_stub_ts.render_scene_stub(
        sample_payload(),
        scene_name="TradingRpgAssetScene",
        scene_key="trading-rpg-assets",
        module_import="./trading_rpg_assets",
    )

    assert 'import { preloadPhaserAssets, registerPhaserAnimations } from "./trading_rpg_assets";' in text
    assert "export const tradingRpgAssetsSceneKey = " in text
    assert "export class TradingRpgAssetScene extends Phaser.Scene" in text
    assert "preloadPhaserAssets(this);" in text
    assert "registerPhaserAnimations(this);" in text
    assert 'private readonly previewTextureKey = "character.captain.captain-trader-01.idle";' in text
    assert 'this.previewSprite = this.add.sprite(this.cameras.main.centerX, this.cameras.main.centerY, this.previewTextureKey);' in text
    assert 'this.previewSprite.play(this.previewAnimationKey);' in text


def test_render_scene_stub_handles_payload_without_preview_assets():
    text = build_phaser_scene_stub_ts.render_scene_stub(
        {"preload": [], "animations": []},
        scene_name="EmptyScene",
        scene_key="empty-scene",
        module_import="./empty_assets",
    )

    assert "private readonly previewTextureKey" not in text
    assert "this.previewSprite = this.add.sprite" not in text
    assert "registerPhaserAnimations(this);" in text


def test_cli_renders_typescript_from_file(tmp_path):
    payload = tmp_path / "payload.json"
    write_payload(payload, sample_payload())

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(payload),
            "--scene-name",
            "TradingRpgAssetScene",
            "--scene-key",
            "trading-rpg-assets",
            "--module-import",
            "./trading_rpg_assets",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert "TradingRpgAssetScene" in result.stdout
    assert "tradingRpgAssetsSceneKey" in result.stdout


def test_cli_supports_stdin():
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "-",
            "--scene-name",
            "TradingRpgAssetScene",
            "--scene-key",
            "trading-rpg-assets",
            "--module-import",
            "./trading_rpg_assets",
        ],
        input=json.dumps(sample_payload(), ensure_ascii=False),
        check=True,
        capture_output=True,
        text=True,
    )

    assert "preloadPhaserAssets(this);" in result.stdout
    assert "registerPhaserAnimations(this);" in result.stdout
