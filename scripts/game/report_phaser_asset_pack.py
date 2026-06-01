#!/usr/bin/env python3
"""Report readiness for a Phaser asset pack built from A-Wiki asset manifests."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent


def load_build_manifest_module():
    path = SCRIPT_DIR / "build_phaser_asset_manifest.py"
    spec = importlib.util.spec_from_file_location("build_phaser_asset_manifest", path)
    if not spec or not spec.loader:
        raise RuntimeError(f"could not load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


build_manifest = load_build_manifest_module()


def resolve_asset_path(asset_path: str, root: Path) -> Path:
    path = Path(asset_path)
    if path.is_absolute():
        return path
    return root / path


def analyze_pack(target: Path, root: Path, check_files: bool = False) -> dict[str, Any]:
    files = build_manifest.discover_manifest_files(target)
    issues: list[str] = []
    warnings: list[str] = []
    manifest_rows: list[dict[str, Any]] = []
    preload_keys: list[str] = []
    animation_keys: list[str] = []
    asset_keys: list[str] = []

    if not files:
        issues.append(f"{target}: no manifest JSON files found")

    for path in files:
        try:
            manifest = build_manifest.load_manifest(path)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            issues.append(f"{build_manifest.rel(path, root)}: cannot load manifest: {exc}")
            continue

        try:
            issues.extend(build_manifest.validate_manifest(path, manifest))
        except AttributeError as exc:
            issues.append(f"{build_manifest.rel(path, root)}: invalid manifest object shape: {exc}")

        files_block = manifest.get("files") if isinstance(manifest.get("files"), dict) else {}
        phaser = manifest.get("phaser") if isinstance(manifest.get("phaser"), dict) else {}
        spritesheets = files_block.get("spritesheets") if isinstance(files_block.get("spritesheets"), dict) else {}
        animations = phaser.get("animations") if isinstance(phaser.get("animations"), list) else []
        texture_key = str(phaser.get("texture_key") or "")
        asset_key = str(manifest.get("asset_key") or "")
        if asset_key:
            asset_keys.append(asset_key)
        if texture_key:
            for sheet_name in spritesheets:
                preload_keys.append(f"{texture_key}.{sheet_name}")
        for animation in animations:
            if isinstance(animation, dict) and animation.get("key"):
                animation_keys.append(str(animation["key"]))

        manifest_rows.append(
            {
                "path": build_manifest.rel(path, root),
                "asset_key": asset_key,
                "asset_type": manifest.get("asset_type", ""),
                "texture_key": texture_key,
                "spritesheets": len(spritesheets) if isinstance(spritesheets, dict) else 0,
                "animations": len(animations) if isinstance(animations, list) else 0,
            }
        )
        if not manifest.get("asset_type"):
            warnings.append(f"{build_manifest.rel(path, root)}: asset_type is empty")
        if isinstance(spritesheets, dict) and spritesheets and not animations:
            warnings.append(f"{build_manifest.rel(path, root)}: has spritesheets but no animations")
        if check_files and isinstance(spritesheets, dict):
            for sheet_name, asset_path in spritesheets.items():
                resolved = resolve_asset_path(str(asset_path), root)
                if not resolved.exists():
                    issues.append(
                        f"{build_manifest.rel(path, root)}: missing asset file for sheet {sheet_name!r}: {asset_path}"
                    )

    for duplicate in sorted(build_manifest.find_duplicates(asset_keys)):
        issues.append(f"duplicate asset_key: {duplicate}")
    for duplicate in sorted(build_manifest.find_duplicates(preload_keys)):
        issues.append(f"duplicate preload key: {duplicate}")
    for duplicate in sorted(build_manifest.find_duplicates(animation_keys)):
        issues.append(f"duplicate animation key: {duplicate}")
    status = "ready" if not issues else "blocked"
    return {
        "status": status,
        "summary": {
            "manifest_count": len(files),
            "preload_count": len(preload_keys),
            "animation_count": len(animation_keys),
            "issue_count": len(issues),
            "warning_count": len(warnings),
            "check_files": check_files,
        },
        "issues": issues,
        "warnings": warnings,
        "manifests": manifest_rows,
    }


def format_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    status = report["status"].upper()
    lines = [
        "# Phaser Asset Pack Report",
        "",
        f"Status: **{status}**",
        "",
        "| Metric | Count |",
        "|---|---:|",
        f"| Manifests | {summary.get('manifest_count', 0)} |",
        f"| Preload entries | {summary.get('preload_count', 0)} |",
        f"| Animations | {summary.get('animation_count', 0)} |",
        f"| Issues | {summary.get('issue_count', 0)} |",
        f"| Warnings | {summary.get('warning_count', 0)} |",
        "",
    ]

    if report["issues"]:
        lines.extend(["## Issues", ""])
        lines.extend(f"- {issue}" for issue in report["issues"])
        lines.append("")
    if report["warnings"]:
        lines.extend(["## Warnings", ""])
        lines.extend(f"- {warning}" for warning in report["warnings"])
        lines.append("")

    lines.extend(
        [
            "## Manifests",
            "",
            "| Path | Asset key | Type | Texture key | Sheets | Animations |",
            "|---|---|---|---|---:|---:|",
        ]
    )
    for row in report["manifests"]:
        lines.append(
            "| {path} | `{asset_key}` | {asset_type} | `{texture_key}` | {spritesheets} | {animations} |".format(
                **row
            )
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report Phaser asset pack readiness from manifest JSON files.")
    parser.add_argument("target", help="Manifest JSON file or directory.")
    parser.add_argument("--root", default=".", help="Root path used to resolve and relativize paths.")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown", help="Output format.")
    parser.add_argument("--check-files", action="store_true", help="Verify spritesheet file paths exist under --root.")
    parser.add_argument("--fail-on-issues", action="store_true", help="Exit non-zero when the report status is blocked.")
    args = parser.parse_args(argv)

    report = analyze_pack(
        target=Path(args.target).resolve(),
        root=Path(args.root).resolve(),
        check_files=args.check_files,
    )
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(format_markdown(report))
    return 2 if args.fail_on_issues and report["status"] != "ready" else 0


if __name__ == "__main__":
    sys.exit(main())
