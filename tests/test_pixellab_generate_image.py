from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "game" / "pixellab_generate_image.py"
spec = importlib.util.spec_from_file_location("pixellab_generate_image", SCRIPT)
assert spec and spec.loader
pixellab_generate_image = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = pixellab_generate_image
spec.loader.exec_module(pixellab_generate_image)


def test_icon_payload_forces_small_transparent_medium_pixel_art():
    payload = pixellab_generate_image.build_payload(
        description="a tiny sensor",
        negative="text",
        size=256,
        no_background=False,
        view=None,
        text_guidance=8.0,
        seed=42,
        icon=True,
    )

    assert payload["image_size"] == {"width": 64, "height": 64}
    assert payload["no_background"] is True
    assert payload["detail"] == "medium detail"
    assert "pixelation_style" not in payload
    assert payload["negative_description"] == "text"
    assert payload["seed"] == 42


def test_regular_payload_keeps_requested_size_without_icon_style():
    payload = pixellab_generate_image.build_payload(
        description="a room",
        negative="",
        size=320,
        no_background=False,
        view="high top-down",
        text_guidance=7.5,
        seed=None,
        icon=False,
    )

    assert payload["image_size"] == {"width": 320, "height": 320}
    assert payload["no_background"] is False
    assert payload["view"] == "high top-down"
    assert "pixelation_style" not in payload
