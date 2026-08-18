#!/usr/bin/env python3
"""awiki memory status — read-only Memory Plane inspection (Phase 5).

Reports, per project adapter: layer policy scopes, L2 store availability,
L5 experiment count, promotion config. Deterministic; never writes.
Exit 0 = adapter valid; 1 = invalid/missing adapter.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

import memory_layers as ml
import project_memory as pm
import experiment_memory as em


def status(project_root: Path, data_root: Path | None = None) -> dict:
    info: dict = {"project_root": str(project_root)}
    try:
        store = pm.ProjectMemoryStore(project_root, data_root=data_root)
    except pm.AdapterInvalid as e:
        info["adapter_valid"] = False
        info["error"] = str(e)
        return info

    info["adapter_valid"] = True
    info["project_id"] = store.project_id
    info["scopes"] = store.scopes
    info["privacy"] = store.privacy
    info["trust"] = store.trust
    info["memory_dir_available"] = store.memory_dir.is_dir()
    info["l2_entries"] = 0
    if store.scopes.get("project") and (store.memory_dir / "entries.jsonl").is_file():
        info["l2_entries"] = sum(
            1 for line in (store.memory_dir / "entries.jsonl")
            .read_text(encoding="utf-8").splitlines() if line.strip())
    exp_root = store._root / "projects" / store.project_id / "experiments"
    info["l5_experiments"] = len([d for d in exp_root.iterdir()]) if exp_root.is_dir() else 0
    info["promotion"] = {"default_mode": "manual-with-evidence", "dry_run_first": True}
    info["layers"] = {k: v["durability"] for k, v in ml.LAYER_POLICY.items()}
    return info


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only Memory Plane status")
    parser.add_argument("project_root", nargs="?", type=Path, default=Path("."))
    parser.add_argument("--data-root", type=Path, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    info = status(args.project_root.resolve(), args.data_root)
    if args.json:
        print(json.dumps(info, ensure_ascii=False, indent=2, default=str))
    else:
        for key, value in info.items():
            print(f"{key:22}: {value}")
    return 0 if info.get("adapter_valid") else 1


if __name__ == "__main__":
    sys.exit(main())
