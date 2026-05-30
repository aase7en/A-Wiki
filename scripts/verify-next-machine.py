#!/usr/bin/env python3
"""One-command verifier for a freshly pulled A-Wiki clone on another machine."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Step:
    level: str
    name: str
    detail: str


def run(args: list[str], timeout: int = 180) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=REPO_ROOT, text=True, capture_output=True, timeout=timeout)


def tail(proc: subprocess.CompletedProcess[str]) -> str:
    lines = (proc.stdout or proc.stderr or "").strip().splitlines()
    return lines[-1] if lines else f"exit {proc.returncode}"


def command_step(name: str, args: list[str], timeout: int = 180) -> Step:
    proc = run(args, timeout=timeout)
    if proc.returncode == 0:
        return Step("OK", name, tail(proc))
    return Step("FAIL", name, tail(proc))


def docker_step() -> Step:
    if shutil.which("docker") is None:
        return Step("WARN", "docker", "not installed; skip Linux container verification on this machine")
    proc = run(["docker", "version", "--format", "{{.Server.Version}}"], timeout=20)
    if proc.returncode != 0:
        return Step("WARN", "docker", tail(proc))
    return Step("OK", "docker", f"available: {tail(proc)}")


def checks(build_vec: bool = False) -> list[Step]:
    vec_args = [sys.executable, "scripts/verify-cross-platform.py"]
    if build_vec:
        vec_args.append("--build-vec")
    return [
        command_step("cloud link", ["bash", "scripts/setup-cloud-link.sh", "--status"], timeout=60),
        command_step("drive secrets", [sys.executable, "scripts/lib/drive_secrets.py", "--check"], timeout=60),
        command_step("import keys", [sys.executable, "scripts/import-keys.py", "--check"], timeout=60),
        command_step("readiness", [sys.executable, "scripts/verify-awiki-ready.py", "--skip-remote"], timeout=180),
        command_step("cross-platform", vec_args, timeout=360 if build_vec else 180),
        command_step("sync smoke", [sys.executable, "scripts/sync-smoke.py"], timeout=120),
        docker_step(),
    ]


def exit_code(steps: list[Step]) -> int:
    return 1 if any(step.level == "FAIL" for step in steps) else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-vec", action="store_true", help="include heavy sqlite-vec rebuild")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    steps = checks(build_vec=args.build_vec)
    if args.json:
        print(json.dumps([asdict(step) for step in steps], ensure_ascii=False, indent=2))
    else:
        print("A-Wiki Next Machine Verify")
        print("==========================")
        for step in steps:
            print(f"[{step.level}] {step.name} - {step.detail}")
    return exit_code(steps)


if __name__ == "__main__":
    raise SystemExit(main())

