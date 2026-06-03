#!/usr/bin/env python3
"""PixelLab API v2 — character + animation wrapper (async jobs).

Adds the persistent-character flow on top of pixellab_gen.py (which only does the
sync pixflux endpoint). Used to build น้องซันเดย์ for Pixel Wealth Quest:

    create-character-v3  → 8 clean rotations from a south-facing reference
    animate-character    → idle/walk/sit/lie/… (mode v3 = free-text action)

Secret policy: PIXELLAB_API_TOKEN read on-demand from Drive secrets (never cached,
never committed). Downloads rotation/animation PNGs straight into the game.

Examples:
  python3 scripts/game/pixellab_character.py create-character \\
    --ref game-assets/references/pixel-wealth-quest/nong-sunday/nong-sunday--single-pose--nobg--v001.png \\
    --description "Cute Thai boy, navy vest + bow tie, cozy 16-bit RPG sprite" \\
    --name nong-sunday --view "low top-down" --template-id mannequin --size 64 \\
    --no-bg --out-dir /abs/pwq/public/assets/character/nong-sunday/v3 --slug nong-sunday

  python3 scripts/game/pixellab_character.py animate --character-id <id> \\
    --action "sitting down on the floor" --mode v3 --frames 8 --directions south \\
    --out-dir /abs/pwq/public/assets/character/nong-sunday/anim --slug nong-sunday
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import ssl
import sys
import time
import urllib.request
import urllib.error

API_BASE = "https://api.pixellab.ai/v2"


def _ssl_ctx() -> ssl.SSLContext:
    try:
        import certifi  # type: ignore

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()


_SSL = _ssl_ctx()
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "lib")))


def get_token() -> str:
    tok = os.environ.get("PIXELLAB_API_TOKEN")
    if tok:
        return tok.strip()
    try:
        from drive_secrets import fetch_secret  # type: ignore

        return str(fetch_secret("PIXELLAB_API_TOKEN")).strip()
    except Exception as exc:  # pragma: no cover
        sys.exit(f"Could not resolve PIXELLAB_API_TOKEN: {exc}")


def _request(method: str, path: str, token: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(f"{API_BASE}{path}", data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=180, context=_SSL) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code} on {method} {path}: {e.read().decode(errors='replace')[:800]}")
    except urllib.error.URLError as e:
        sys.exit(f"Network error on {method} {path}: {e}")


def _b64img(path: str) -> dict:
    with open(path, "rb") as f:
        raw = f.read()
    fmt = "png" if path.lower().endswith(".png") else "jpeg"
    return {"type": "base64", "base64": base64.b64encode(raw).decode(), "format": fmt}


def _download(url: str, out: str) -> None:
    os.makedirs(os.path.dirname(out), exist_ok=True)
    req = urllib.request.Request(url)  # rotation/anim URLs are signed — no auth header
    with urllib.request.urlopen(req, timeout=120, context=_SSL) as r, open(out, "wb") as f:
        f.write(r.read())


def _download_character_zip(cid: str, token: str, out_dir: str, slug: str) -> list[str]:
    """The rotation/animation B2 URLs 403 for direct GET — the documented delivery
    path is the authenticated /characters/{id}/zip export. Unpacks all PNGs."""
    import io
    import zipfile

    req = urllib.request.Request(
        f"{API_BASE}/characters/{cid}/zip", headers={"Authorization": f"Bearer {token}"}
    )
    with urllib.request.urlopen(req, timeout=180, context=_SSL) as r:
        data = r.read()
    os.makedirs(out_dir, exist_ok=True)
    names: list[str] = []
    z = zipfile.ZipFile(io.BytesIO(data))
    for m in z.namelist():
        if not m.lower().endswith(".png"):
            continue
        parts = m.split("/")
        if "rotations" in parts:
            name = f"{slug}_{parts[-1]}"  # e.g. nong-sunday_south.png
        else:  # animations/<action>/<dir>/<frame>.png → flatten
            name = f"{slug}_" + "_".join(parts[1:]).replace(".png", "") + ".png"
        with z.open(m) as src, open(os.path.join(out_dir, name), "wb") as dst:
            dst.write(src.read())
        names.append(name)
    return names


def _collect_urls(node, prefix=""):  # walk nested dict/list for http(s) string URLs
    found = []
    if isinstance(node, str) and node.startswith("http"):
        found.append((prefix.strip("_"), node))
    elif isinstance(node, dict):
        for k, v in node.items():
            found += _collect_urls(v, f"{prefix}_{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            found += _collect_urls(v, f"{prefix}_{i}")
    return found


def poll(job_id: str, token: str, timeout: int = 300, interval: int = 5) -> dict:
    waited = 0
    while waited < timeout:
        job = _request("GET", f"/background-jobs/{job_id}", token)
        status = (job.get("status") or "").lower()
        print(f"  job {job_id[:8]}… status={status} ({waited}s)", file=sys.stderr)
        if status in ("completed", "success", "succeeded", "done"):
            return job
        if status in ("failed", "error", "cancelled"):
            sys.exit(f"Job {job_id} {status}: {json.dumps(job.get('last_response'))[:600]}")
        time.sleep(interval)
        waited += interval
    sys.exit(f"Job {job_id} timed out after {timeout}s")


def cmd_create_character(a: argparse.Namespace, token: str) -> None:
    body: dict = {"description": a.description, "view": a.view}
    if a.ref:
        body["reference_image"] = _b64img(a.ref)
    if a.size:
        body["image_size"] = {"width": a.size, "height": a.size}
    if a.template_id:
        body["template_id"] = a.template_id
    if a.name:
        body["name"] = a.name
    if a.seed is not None:
        body["seed"] = a.seed
    if a.no_bg:
        body["no_background"] = True

    print(f"Creating character v3: {a.description!r} (ref={bool(a.ref)}) …", file=sys.stderr)
    resp = _request("POST", "/create-character-v3", token, body)
    cid = resp.get("character_id")
    job = resp.get("background_job_id")
    print(json.dumps({"character_id": cid, "background_job_id": job, "usage": resp.get("usage")}))
    if not cid or not job:
        sys.exit(f"Unexpected response: {json.dumps(resp)[:600]}")
    poll(job, token)
    names = _download_character_zip(cid, token, a.out_dir, a.slug)
    detail = _request("GET", f"/characters/{cid}", token)
    with open(os.path.join(a.out_dir, f"{a.slug}.character.json"), "w") as f:
        json.dump({"character_id": cid, "size": detail.get("size"),
                   "directions": detail.get("directions"), "files": names}, f, indent=2)
    print(f"DONE character_id={cid}; downloaded {len(names)} png(s): {names}")


def cmd_animate(a: argparse.Namespace, token: str) -> None:
    body: dict = {"character_id": a.character_id, "mode": a.mode}
    if a.action:
        body["action_description"] = a.action
    if a.template_animation_id:
        body["template_animation_id"] = a.template_animation_id
    if a.frames:
        body["frame_count"] = a.frames
    if a.directions:
        body["directions"] = a.directions.split(",")
    if a.name:
        body["animation_name"] = a.name
    print(f"Animating {a.character_id} mode={a.mode} action={a.action!r} …", file=sys.stderr)
    resp = _request("POST", "/animate-character", token, body)
    jobs = resp.get("background_job_ids") or []
    print(json.dumps({"jobs": jobs, "directions": resp.get("directions")}))
    for j in jobs:
        poll(j, token)
    names = _download_character_zip(a.character_id, token, a.out_dir, a.slug)
    print(f"DONE animation; re-exported {len(names)} png(s) → {a.out_dir}")


def cmd_get_character(a: argparse.Namespace, token: str) -> None:
    print(json.dumps(_request("GET", f"/characters/{a.character_id}", token), indent=2)[:4000])


def main() -> None:
    ap = argparse.ArgumentParser(description="PixelLab character + animation (async)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    cc = sub.add_parser("create-character", help="create-character-v3 from a south-facing reference")
    cc.add_argument("--ref", help="south-facing reference PNG (optional; else from-scratch)")
    cc.add_argument("--description", required=True)
    cc.add_argument("--name", default=None)
    cc.add_argument("--view", default="low top-down", choices=["low top-down", "high top-down", "side"])
    cc.add_argument("--template-id", default=None, help="skeleton body type, e.g. mannequin")
    cc.add_argument("--size", type=int, default=64)
    cc.add_argument("--seed", type=int, default=None)
    cc.add_argument("--no-bg", action="store_true")
    cc.add_argument("--out-dir", required=True)
    cc.add_argument("--slug", default="character")

    an = sub.add_parser("animate", help="animate an existing character")
    an.add_argument("--character-id", required=True)
    an.add_argument("--action", default=None, help="free-text action for v3 mode")
    an.add_argument("--template-animation-id", default=None, help="for template mode (1 gen/dir)")
    an.add_argument("--mode", default="v3", choices=["template", "v3", "pro"])
    an.add_argument("--frames", type=int, default=8)
    an.add_argument("--directions", default=None, help="comma list e.g. south,north,east,west")
    an.add_argument("--name", default=None, help="animation name (used in filenames)")
    an.add_argument("--out-dir", required=True)
    an.add_argument("--slug", default="character")

    gc = sub.add_parser("get-character", help="dump character detail JSON")
    gc.add_argument("--character-id", required=True)

    args = ap.parse_args()
    token = get_token()
    {"create-character": cmd_create_character, "animate": cmd_animate, "get-character": cmd_get_character}[args.cmd](args, token)


if __name__ == "__main__":
    main()
