#!/usr/bin/env python3
"""Portable clone verifier for Mac, Linux, Windows, and WSL.

Run this after cloning and setup-local on each machine. It intentionally avoids
printing secrets and keeps heavyweight vector rebuild optional.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import platform
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Check:
    level: str
    name: str
    detail: str


def run(args: list[str], timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=REPO_ROOT, text=True, capture_output=True, timeout=timeout)


def check_python_version() -> Check:
    version = sys.version_info
    if version < (3, 9):
        return Check("FAIL", "python", f"{platform.python_version()} < 3.9")
    if version >= (3, 13):
        return Check("WARN", "python", f"{platform.python_version()} may lack some fastembed wheels")
    return Check("OK", "python", platform.python_version())


def check_module(module: str) -> Check:
    if importlib.util.find_spec(module) is None:
        return Check("FAIL", f"module {module}", f"missing; run {sys.executable} -m pip install -r requirements.txt")
    return Check("OK", f"module {module}", "available")


def check_drive_pointer() -> Check:
    drive = REPO_ROOT / "drive"
    raw = REPO_ROOT / "raw"
    if drive.exists() or raw.exists():
        pieces = []
        if drive.exists():
            pieces.append("drive")
        if raw.exists():
            pieces.append("raw")
        return Check("OK", "external data link", "present: " + ", ".join(pieces))
    if (REPO_ROOT / ".drive-path").exists():
        return Check("WARN", "external data link", ".drive-path exists but drive/raw link is missing")
    return Check("WARN", "external data link", "missing; run bash scripts/setup-cloud-link.sh --provider google")


def check_gen_index() -> Check:
    proc = run([sys.executable, "scripts/gen-index.py", "--check"], timeout=60)
    if proc.returncode == 0:
        return Check("OK", "gen-index --check", "passed")
    detail = (proc.stderr or proc.stdout or "").strip().splitlines()
    return Check("FAIL", "gen-index --check", detail[-1] if detail else f"exit {proc.returncode}")


def check_vec_build(enabled: bool) -> Check:
    if not enabled:
        return Check("WARN", "vec index build", "skipped; rerun with --build-vec for full verification")
    proc = run([sys.executable, "scripts/build-vec-index.py"], timeout=300)
    if proc.returncode == 0:
        lines = (proc.stdout or proc.stderr or "").strip().splitlines()
        return Check("OK", "vec index build", lines[-1] if lines else "passed")
    detail = (proc.stderr or proc.stdout or "").strip().splitlines()
    return Check("FAIL", "vec index build", detail[-1] if detail else f"exit {proc.returncode}")


def check_shell_scripts() -> Check:
    scripts = [
        "scripts/setup-local.sh",
        "scripts/update-model-roster.sh",
        "scripts/delegate.sh",
        "scripts/swarm/delegate.sh",
    ]
    proc = run(["bash", "-n", *scripts], timeout=30)
    if proc.returncode == 0:
        return Check("OK", "shell syntax", f"{len(scripts)} script(s)")
    detail = (proc.stderr or proc.stdout or "").strip().splitlines()
    return Check("FAIL", "shell syntax", detail[-1] if detail else f"exit {proc.returncode}")


def checks(build_vec: bool) -> list[Check]:
    return [
        Check("OK", "platform", f"{platform.system()} {platform.release()} ({platform.machine()})"),
        check_python_version(),
        check_module("apsw"),
        check_module("sqlite_vec"),
        check_module("fastembed"),
        check_drive_pointer(),
        check_shell_scripts(),
        check_gen_index(),
        check_vec_build(build_vec),
    ]


def exit_code(results: list[Check]) -> int:
    return 1 if any(item.level == "FAIL" for item in results) else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify this A-Wiki clone on the current OS.")
    parser.add_argument("--build-vec", action="store_true", help="Run the heavier sqlite-vec embedding rebuild.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    results = checks(build_vec=args.build_vec)
    if args.json:
        print(json.dumps([item.__dict__ for item in results], ensure_ascii=False, indent=2))
    else:
        print("A-Wiki Cross-Platform Verify")
        print("============================")
        for item in results:
            print(f"[{item.level}] {item.name} - {item.detail}")
    return exit_code(results)


if __name__ == "__main__":
    raise SystemExit(main())
