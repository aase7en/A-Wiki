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


def agent_config_links_step() -> Step:
    # Non-fatal: a fresh machine may not have every harness installed yet,
    # or Drive may not be mounted — that's an actionable WARN, not a FAIL.
    proc = run(["bash", "scripts/link-agent-configs.sh", "--status"], timeout=120)
    level = "OK" if proc.returncode == 0 else "WARN"
    return Step(level, "agent config links", tail(proc))


def global_env_step() -> Step:
    """Check secrets/global.env exists on Drive and isn't a placeholder stub."""
    proc = run(
        [sys.executable, "-c",
         "import sys; sys.path.insert(0,'scripts'); "
         "from drive_path import get_drive_root; "
         "from pathlib import Path; "
         "p = Path(get_drive_root()) / 'secrets' / 'global.env'; "
         "sys.exit(0 if p.exists() and '__LOAD_GLOBAL__' not in p.read_text(encoding='utf-8', errors='ignore') else 1)"],
        timeout=30,
    )
    if proc.returncode == 0:
        return Step("OK", "global.env", "secrets/global.env present (not a placeholder)")
    return Step("WARN", "global.env", "missing or placeholder — run setup-local.sh or populate Drive secrets/")


def ide_hook_step() -> Step:
    """Check the IDE terminal hook is injected into a shell rc file."""
    if not (REPO_ROOT / "scripts" / "setup-ide-env.sh").exists():
        return Step("WARN", "IDE hook", "setup-ide-env.sh not found in this clone")
    proc = run(["bash", "scripts/setup-ide-env.sh", "--status"], timeout=20)
    # Status exits 0 regardless; parse output for an injected hook.
    out = (proc.stdout or "") + (proc.stderr or "")
    if "✅" in out or "injected" in out.lower():
        return Step("OK", "IDE hook", tail(proc))
    return Step("WARN", "IDE hook", "no rc file has the hook — run 'bash scripts/setup-ide-env.sh'")


def loader_step() -> Step:
    """Sanity-check that load-global-env.sh can source at least one AI key."""
    loader = REPO_ROOT / "scripts" / "load-global-env.sh"
    if not loader.exists():
        return Step("WARN", "env loader", "load-global-env.sh not found in this clone")
    # Source the loader, then probe common AI keys. Pass Drive path explicitly
    # via env so the resolver finds it even in a clean subprocess context.
    try:
        drive_root = subprocess.run(
            [sys.executable, "-c",
             "import sys; sys.path.insert(0,'scripts'); "
             "from drive_path import get_drive_root; print(get_drive_root())"],
            cwd=REPO_ROOT, text=True, capture_output=True, timeout=15,
        ).stdout.strip()
    except Exception:
        drive_root = ""
    env = dict(__import__("os").environ)
    if drive_root:
        env["A_WIKI_DRIVE_PATH"] = drive_root
    probe = (
        f"source \"{loader}\" --quiet 2>/dev/null; "
        "for k in GEMINI_API_KEY OPENROUTER_API_KEY ANTHROPIC_API_KEY DEEPSEEK_API_KEY GROQ_API_KEY; "
        "do [ -n \"${!k:-}\" ] && echo FOUND && exit 0; done; "
        "echo NONE"
    )
    proc = subprocess.run(["bash", "-c", probe], cwd=REPO_ROOT, text=True,
                          capture_output=True, timeout=30, env=env)
    if "FOUND" in (proc.stdout or ""):
        return Step("OK", "env loader", "load-global-env.sh sources ≥1 AI key")
    return Step("WARN", "env loader", "no AI keys loaded — check secrets/global.env on Drive")


def checks(build_vec: bool = False) -> list[Step]:
    vec_args = [sys.executable, "scripts/verify-cross-platform.py"]
    if build_vec:
        vec_args.append("--build-vec")
    return [
        command_step("cloud link", ["bash", "scripts/setup-cloud-link.sh", "--status"], timeout=60),
        agent_config_links_step(),
        global_env_step(),
        ide_hook_step(),
        loader_step(),
        command_step("drive secrets", [sys.executable, "scripts/lib/drive_secrets.py", "--check"], timeout=60),
        command_step("import keys", [sys.executable, "scripts/import-keys.py", "--check"], timeout=60),
        command_step("kilo config", ["bash", "scripts/setup-kilo-config.sh", "--check"], timeout=60),
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

