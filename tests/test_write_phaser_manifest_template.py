from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "game" / "write_phaser_manifest_template.py"
spec = importlib.util.spec_from_file_location("write_phaser_manifest_template", SCRIPT)
assert spec and spec.loader
write_phaser_manifest_template = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = write_phaser_manifest_template
spec.loader.exec_module(write_phaser_manifest_template)


def test_build_template_infers_texture_key_frame_size_and_actions():
    payload = write_phaser_manifest_template.build_template(
        asset_key="character.captain.captain-trader-01.base.8dir.64",
        actions=["idle", "walk"],
        tags=["captain", "hero"],
    )

    assert payload["asset_type"] == "character"
    assert payload["name"] == "captain-trader-01"
    assert payload["directions"] == 8
    assert payload["frame_size"] == {"w": 64, "h": 64}
    assert payload["phaser"]["texture_key"] == "character.captain.captain-trader-01"
    assert payload["files"]["spritesheets"]["idle"].endswith("captain-trader-01--idle--8dir--64.png")
    assert payload["phaser"]["animations"][0]["key"] == "captain-trader-01:idle:south"
    assert payload["tags"] == ["captain", "hero"]


def test_cli_writes_manifest_file(tmp_path):
    out = tmp_path / "captain.json"

    subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(out),
            "--asset-key",
            "character.captain.captain-trader-01.base.8dir.64",
            "--action",
            "idle",
            "--action",
            "walk",
            "--tag",
            "captain",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["phaser"]["texture_key"] == "character.captain.captain-trader-01"
    assert payload["phaser"]["animations"][1]["key"] == "captain-trader-01:walk:south"
