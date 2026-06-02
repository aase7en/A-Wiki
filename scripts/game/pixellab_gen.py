#!/usr/bin/env python3
"""PixelLab API generator for the Tide & Tally asset pipeline.

Secret policy: the API token is read on-demand from Drive secrets
(drive_secrets.PIXELLAB_API_TOKEN) — never hard-coded, never committed.

Currently supports the cheap synchronous image endpoint (pixflux). Async
endpoints (objects, tilesets, characters) can be added the same way later.

Usage:
    python3 scripts/game/pixellab_gen.py balance
    python3 scripts/game/pixellab_gen.py image \\
        --prompt "wooden treasure chest, closed, gold trim, pixel art" \\
        --width 128 --height 128 --view "high top-down" --no-bg \\
        --out /abs/path/prop.png
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import ssl
import sys
import urllib.request
import urllib.error

API_BASE = "https://api.pixellab.ai/v2"


def _ssl_context() -> ssl.SSLContext:
    """Use certifi's CA bundle if present (python.org builds lack system CAs)."""
    try:
        import certifi  # type: ignore

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


_SSL = _ssl_context()

# Resolve the token via the A-Wiki Drive secrets helper (on-demand).
_LIB = os.path.join(os.path.dirname(__file__), "..", "lib")
sys.path.insert(0, os.path.abspath(_LIB))


def get_token() -> str:
    tok = os.environ.get("PIXELLAB_API_TOKEN")
    if tok:
        return tok.strip()
    try:
        from drive_secrets import fetch_secret  # type: ignore

        return str(fetch_secret("PIXELLAB_API_TOKEN")).strip()
    except Exception as exc:  # pragma: no cover - environment dependent
        sys.exit(f"Could not resolve PIXELLAB_API_TOKEN: {exc}")


def _request(method: str, path: str, token: str, body: dict | None = None) -> dict:
    url = f"{API_BASE}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=180, context=_SSL) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")
        sys.exit(f"HTTP {e.code} on {method} {path}: {detail[:500]}")
    except urllib.error.URLError as e:
        sys.exit(f"Network error on {method} {path}: {e}")


def cmd_balance(_: argparse.Namespace, token: str) -> None:
    print(json.dumps(_request("GET", "/balance", token), indent=2))


def cmd_image(args: argparse.Namespace, token: str) -> None:
    body: dict = {
        "description": args.prompt,
        "image_size": {"width": args.width, "height": args.height},
        "no_background": bool(args.no_bg),
        "isometric": bool(args.iso),
    }
    if args.negative:
        body["negative_description"] = args.negative
    if args.view:
        body["view"] = args.view
    if args.direction:
        body["direction"] = args.direction
    if args.seed is not None:
        body["seed"] = args.seed

    print(f"Generating (pixflux) {args.width}x{args.height}: {args.prompt!r} ...", file=sys.stderr)
    resp = _request("POST", "/create-image-pixflux", token, body)

    img = resp.get("image") or {}
    b64 = img.get("base64")
    if not b64:
        sys.exit(f"No image in response: {json.dumps(resp)[:500]}")
    out = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "wb") as f:
        f.write(base64.b64decode(b64))

    usage = resp.get("usage")
    print(f"Wrote {out} ({os.path.getsize(out)} bytes)")
    if usage:
        print(f"Usage: {json.dumps(usage)}")


def main() -> None:
    ap = argparse.ArgumentParser(description="PixelLab generator (Tide & Tally)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("balance", help="show remaining credits/generations")

    pi = sub.add_parser("image", help="generate one image (pixflux, sync)")
    pi.add_argument("--prompt", required=True)
    pi.add_argument("--negative", default="")
    pi.add_argument("--width", type=int, default=128)
    pi.add_argument("--height", type=int, default=128)
    pi.add_argument("--view", choices=["side", "low top-down", "high top-down"], default=None)
    pi.add_argument(
        "--direction",
        choices=["north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west"],
        default=None,
    )
    pi.add_argument("--iso", action="store_true", help="isometric framing")
    pi.add_argument("--no-bg", action="store_true", help="transparent background")
    pi.add_argument("--seed", type=int, default=None)
    pi.add_argument("--out", required=True, help="output PNG path")

    args = ap.parse_args()
    token = get_token()
    {"balance": cmd_balance, "image": cmd_image}[args.cmd](args, token)


if __name__ == "__main__":
    main()
