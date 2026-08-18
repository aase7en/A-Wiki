#!/usr/bin/env python3
"""awiki status — read-only, deterministic project-adapter report.

Shows: project id, adapter validity (via the same offline validator),
domains, memory policy, allowed integrations, privacy/trust, and state-dir
availability. --json emits machine-readable output. Never writes anything.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate as pv  # noqa: E402 -- same validation path as the CLI
from attach import AGENTS_MARKER  # noqa: E402 -- one marker definition


def status(project_root: Path) -> dict:
    yml = project_root / ".awiki" / "project.yaml"
    data: dict = {}
    if yml.is_file():
        try:
            loaded = yaml.safe_load(yml.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                data = loaded
        except yaml.YAMLError:
            data = {}

    result = pv.validate(project_root)
    agents = project_root / "AGENTS.md"
    agents_text = agents.read_text(encoding="utf-8") if agents.is_file() else ""

    return {
        "project_root": str(project_root),
        "id": data.get("id"),
        "adapter_present": yml.is_file(),
        "adapter_valid": result.exit_code() == 0,
        "validation_errors": result.errors,
        "domains": data.get("domains", []),
        "memory": data.get("memory", {}).get("scopes", {}),
        "integrations": data.get("integrations", {}).get("allowed", []),
        "privacy": data.get("privacy", {}),
        "trust": data.get("trust", {}),
        "code_context_enabled": bool(data.get("code_context", {}).get("enabled")),
        "context_md_present": (project_root / ".awiki" / "context.md").is_file(),
        "state_dir_available": (project_root / ".awiki" / "state").is_dir(),
        "agents_adapter_section": AGENTS_MARKER in agents_text,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only A-Wiki project-adapter status")
    parser.add_argument("project_root", nargs="?", type=Path, default=Path("."))
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(argv)

    root = args.project_root.resolve()
    info = status(root)
    code = 0 if info["adapter_valid"] else 1

    if args.json:
        print(json.dumps(info, ensure_ascii=False, indent=2, default=str))
        return code

    print(f"A-Wiki adapter   : {'valid' if info['adapter_valid'] else 'INVALID/MISSING'}")
    print(f"Project          : {info['id'] or '<unknown>'}")
    print(f"Domains          : {', '.join(info['domains']) or '-'}")
    print(f"Memory scopes    : {info['memory'] or '-'}")
    print(f"Integrations     : {', '.join(info['integrations']) or '-'}")
    print(f"Privacy          : {info['privacy'] or '-'}")
    print(f"Trust            : {info['trust'] or '-'}")
    print(f"Code context     : {'enabled (policy only)' if info['code_context_enabled'] else 'off'}")
    print(f"context.md       : {'yes' if info['context_md_present'] else 'no'}")
    print(f"state/ available : {'yes' if info['state_dir_available'] else 'no'}")
    for e in info["validation_errors"]:
        print(f"  error: {e}")
    return code


if __name__ == "__main__":
    sys.exit(main())
