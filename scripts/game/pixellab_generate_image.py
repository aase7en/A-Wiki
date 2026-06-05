#!/usr/bin/env python3
"""Generate a single pixel-art image via the PixelLab `create-image-pixflux` API.

Lightweight, reusable helper for the A-Wiki / Trading-RPG asset pipeline.
- Reads PIXELLAB_API_TOKEN on-demand from Drive secrets (never cached, never logged).
- pixflux is synchronous and returns a base64 PNG (max 400x400).
- Optional nearest-neighbour upscale to a target square size (keeps crisp pixels),
  so a 256px generation can fill a 2048px scene texture without code changes.

Usage:
  python3 scripts/game/pixellab_generate_image.py \
    --description "high top-down wooden pirate galleon deck ..." \
    --size 256 --no-background --upscale 2048 \
    --out /path/to/out.png [--seed 12345] [--view "high top-down"]

  python3 scripts/game/pixellab_generate_image.py \
    --description "pixel art icon of a tiny garden sprinkler" \
    --icon --out /path/to/icon.png

Token policy: see CLAUDE.md Secrets Policy. The token is fetched per call and
never written to disk, manifests, or stdout.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import ssl
import urllib.request
import urllib.error

API_URL = "https://api.pixellab.ai/v2/create-image-pixflux"


def ssl_context() -> ssl.SSLContext:
    """Prefer certifi's CA bundle; some python.org builds ship without system roots."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


def fetch_token() -> str:
    tok = os.environ.get("PIXELLAB_API_TOKEN")
    if tok:
        return tok.strip()
    # Fall back to Drive secrets resolver (on-demand, never cached).
    here = os.path.dirname(os.path.abspath(__file__))
    lib = os.path.normpath(os.path.join(here, "..", "lib"))
    sys.path.insert(0, lib)
    try:
        from drive_secrets import fetch_secret  # type: ignore
    except Exception as exc:  # pragma: no cover
        sys.exit(f"cannot import drive_secrets: {exc}")
    tok = fetch_secret("PIXELLAB_API_TOKEN")
    if not tok:
        sys.exit("PIXELLAB_API_TOKEN unavailable")
    return tok.strip()


def build_payload(
    *,
    description: str,
    negative: str,
    size: int,
    no_background: bool,
    view: str | None,
    text_guidance: float,
    seed: int | None,
    icon: bool,
) -> dict:
    effective_size = 64 if icon else size
    payload = {
        "description": description,
        "image_size": {"width": effective_size, "height": effective_size},
        "text_guidance_scale": text_guidance,
        "no_background": True if icon else no_background,
    }
    if icon:
        payload["detail"] = "medium detail"
    if negative:
        payload["negative_description"] = negative
    if view:
        payload["view"] = view
    if seed is not None:
        payload["seed"] = seed
    return payload


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--description", required=True)
    ap.add_argument("--negative", default="")
    ap.add_argument("--size", type=int, default=256, help="square generation size (16-400)")
    ap.add_argument("--no-background", action="store_true", help="transparent background")
    ap.add_argument("--view", default=None, choices=["side", "low top-down", "high top-down"])
    ap.add_argument("--text-guidance", type=float, default=8.0)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--upscale", type=int, default=0, help="nearest-neighbour upscale to NxN (0=off)")
    ap.add_argument("--icon", action="store_true", help="force a 64x64 transparent medium-detail icon")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    payload = build_payload(
        description=args.description,
        negative=args.negative,
        size=args.size,
        no_background=args.no_background,
        view=args.view,
        text_guidance=args.text_guidance,
        seed=args.seed,
        icon=args.icon,
    )

    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {fetch_token()}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=180, context=ssl_context()) as resp:
            body = json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        sys.exit(f"HTTP {exc.code}: {exc.read().decode()[:500]}")

    b64 = body["image"]["base64"] if isinstance(body.get("image"), dict) else body.get("image")
    if not b64:
        sys.exit(f"no image in response: {list(body)}")
    raw = base64.b64decode(b64)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "wb") as f:
        f.write(raw)

    usage = body.get("usage")
    if args.upscale:
        from PIL import Image  # local import: only needed for upscale path
        im = Image.open(args.out).convert("RGBA")
        im = im.resize((args.upscale, args.upscale), Image.NEAREST)
        im.save(args.out)
    gen_size = payload["image_size"]["width"]
    print(json.dumps({"out": args.out, "gen_size": gen_size, "upscaled_to": args.upscale or gen_size, "usage": usage}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
