#!/usr/bin/env python3
"""Generate Phaser asset payload JSON, loader TS, and scene stub TS in one command."""
from __future__ import annotations

import argparse
import shutil
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent


def load_module(filename: str, module_name: str):
    path = SCRIPT_DIR / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    if not spec or not spec.loader:
        raise RuntimeError(f"could not load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


build_manifest = load_module("build_phaser_asset_manifest.py", "build_phaser_asset_manifest")
build_loader = load_module("build_phaser_loader_ts.py", "build_phaser_loader_ts")
build_scene = load_module("build_phaser_scene_stub_ts.py", "build_phaser_scene_stub_ts")


def bootstrap_pack(
    target: Path,
    out_dir: Path,
    root: Path,
    module_name: str,
    scene_name: str,
    scene_key: str,
    module_import: str,
    copy_to_project: Path | None = None,
) -> dict[str, Path]:
    files = build_manifest.discover_manifest_files(target)
    payload = build_manifest.build_export(files, root=root)
    payload_text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    loader_text = build_loader.render_typescript(payload, module_name=module_name)
    scene_text = build_scene.render_scene_stub(
        payload,
        scene_name=scene_name,
        scene_key=scene_key,
        module_import=module_import,
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    payload_path = out_dir / f"{module_name}.json"
    loader_path = out_dir / f"{module_name}.ts"
    scene_path = out_dir / f"{scene_name}.ts"

    payload_path.write_text(payload_text, encoding="utf-8")
    loader_path.write_text(loader_text, encoding="utf-8")
    scene_path.write_text(scene_text, encoding="utf-8")

    result = {
        "payload_path": payload_path,
        "loader_path": loader_path,
        "scene_path": scene_path,
    }
    if copy_to_project is not None:
        copy_to_project.mkdir(parents=True, exist_ok=True)
        project_payload_path = copy_to_project / payload_path.name
        project_loader_path = copy_to_project / loader_path.name
        project_scene_path = copy_to_project / scene_path.name
        shutil.copy2(payload_path, project_payload_path)
        shutil.copy2(loader_path, project_loader_path)
        shutil.copy2(scene_path, project_scene_path)
        barrel_path = copy_to_project / "index.ts"
        barrel_path.write_text(
            f'export * from "./{loader_path.stem}";\nexport * from "./{scene_path.stem}";\n',
            encoding="utf-8",
        )
        result.update(
            {
                "project_payload_path": project_payload_path,
                "project_loader_path": project_loader_path,
                "project_scene_path": project_scene_path,
                "project_barrel_path": barrel_path,
            }
        )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bootstrap Phaser asset payload, loader, and scene files.")
    parser.add_argument("target", help="Manifest JSON file or directory.")
    parser.add_argument("--out-dir", required=True, help="Directory where generated files will be written.")
    parser.add_argument("--root", default=".", help="Root path used to relativize manifest paths.")
    parser.add_argument("--module-name", default="phaser_assets", help="Base filename and summary const prefix for generated files.")
    parser.add_argument("--scene-name", default="GeneratedAssetScene", help="TypeScript class name for generated scene stub.")
    parser.add_argument("--scene-key", default="generated-asset-scene", help="Phaser scene key.")
    parser.add_argument("--module-import", default="./phaser_assets", help="Import path used by generated scene stub.")
    parser.add_argument("--copy-to-project", help="Optional directory that receives copies of the generated files plus index.ts barrel.")
    args = parser.parse_args(argv)

    result = bootstrap_pack(
        target=Path(args.target).resolve(),
        out_dir=Path(args.out_dir).resolve(),
        root=Path(args.root).resolve(),
        module_name=args.module_name,
        scene_name=args.scene_name,
        scene_key=args.scene_key,
        module_import=args.module_import,
        copy_to_project=Path(args.copy_to_project).resolve() if args.copy_to_project else None,
    )
    print(f"[OK] payload -> {result['payload_path']}")
    print(f"[OK] loader  -> {result['loader_path']}")
    print(f"[OK] scene   -> {result['scene_path']}")
    if "project_loader_path" in result:
        print(f"[OK] project payload -> {result['project_payload_path']}")
        print(f"[OK] project loader  -> {result['project_loader_path']}")
        print(f"[OK] project scene   -> {result['project_scene_path']}")
        print(f"[OK] project barrel  -> {result['project_barrel_path']}")
    return 0



if __name__ == "__main__":
    sys.exit(main())
