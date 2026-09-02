#!/usr/bin/env python3
"""awiki doctor — one command brain health check (Slice F).

Sections (default = fast local checks; --full adds preflight + last CI):
  registry   skills-registry integrity + surface drift
  hooks      hook registry authority + config wiring
  mcp        awiki MCP server tool surface (import + count)
  specs      stale-spec gate (plans vs scoped files)
  privacy    quick tracked-file privacy scan
"""
from __future__ import annotations

import argparse
import importlib.util as ilu
import subprocess
import sys
from pathlib import Path

def _configure_utf8_stdio() -> None:
    """Pin CLI byte streams to UTF-8 without mutating host stdio on import."""
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError, ValueError):
            pass


REPO_ROOT = Path(__file__).resolve().parents[1]


def _run(cmd: list[str]) -> tuple[bool, str]:
    p = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=300)
    tail = ((p.stdout or "") + (p.stderr or "")).strip().splitlines()
    return p.returncode == 0, tail[-1][:120] if tail else ""


def sections(full: bool) -> list[tuple[str, bool, str, str]]:
    out = []
    ok, msg = _run([sys.executable, "scripts/regen-skill-surfaces.py",
                    "--check"])
    out.append(("registry", ok, "registry + surfaces in sync", msg))
    ok, msg = _run([sys.executable, "scripts/hooks/registry.py", "--check"])
    out.append(("hooks", ok, "hook registry authority", msg))
    # MCP: import module, count tools
    try:
        spec = ilu.spec_from_file_location(
            "m", REPO_ROOT / "scripts" / "mcp-wiki-server.py")
        m = ilu.module_from_spec(spec); spec.loader.exec_module(m)
        n = len(m.TOOLS)
        out.append(("mcp", n >= 30, f"awiki MCP tools ({n})", ""))
    except Exception as e:
        out.append(("mcp", False, "awiki MCP import", str(e)[:120]))
    ok, msg = _run([sys.executable, "scripts/check-stale-specs.py"])
    out.append(("specs", ok, "plans cover their scoped files", msg))
    ok, msg = _run([sys.executable, "scripts/check-privacy.py"])
    out.append(("privacy", ok, "tracked files privacy", msg))
    if full:
        ok, msg = _run([sys.executable, "scripts/agent-preflight.py",
                        "--skip-remote"])
        out.append(("preflight", ok, "full machine preflight", msg))
        head_ok, head = _run(["git", "rev-parse", "HEAD"])
        if head_ok and head:
            ok, msg = _run(["gh", "run", "list", "--workflow",
                            "ci-core.yml", "--commit", head, "--limit", "1",
                            "--json", "conclusion", "--jq", ".[0].conclusion"])
        else:
            ok, msg = False, head or "unable to resolve HEAD"
        out.append(("ci", ok and msg == "success",
                    "Core CI at current HEAD", msg or "unknown"))
    return out


def main(argv=None) -> int:
    _configure_utf8_stdio()
    ap = argparse.ArgumentParser(description="A-Wiki brain health check")
    ap.add_argument("--full", action="store_true",
                    help="add preflight + last CI verdict (slower)")
    args = ap.parse_args(argv)
    version = (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()         if (REPO_ROOT / "VERSION").is_file() else "?"
    print(f"🧠 A-Wiki brain v{version}" + ("  (--full)" if args.full else ""))
    rows = sections(args.full)
    bad = 0
    for name, ok, what, msg in rows:
        print(f"{'✅' if ok else '❌'} {name:9} {what}"
              + (f" — {msg}" if (msg and not ok) else ""))
        bad += 0 if ok else 1
    print(("🧠 brain healthy" if not bad else f"⚠️ {bad} section(s) need "
           "attention"))
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
