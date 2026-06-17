#!/usr/bin/env python3
"""
Generate ~/.claude-code-router/config.json for claude-code-router (ccr).

Reads scripts/ccr/config.template.json, substitutes every ${SECRET_NAME}
placeholder with the matching value from the Drive `.secrets` file (via
scripts/lib/drive_secrets.py), and writes the result to the ccr config path in
the user's home directory.

Why this design (Iron Law #6 + Secrets Policy):
  - The template is public-safe and committed (placeholders only, no keys).
  - Real keys never touch the repo — they are fetched on demand from Drive.
  - Output lives OUTSIDE the repo (~/.claude-code-router/), so it is never
    accidentally committed.

Missing secrets are reported by NAME only (never value) and left blank so the
other providers still work; that provider will simply 401 until you add its key
to Drive `.secrets`.

Usage:
  python scripts/gen-ccr-config.py            # write ~/.claude-code-router/config.json
  python scripts/gen-ccr-config.py --print    # print result to stdout, don't write
  python scripts/gen-ccr-config.py --out PATH # custom output path
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = REPO_ROOT / "scripts" / "ccr" / "config.template.json"

# Reuse the repo's on-demand Drive secret reader.
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))
try:
    from drive_secrets import fetch_secret  # type: ignore
except Exception as exc:  # pragma: no cover - defensive
    sys.stderr.write(f"ERROR: cannot import drive_secrets: {exc}\n")
    raise SystemExit(1)

PLACEHOLDER = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


def default_out() -> Path:
    return Path.home() / ".claude-code-router" / "config.json"


def render(template_text: str) -> tuple[str, list[str], list[str]]:
    """Substitute ${NAME} -> secret value. Returns (text, resolved, missing)."""
    resolved: list[str] = []
    missing: list[str] = []

    def sub(match: re.Match[str]) -> str:
        name = match.group(1)
        value = fetch_secret(name)
        if value:
            if name not in resolved:
                resolved.append(name)
            return value
        if name not in missing:
            missing.append(name)
        return ""

    return PLACEHOLDER.sub(sub, template_text), resolved, missing


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--print", action="store_true", help="print to stdout, do not write file")
    ap.add_argument("--out", type=Path, default=None, help="output path (default ~/.claude-code-router/config.json)")
    args = ap.parse_args()

    if not TEMPLATE.is_file():
        sys.stderr.write(f"ERROR: template not found: {TEMPLATE}\n")
        return 1

    text, resolved, missing = render(TEMPLATE.read_text(encoding="utf-8"))

    if args.print:
        # Note: --print exposes real keys; keep for debugging only.
        sys.stdout.write(text)
        return 0

    out = args.out or default_out()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")

    print(f"[OK] wrote ccr config: {out}")
    print(f"     keys resolved from Drive: {', '.join(resolved) or '(none)'}")
    if missing:
        print(f"     [WARN] MISSING in Drive .secrets (provider will 401 until added): {', '.join(missing)}")
        print("            add them:  echo 'NAME=value' >> drive/.secrets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
