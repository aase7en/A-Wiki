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
    payload = build_manifest.build_export(files, root=root, validate=False)

    if not files:
        issues.append(f"{target}: no manifest JSON files found")

    for path in files:
        manifest = build_manifest.load_manifest(path)
        issues.extend(build_manifest.validate_manifest(path, manifest))
        phaser = manifest.get("phaser") or {}
        spritesheets = ((manifest.get("files") or {}).get("spritesheets") or {})
        animations = phaser.get("animations") or []
        manifest_rows.append(
            {
                "path": build_manifest.rel(path, root),
                "asset_key": manifest.get("asset_key", ""),
                "asset_type": manifest.get("asset_type", ""),
                "texture_key": phaser.get("texture_key", ""),
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

    issues.extend(build_manifest.validate_export(payload))
    status = "ready" if not issues else "blocked"
    return {
        "status": status,
        "summary": {
            **payload.get("summary", {}),
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
