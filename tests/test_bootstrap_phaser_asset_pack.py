from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "game" / "bootstrap_phaser_asset_pack.py"
spec = importlib.util.spec_from_file_location("bootstrap_phaser_asset_pack", SCRIPT)
assert spec and spec.loader
bootstrap_phaser_asset_pack = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = bootstrap_phaser_asset_pack
spec.loader.exec_module(bootstrap_phaser_asset_pack)


def write_manifest(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def sample_manifest() -> dict:
    return {
        "asset_key": "character.captain.captain-trader-01.base.8dir.64",
        "asset_type": "character",
        "files": {
            "spritesheets": {
                "idle": "game-assets/characters/captain/captain-trader-01/idle/captain-trader-01--idle--8dir--64.png"
            }
        },
        "phaser": {
            "texture_key": "character.captain.captain-trader-01",
            "frame_config": {"frameWidth": 64, "frameHeight": 64},
            "animations": [{"key": "captain-trader-01:idle:south", "sheet": "idle"}],
        },
    }


def test_bootstrap_outputs_have_expected_names_and_content(tmp_path):
    manifests = tmp_path / "game-assets" / "manifests"
    write_manifest(manifests / "captain.json", sample_manifest())
    out_dir = tmp_path / "generated"

    result = bootstrap_phaser_asset_pack.bootstrap_pack(
        target=manifests,
        out_dir=out_dir,
        root=tmp_path,
        module_name="trading_rpg_assets",
        scene_name="TradingRpgAssetScene",
        scene_key="trading-rpg-assets",
        module_import="./trading_rpg_assets",
    )

    assert result["payload_path"].name == "trading_rpg_assets.json"
    assert result["loader_path"].name == "trading_rpg_assets.ts"
    assert result["scene_path"].name == "TradingRpgAssetScene.ts"
    assert json.loads(result["payload_path"].read_text(encoding="utf-8"))["summary"]["manifest_count"] == 1
    assert "preloadPhaserAssets" in result["loader_path"].read_text(encoding="utf-8")
    assert "TradingRpgAssetScene" in result["scene_path"].read_text(encoding="utf-8")


def test_cli_generates_three_files(tmp_path):
    manifests = tmp_path / "game-assets" / "manifests"
    write_manifest(manifests / "captain.json", sample_manifest())
    out_dir = tmp_path / "generated"

    subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(manifests),
            "--out-dir",
            str(out_dir),
            "--root",
            str(tmp_path),
            "--module-name",
            "trading_rpg_assets",
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

    assert (out_dir / "trading_rpg_assets.json").exists()
    assert (out_dir / "trading_rpg_assets.ts").exists()
    assert (out_dir / "TradingRpgAssetScene.ts").exists()
