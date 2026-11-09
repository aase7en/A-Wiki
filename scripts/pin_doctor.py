#!/usr/bin/env python3
"""pin_doctor.py — detect stale `model:` pins in Kilo agent configs.

Scans <root>/.kilo/agents/*.md for `model:` frontmatter values and classifies:
  OK-DYNAMIC  alias-style pins (contain '/auto/' or equal 'auto') that resolve
              to the current model family at run time — cannot go stale.
  OK          hard pin still present in the live provider model list.
  DEPRECATED  hard pin absent from the live list — needs a replacement.
  UNKNOWN     could not verify (no network / no key / provider unsupported).

Live checks: Fireworks (FIREWORKS_API_KEY) and OpenRouter (public list, no key).
Fail-closed for reporting only — never exits nonzero on UNKNOWN, exits 1 only
when a DEPRECATED pin is found. Stdlib only; no writes; no secret output.

Usage: py -3.13 scripts/pin_doctor.py [--root <repo>] [--model <id>]
  --model probes a single model id without scanning (dry-run a candidate pin).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

_PIN_RE = re.compile(r"^model:\s*(\S+)\s*$", re.MULTILINE)
_TIMEOUT = 15


def _get(url: str, headers: dict[str, str] | None = None) -> dict | None:
    try:
        req = urllib.request.Request(url, headers=headers or {})
        with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def load_key() -> str | None:
    # Optional private env file via AWIKI_GLOBAL_ENV (machine-specific paths stay
    # out of this repo); never print values.
    candidate = os.environ.get("AWIKI_GLOBAL_ENV")
    if candidate:
        path = Path(candidate)
        if path.is_file():
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                m = re.match(r"^\s*FIREWORKS_API_KEY\s*=\s*(.+?)\s*$", line)
                if m:
                    return m.group(1).strip().strip('"').strip("'")
    return os.environ.get("FIREWORKS_API_KEY")


def provider_of(pin: str) -> str | None:
    if pin.startswith("fireworks-ai/") or "/fireworks/" in pin:
        return "fireworks"
    if pin.startswith("openrouter/") or "openrouter.ai" in pin:
        return "openrouter"
    if pin.startswith("anthropic/") or pin.startswith("openai/"):
        return None  # family not checkable here
    return None


def live_ids(provider: str) -> set[str] | None:
    if provider == "fireworks":
        key = load_key()
        if not key:
            return None
        data = _get(
            "https://api.fireworks.ai/inference/v1/models",
            {"Authorization": f"Bearer {key}"},
        )
        if not data:
            return None
        return {str(m.get("id", "")) for m in data.get("data", []) if m.get("id")}
    if provider == "openrouter":
        data = _get("https://openrouter.ai/api/v1/models")
        if not data:
            return None
        return {str(m.get("id", "")) for m in data.get("data", []) if m.get("id")}
    return None


def classify(pin: str) -> tuple[str, str]:
    if "/auto/" in pin or pin == "auto":
        return "OK-DYNAMIC", "alias resolves at run time; cannot go stale"
    provider = provider_of(pin)
    if provider is None:
        return "UNKNOWN", "no live-list probe for this provider family"
    ids = live_ids(provider)
    if ids is None:
        return "UNKNOWN", f"{provider}: list unavailable (network/key)"
    # Accept both the full routed id and its bare suffix form.
    bare = pin.rsplit("/", 1)[-1]
    if pin in ids or bare in ids:
        return "OK", f"present in live {provider} model list ({len(ids)} models)"
    return "DEPRECATED", f"absent from live {provider} model list — replace pin"


def scan(root: Path) -> int:
    agents_dir = root / ".kilo" / "agents"
    files = sorted(agents_dir.glob("*.md")) if agents_dir.is_dir() else []
    if not files:
        print(f"pin_doctor: no agent configs under {agents_dir}")
        return 0
    print(f"{'file':24} {'status':11} model")
    deprecated = 0
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        m = _PIN_RE.search(text)
        if not m:
            print(f"{path.name:24} {'NO-PIN':11} -")
            continue
        pin = m.group(1)
        status, note = classify(pin)
        print(f"{path.name:24} {status:11} {pin}")
        print(f"{'':24} {'':11} -> {note}")
        if status == "DEPRECATED":
            deprecated += 1
    if deprecated:
        print(f"pin_doctor: {deprecated} DEPRECATED pin(s) — action required")
        return 1
    print("pin_doctor: no deprecated pins")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    ap.add_argument("--model", help="probe a single model id instead of scanning")
    args = ap.parse_args()
    if args.model:
        status, note = classify(args.model)
        print(f"{status}: {args.model}\n-> {note}")
        return 1 if status == "DEPRECATED" else 0
    return scan(Path(args.root))


if __name__ == "__main__":
    sys.exit(main())
