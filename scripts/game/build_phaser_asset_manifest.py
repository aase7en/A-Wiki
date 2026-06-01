#!/usr/bin/env python3
"""Build a Phaser-friendly preload/animation manifest from asset manifests."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]


class ManifestValidationError(ValueError):
    """Raised when one or more asset manifests cannot produce valid Phaser output."""

    def __init__(self, issues: list[str]) -> None:
        super().__init__("\n".join(issues))
        self.issues = issues


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


def validate_manifest(path: Path, manifest: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    asset_key = str(manifest.get("asset_key") or "")
    phaser = manifest.get("phaser") or {}
    files = manifest.get("files") or {}
    spritesheets = files.get("spritesheets") or {}
    animations = phaser.get("animations") or []
    frame_config = phaser.get("frame_config") or {}
    texture_key = str(phaser.get("texture_key") or "")

    prefix = rel(path, REPO_ROOT)
    if not asset_key:
        issues.append(f"{prefix}: missing asset_key")
    if (spritesheets or animations) and not texture_key:
        issues.append(f"{prefix}: phaser.texture_key is required when spritesheets or animations exist")
    if spritesheets:
        for field in ("frameWidth", "frameHeight"):
            value = frame_config.get(field)
            if not isinstance(value, int) or value <= 0:
                issues.append(f"{prefix}: phaser.frame_config.{field} must be a positive integer")
    if not isinstance(spritesheets, dict):
        issues.append(f"{prefix}: files.spritesheets must be an object")
        spritesheets = {}
    if not isinstance(animations, list):
        issues.append(f"{prefix}: phaser.animations must be a list")
        animations = []

    for index, animation in enumerate(animations):
        if not isinstance(animation, dict):
            issues.append(f"{prefix}: phaser.animations[{index}] must be an object")
            continue
        if not animation.get("key"):
            issues.append(f"{prefix}: phaser.animations[{index}].key is required")
        sheet = animation.get("sheet")
        if sheet and sheet not in spritesheets:
            issues.append(f"{prefix}: animation {animation.get('key', index)!r} references missing sheet {sheet!r}")
    return issues


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


def find_duplicates(values: list[str]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return duplicates


def validate_export(payload: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    asset_keys = [item.get("asset_key", "") for item in payload.get("manifests", []) if item.get("asset_key")]
    preload_keys = [item.get("key", "") for item in payload.get("preload", []) if item.get("key")]
    animation_keys = [item.get("key", "") for item in payload.get("animations", []) if item.get("key")]

    for duplicate in sorted(find_duplicates(asset_keys)):
        issues.append(f"duplicate asset_key: {duplicate}")
    for duplicate in sorted(find_duplicates(preload_keys)):
        issues.append(f"duplicate preload key: {duplicate}")
    for duplicate in sorted(find_duplicates(animation_keys)):
        issues.append(f"duplicate animation key: {duplicate}")
    return issues


def build_export(files: list[Path], root: Path, validate: bool = True) -> dict[str, Any]:
    manifests: list[dict[str, Any]] = []
    preload: list[dict[str, Any]] = []
    animations: list[dict[str, Any]] = []
    issues: list[str] = []

    for path in files:
        manifest = load_manifest(path)
        if validate:
            issues.extend(validate_manifest(path, manifest))
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

    payload = {
        "summary": {
            "manifest_count": len(files),
            "preload_count": len(preload),
            "animation_count": len(animations),
        },
        "manifests": manifests,
        "preload": preload,
        "animations": animations,
    }
    if validate:
        issues.extend(validate_export(payload))
        if issues:
            raise ManifestValidationError(issues)
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build Phaser preload/animation JSON from asset manifests.")
    parser.add_argument("target", help="Manifest JSON file or directory containing manifest JSON files.")
    parser.add_argument("--root", default=str(REPO_ROOT), help="Root path used to relativize output paths.")
    parser.add_argument("--no-validate", action="store_true", help="Skip manifest and duplicate-key validation.")
    args = parser.parse_args(argv)

    target = Path(args.target).resolve()
    root = Path(args.root).resolve()
    try:
        payload = build_export(discover_manifest_files(target), root=root, validate=not args.no_validate)
    except ManifestValidationError as exc:
        for issue in exc.issues:
            print(f"[ERROR] {issue}", file=sys.stderr)
        return 2
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
