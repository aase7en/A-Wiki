#!/usr/bin/env python3
"""
ask-notebooklm.py — Synthesize answers across many wiki pages via Gemini API.

NotebookLM has no public API, but it is built on Gemini. This script
reproduces the "ask across many sources, get cited answer" workflow by:

  1. Loading exports/notebooklm/<domain>.md (created by scripts/export-to-notebooklm.sh)
  2. Sending it as context + your question to Gemini Flash (free tier)
  3. Returning the answer + citing source page paths

Cost: Level 1 in Cost Pyramid (free, no Claude tokens spent).

Usage:
    python3 scripts/ask-notebooklm.py --domain iot --query "MQTT vs CoAP tradeoffs"
    python3 scripts/ask-notebooklm.py --domain pharmacy --query "ยาสามัญที่มี paracetamol"
    python3 scripts/ask-notebooklm.py --list                       # show bundles
    python3 scripts/ask-notebooklm.py --domain iot --refresh-bundle # re-run export first

Env: GEMINI_API_KEY (required). Get from https://aistudio.google.com/apikey
Model default: gemini-2.0-flash-exp (free, fast, 1M context).

Fallback: if GEMINI_API_KEY missing → suggests NotebookLM manual paste workflow.
"""
from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BUNDLE_DIR = REPO_ROOT / "exports" / "notebooklm"
DEFAULT_MODEL = "gemini-2.0-flash-exp"
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
MAX_BUNDLE_BYTES = 800_000  # ~200k tokens — well under Flash 1M ctx, leaves room

SYSTEM_PROMPT = """You are a knowledge synthesizer for the Aase7en InW Wiki.

Rules:
1. Answer ONLY from the provided wiki context. If the context does not cover the question, say so plainly.
2. Cite source pages inline as [wiki/path/to/file.md] after each claim.
3. Be concise — bullet points preferred over prose. No preamble.
4. If multiple pages disagree, surface the disagreement and cite both.
5. Respond in the same language as the question (Thai → Thai, English → English).
"""


def list_bundles() -> list[Path]:
    if not BUNDLE_DIR.is_dir():
        return []
    return sorted(BUNDLE_DIR.glob("*.md"))


def load_bundle(domain: str) -> tuple[str, Path]:
    fp = BUNDLE_DIR / f"{domain}.md"
    if not fp.exists():
        avail = ", ".join(p.stem for p in list_bundles()) or "(none)"
        raise SystemExit(
            f"bundle not found: {fp}\n"
            f"available: {avail}\n"
            f"run: bash scripts/export-to-notebooklm.sh {domain}"
        )
    text = fp.read_text(encoding="utf-8")
    if len(text.encode("utf-8")) > MAX_BUNDLE_BYTES:
        # Truncate — keep head + tail
        keep = MAX_BUNDLE_BYTES // 2
        text = text[:keep] + f"\n\n...[truncated {len(text) - keep*2} chars]...\n\n" + text[-keep:]
    return text, fp


def refresh_bundle(domain: str) -> None:
    script = REPO_ROOT / "scripts" / "export-to-notebooklm.sh"
    if not script.exists():
        raise SystemExit(f"missing: {script}")
    subprocess.run(["bash", str(script), domain], check=True)


def call_gemini(api_key: str, model: str, context: str, question: str) -> str:
    url = API_URL.format(model=model) + f"?key={api_key}"
    user_content = (
        f"# Wiki Context\n\n{context}\n\n"
        f"---\n\n# Question\n\n{question}"
    )
    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"role": "user", "parts": [{"text": user_content}]}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 2048},
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Gemini API HTTP {e.code}: {body}")
    except urllib.error.URLError as e:
        raise SystemExit(f"Gemini API network error: {e.reason}")

    candidates = data.get("candidates", [])
    if not candidates:
        raise SystemExit(f"empty response: {json.dumps(data)[:500]}")
    parts = candidates[0].get("content", {}).get("parts", [])
    return "".join(p.get("text", "") for p in parts).strip()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--domain", help="domain bundle name (iot, env, ai, pharmacy)")
    p.add_argument("--query", help="your question")
    p.add_argument("--model", default=DEFAULT_MODEL, help=f"Gemini model (default: {DEFAULT_MODEL})")
    p.add_argument("--list", action="store_true", help="list available bundles + exit")
    p.add_argument("--refresh-bundle", action="store_true", help="re-run export-to-notebooklm.sh before asking")
    p.add_argument("--show-context-size", action="store_true", help="print bundle size + exit")
    args = p.parse_args()

    if args.list:
        bundles = list_bundles()
        if not bundles:
            print("(no bundles — run bash scripts/export-to-notebooklm.sh <domain>)")
            return 0
        for b in bundles:
            size_kb = b.stat().st_size / 1024
            print(f"  {b.stem}\t{size_kb:.1f} KB")
        return 0

    if not args.domain:
        p.error("--domain is required (or use --list)")

    if args.refresh_bundle:
        refresh_bundle(args.domain)

    context, bundle_path = load_bundle(args.domain)

    if args.show_context_size:
        print(f"{bundle_path}: {len(context)} chars (~{len(context)//4} tokens)")
        return 0

    if not args.query:
        p.error("--query is required (unless --show-context-size or --list)")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print(
            "❌ GEMINI_API_KEY not set.\n\n"
            "Get a free key: https://aistudio.google.com/apikey\n"
            "Then: export GEMINI_API_KEY=...\n\n"
            "Fallback: upload the bundle manually to NotebookLM:\n"
            f"  open {bundle_path}\n",
            file=sys.stderr,
        )
        return 1

    answer = call_gemini(api_key, args.model, context, args.query)
    print(answer)
    return 0


if __name__ == "__main__":
    sys.exit(main())
