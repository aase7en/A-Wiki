#!/usr/bin/env python3
"""awiki memory status — read-only Memory Plane inspection (Phase 5).

Reports, per project adapter: layer policy scopes, L2 store availability,
L5 experiment count, promotion config. Deterministic; NEVER writes —
R-P5-005: storage resolution is read-only (no ~/.a-wiki-data fallback
creation) and the report emits no absolute/private machine paths.
Storage-resolution failures become deterministic JSON fields, never tracebacks.
Exit 0 = adapter valid (storage issues reported in JSON); 1 = invalid/missing adapter.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "project"))

import memory_layers as ml
import project_memory as pm
import experiment_memory as em


def status(project_root: Path, data_root: Path | None = None) -> dict:
    # R-P5-005: no resolved/absolute project path in the report — identity
    # is the adapter's project id, never a machine path.
    info: dict = {"project_id": None, "adapter_valid": False, "storage_ok": True}
    try:
        store = pm.ProjectMemoryStore(project_root, data_root=data_root, read_only=True)
    except pm.AdapterInvalid as e:
        info["error"] = str(e)
        return info
    except (pm.DataRootUnavailable, pm.StorageUnsafe, ValueError, OSError) as e:
        # adapter may still be valid — report it truthfully, storage broken
        try:
            import validate as project_validate
            info["adapter_valid"] = project_validate.validate(project_root).exit_code() == 0
        except Exception:                       # noqa: BLE001 -- report shape first
            info["adapter_valid"] = False
        info["storage_ok"] = False
        info["storage_error"] = str(e).splitlines()[0][:200]
        return info

    info["adapter_valid"] = True
    info["project_id"] = store.project_id
    info["scopes"] = store.scopes
    info["privacy"] = store.privacy
    info["trust"] = store.trust
    info["promotion"] = {"default_mode": "manual-with-evidence", "dry_run_first": True}
    info["layers"] = {k: v["durability"] for k, v in ml.LAYER_POLICY.items()}

    # storage facts — every access through the containment-safe paths; a
    # symlinked/escaped store reports unavailable instead of being followed
    try:
        info["memory_dir_available"] = store.memory_dir.is_dir()
        info["l2_entries"] = store.count_entries() if store.scopes.get("project") else 0
        exps = store.experiments_dir
        info["l5_experiments"] = len(list(exps.iterdir())) if exps.is_dir() else 0
    except (pm.ScopeDenied, pm.StorageUnsafe, ValueError, OSError) as e:
        info["storage_ok"] = False
        info["storage_error"] = str(e).splitlines()[0][:200]
        info["l2_entries"] = 0
        info["l5_experiments"] = 0
    return info


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only Memory Plane status")
    parser.add_argument("project_root", nargs="?", type=Path, default=Path("."))
    parser.add_argument("--data-root", type=Path, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    info = status(args.project_root, args.data_root)
    if args.json:
        print(json.dumps(info, ensure_ascii=False, indent=2, default=str))
    else:
        for key, value in info.items():
            print(f"{key:22}: {value}")
    return 0 if info.get("adapter_valid") else 1


if __name__ == "__main__":
    sys.exit(main())
