#!/usr/bin/env python3
"""Build a Phaser-friendly preload/animation manifest from asset manifests."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def discover_manifest_files(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    if not target.exists():
        raise FileNotFoundError(f"manifest path not found: {target}")
    return sorted(path for path in target.rglob("*.json") if path.is_file())


def load_manifest(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"manifest must be a JSON object: {path}")
    return data


def build_preload_entries(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    phaser = manifest.get("phaser") or {}
    texture_key = phaser.get("texture_key")
    frame_config = phaser.get("frame_config") or {}
    spritesheets = ((manifest.get("files") or {}).get("spritesheets") or {})

    if not texture_key:
        return []

    entries: list[dict[str, Any]] = []
    for sheet_name, asset_path in sorted(spritesheets.items()):
        entries.append(
            {
                "kind": "spritesheet",
                "key": f"{texture_key}.{sheet_name}",
                "path": asset_path,
                "frame_config": frame_config,
                "asset_key": manifest.get("asset_key", ""),
                "sheet": sheet_name,
            }
        )
    return entries


def build_animation_entries(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    phaser = manifest.get("phaser") or {}
    texture_key = phaser.get("texture_key")
    animations = phaser.get("animations") or []

    if not texture_key:
        return []

    entries: list[dict[str, Any]] = []
    for animation in animations:
        if not isinstance(animation, dict) or not animation.get("key"):
            continue
        sheet = animation.get("sheet")
        resolved_texture_key = f"{texture_key}.{sheet}" if sheet else texture_key
        entry = dict(animation)
        entry["texture_key"] = resolved_texture_key
        entry["asset_key"] = manifest.get("asset_key", "")
        entries.append(entry)
    return entries


def build_export(files: list[Path], root: Path) -> dict[str, Any]:
    manifests: list[dict[str, Any]] = []
    preload: list[dict[str, Any]] = []
    animations: list[dict[str, Any]] = []

    for path in files:
        manifest = load_manifest(path)
        manifests.append(
            {
                "path": rel(path, root),
                "asset_key": manifest.get("asset_key", ""),
                "asset_type": manifest.get("asset_type", ""),
                "texture_key": ((manifest.get("phaser") or {}).get("texture_key") or ""),
            }
        )
        preload.extend(build_preload_entries(manifest))
        animations.extend(build_animation_entries(manifest))

    return {
        "summary": {
            "manifest_count": len(files),
            "preload_count": len(preload),
            "animation_count": len(animations),
        },
        "manifests": manifests,
        "preload": preload,
        "animations": animations,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build Phaser preload/animation JSON from asset manifests.")
    parser.add_argument("target", help="Manifest JSON file or directory containing manifest JSON files.")
    parser.add_argument("--root", default=str(REPO_ROOT), help="Root path used to relativize output paths.")
    args = parser.parse_args(argv)

    target = Path(args.target).resolve()
    root = Path(args.root).resolve()
    payload = build_export(discover_manifest_files(target), root=root)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
