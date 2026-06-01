#!/usr/bin/env python3
"""Write a starter Phaser asset manifest from a stable asset key."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


DIRECTION_LABELS = {
    1: ["south"],
    4: ["south", "west", "east", "north"],
    8: ["south", "south-east", "east", "north-east", "north", "north-west", "west", "south-west"],
}


def parse_size(raw: str) -> tuple[int, int]:
    if "x" in raw:
        left, right = raw.split("x", 1)
        return int(left), int(right)
    size = int(raw)
    return size, size


def infer_directions(parts: list[str]) -> int:
    for part in parts:
        if part.endswith("dir") and part[:-3].isdigit():
            return int(part[:-3])
    return 1


def build_template(asset_key: str, actions: list[str], tags: list[str]) -> dict:
    parts = asset_key.split(".")
    if len(parts) < 5:
        raise ValueError("asset_key must look like domain.family.name.variant....size")
    asset_type = parts[0]
    family = parts[1]
    name = parts[2]
    variant = parts[3]
    directions = infer_directions(parts)
    width, height = parse_size(parts[-1])
    texture_key = ".".join([asset_type, family, name])
    direction_suffix = f"{directions}dir" if directions > 1 else "1dir"

    spritesheets = {}
    animations = []
    for action in actions:
        spritesheets[action] = (
            f"game-assets/{asset_type}s/{family}/{name}/{action}/"
            f"{name}--{action}--{direction_suffix}--{parts[-1]}.png"
        )
        direction_label = DIRECTION_LABELS.get(directions, ["south"])[0]
        animations.append({"key": f"{name}:{action}:{direction_label}", "sheet": action})

    return {
        "asset_key": asset_key,
        "asset_type": asset_type,
        "name": name,
        "variant": variant,
        "actions": actions,
        "directions": directions,
        "frame_size": {"w": width, "h": height},
        "source": {
            "provider": "pixellab",
            "endpoint": "",
            "resource_id": "",
            "job_id": "",
        },
        "files": {"spritesheets": spritesheets},
        "phaser": {
            "texture_key": texture_key,
            "atlas": False,
            "frame_config": {"frameWidth": width, "frameHeight": height},
            "animations": animations,
        },
        "tags": tags,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write a starter Phaser asset manifest from an asset key.")
    parser.add_argument("output", help="Path to the manifest JSON file to create.")
    parser.add_argument("--asset-key", required=True, help="Stable asset key, e.g. character.captain.captain-trader-01.base.8dir.64")
    parser.add_argument("--action", action="append", default=[], help="Action name to pre-seed, e.g. idle or walk. Repeatable.")
    parser.add_argument("--tag", action="append", default=[], help="Tag to pre-seed. Repeatable.")
    args = parser.parse_args(argv)

    payload = build_template(args.asset_key, actions=args.action or ["idle"], tags=args.tag)
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[OK] manifest template -> {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
