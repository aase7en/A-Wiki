#!/usr/bin/env python3
"""
scrape-advanced.py — Multi-tier web scraper router for A-Wiki.

Routes URL scraping to the best available method based on device tier and
installed dependencies. Gracefully degrades when methods are unavailable.

Tier  0: curl-impersonate (TLS fingerprint, no browser)
Tier  1: Scrapling / AutoScraper (lightweight, no browser)
Tier  2: Crawl4AI (RAG-optimized, needs Playwright)
Tier  3: Firecrawl API (cloud, needs API key)
Tier  4: Browser Use (agentic browser, MacBook only)

Usage:
    python3 scripts/wiki/scrape-advanced.py --url <url> [--method auto|scrapling|...]
                                                   [--domain <domain>] [--json] [--list]
"""
from __future__ import annotations
import argparse
import json
import os
import re
import subprocess
import sys
import time
import unicodedata
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
RAW_DIR = REPO_ROOT / "raw"

# Import shared domain constants from lib (F8 dedup — was inline tuple)
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from lib.wiki_domains import VALID_DOMAINS  # noqa: E402

# ── Reused helpers from ingest-source.py (copied to avoid import magic) ────

def slugify(text: str) -> str:
    """Convert text to a safe filesystem slug."""
    text = text.lower().strip()
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text.strip("-")


def frontmatter(**kwargs) -> str:
    """Generate YAML-ish frontmatter."""
    lines = ["---"]
    for k, v in kwargs.items():
        if isinstance(v, list):
            items = ", ".join(f'"{x}"' for x in v)
            lines.append(f"{k}: [{items}]")
        elif isinstance(v, bool):
            lines.append(f"{k}: {'true' if v else 'false'}")
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    return "\n".join(lines)

# Valid domains imported from lib.wiki_domains above (F8 dedup).

# Tier metadata for --list
TIERS: list[dict] = [
    {"method": "curl-impersonate", "tier": 0, "pkg": None, "binary": "curl-impersonate-chrome", "devices": "all", "desc": "TLS-fingerprint curl (bypass Cloudflare)"},
    {"method": "scrapling",        "tier": 1, "pkg": "scrapling",         "binary": None,        "devices": "all",        "desc": "Adaptive lightweight scraper"},
    {"method": "autoscraper",      "tier": 1, "pkg": "autoscraper",       "binary": None,        "devices": "all",        "desc": "Exemplar-based pattern extraction"},
    {"method": "crawl4ai",         "tier": 2, "pkg": "crawl4ai",          "binary": None,        "devices": "macbook",     "desc": "LLM/RAG-optimized crawler"},
    {"method": "firecrawl",        "tier": 3, "pkg": "firecrawl",         "binary": None,        "devices": "all",        "desc": "Cloud API: web to Markdown"},
    {"method": "browser-use",      "tier": 4, "pkg": "browser_use",       "binary": None,        "devices": "macbook",     "desc": "Agentic browser control"},
]


# ── Device detection ───────────────────────────────────────────────────────

def detect_device() -> str:
    """Read ~/.wiki-device; fall back to display-server detection."""
    device_file = Path.home() / ".wiki-device"
    if device_file.is_file():
        return device_file.read_text(encoding="utf-8").strip()
    # Headless detection: no DISPLAY on Linux, no window server check on macOS
    if sys.platform == "linux" and not os.environ.get("DISPLAY"):
        return "pi5"
    if sys.platform == "darwin":
        # macOS is always a GUI machine in practice
        return "home-mac"
    return "unknown"


def device_allows(method: str, device: str) -> bool:
    """Check if the given method can run on this device."""
    restricted_on_pi5 = {"crawl4ai", "browser-use"}
    if device == "pi5" and method in restricted_on_pi5:
        return False
    return True


# ── Save raw output ────────────────────────────────────────────────────────

def save_raw_output(url: str, text: str) -> Path:
    """Save scraped content to ``raw/<slug>.md`` (Iron Law #7 provenance)."""
    slug = slugify(url.split("/")[-1].split("?")[0] or "scraped-page")
    if not slug:
        slug = "scraped-page"
    raw_path = RAW_DIR / f"{slug}.md"
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(text, encoding="utf-8")
    print(f"💾 Raw saved: {raw_path}", file=sys.stderr)
    return raw_path


# ── Adapters ───────────────────────────────────────────────────────────────

def _scrape_curl_impersonate(url: str) -> str | None:
    """Tier 0 — curl-impersonate binary (TLS fingerprint: chrome)."""
    import shutil
    for bin_name in ("curl-impersonate-chrome", "curl-impersonate"):
        bin_path = shutil.which(bin_name)
        if bin_path:
            try:
                result = subprocess.run(
                    [bin_path, "-sL", "--max-time", "20", url],
                    capture_output=True, text=True, timeout=30,
                )
                if result.returncode == 0 and result.stdout.strip():
                    return result.stdout
            except Exception:
                continue
    return None


def _scrape_scrapling(url: str) -> str | None:
    """Tier 1 — Scrapling adaptive fetch."""
    from scrapling import Fetcher  # type: ignore[import-untyped]
    f = Fetcher()
    resp = f.get(url)
    if resp and resp.text:
        return resp.text
    return None


def _scrape_autoscraper(url: str, wanted_list: list[str] | None = None) -> str | None:
    """Tier 1 — AutoScraper exemplar-based extraction.

    In non-wizard mode, returns the full page HTML as text.
    """
    from autoscraper import AutoScraper  # type: ignore[import-untyped]
    scraper = AutoScraper()
    if wanted_list:
        result = scraper.get_result_similar(url, wanted_list)
        if result:
            return "\n".join(str(item) for item in result)
    # Full page fetch
    result = scraper.build(url, [".*"])  # type: ignore[arg-type]
    # Return readable text
    text = "\n".join(str(item) for item in result)
    return text if text.strip() else None


def _scrape_crawl4ai(url: str) -> str | None:
    """Tier 2 — Crawl4AI with RAG-friendly output."""
    from crawl4ai import AsyncWebCrawler  # type: ignore[import-untyped]
    import asyncio

    async def _run() -> str | None:
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=url)
            if result and result.markdown:
                return result.markdown
            if result and result.text:
                return result.text
            return None

    return asyncio.run(_run())


def _scrape_firecrawl(url: str) -> str | None:
    """Tier 3 — Firecrawl cloud API."""
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from lib.drive_secrets import fetch_secret  # type: ignore[import-untyped]

    api_key = fetch_secret("FIRECRAWL_API_KEY")
    if not api_key:
        print("warn: FIRECRAWL_API_KEY not found in drive/.secrets", file=sys.stderr)
        print("hint: echo 'FIRECRAWL_API_KEY=sk-...' >> drive/.secrets", file=sys.stderr)
        return None

    try:
        import requests
    except ImportError:
        print("warn: requests not installed — firecrawl adapter unavailable", file=sys.stderr)
        return None

    resp = requests.post(
        "https://api.firecrawl.dev/v1/scrape",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"url": url, "formats": ["markdown"]},
        timeout=30,
    )
    if resp.status_code == 200:
        data = resp.json()
        if data.get("success") and data.get("data"):
            md = data["data"].get("markdown") or data["data"].get("content") or ""
            return md if md.strip() else None
    elif resp.status_code == 429:
        print("warn: Firecrawl rate-limited (429) — wait and retry", file=sys.stderr)
        return None
    else:
        print(f"warn: Firecrawl API error {resp.status_code}: {resp.text[:200]}", file=sys.stderr)
        return None


def _scrape_browser_use(url: str, task: str | None = None) -> str | None:
    """Tier 4 — Browser Use agentic browser control (MacBook only)."""
    from browser_use import Agent  # type: ignore[import-untyped]
    from langchain_openai import ChatOpenAI  # type: ignore[import-untyped]

    task_str = task or f"Navigate to {url} and extract all visible text content, then return it."
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    agent = Agent(task=task_str, llm=llm)
    result = agent.run()
    return result if result else None


# ── Method registry ────────────────────────────────────────────────────────

def list_methods(device: str) -> list[dict]:
    """Return available methods with installed status, grouped by tier."""
    methods: list[dict] = []
    for info in TIERS:
        available = device_allows(info["method"], device)
        installed = True
        if info["binary"]:
            import shutil
            installed = shutil.which(info["binary"]) is not None
        elif info["pkg"]:
            installed = _pkg_installed(info["pkg"])
        methods.append({
            "method": info["method"],
            "tier": info["tier"],
            "available": available,
            "installed": installed,
            "desc": info["desc"],
        })
    return methods


def _pkg_installed(pkg: str) -> bool:
    """Check if a Python package is importable."""
    import importlib.util
    pkg_import = pkg.replace("-", "_")
    return importlib.util.find_spec(pkg_import) is not None


ADAPTERS: dict[str, callable] = {
    "curl-impersonate": _scrape_curl_impersonate,
    "scrapling": _scrape_scrapling,
    "autoscraper": _scrape_autoscraper,
    "crawl4ai": _scrape_crawl4ai,
    "firecrawl": _scrape_firecrawl,
    "browser-use": _scrape_browser_use,
}


# ── Main dispatch ──────────────────────────────────────────────────────────

def scrape(
    url: str,
    method: str = "auto",
    force_method: bool = False,
    wizard: bool = False,
    domain: str | None = None,
    save_raw: bool = True,
    json_out: bool = False,
) -> dict:
    """Scrape a URL and return result metadata."""
    device = detect_device()
    result: dict = {
        "url": url,
        "device": device,
        "method_used": None,
        "methods_tried": [],
        "content_length": 0,
        "raw_file": None,
        "error": None,
    }

    if method != "auto" and not force_method:
        # Try the requested method first, fall back to auto if it fails
        pass

    if method == "auto":
        methods_to_try = [m["method"] for m in TIERS if device_allows(m["method"], device)]
    elif force_method:
        methods_to_try = [method]
    else:
        methods_to_try = [method] + [m["method"] for m in TIERS if m["method"] != method and device_allows(m["method"], device)]

    text: str | None = None
    for m in methods_to_try:
        adapter = ADAPTERS.get(m)
        if not adapter:
            continue
        if not device_allows(m, device):
            result["methods_tried"].append({"method": m, "status": "blocked_by_device"})
            continue
        try:
            print(f"  trying: {m}...", file=sys.stderr)
            if m == "autoscraper" and wizard:
                print("(AutoScraper wizard mode — provide example items)", file=sys.stderr)
                print("Press Ctrl+D when done, or type example items, one per line:", file=sys.stderr)
                wanted = [line.strip() for line in sys.stdin if line.strip()]
                text = adapter(url, wanted_list=wanted or None)
            else:
                text = adapter(url)
            if text:
                result["method_used"] = m
                result["methods_tried"].append({"method": m, "status": "success"})
                result["content_length"] = len(text)
                break
            result["methods_tried"].append({"method": m, "status": "no_content"})
        except ImportError as e:
            result["methods_tried"].append({"method": m, "status": "not_installed", "detail": str(e)})
        except Exception as e:
            result["methods_tried"].append({"method": m, "status": "error", "detail": str(e)})

    if text is None:
        result["error"] = "all methods failed"
        if json_out:
            return result
        print("error: all scraping methods failed", file=sys.stderr)
        return result

    # Save raw output (Iron Law #7)
    if save_raw:
        raw_path = save_raw_output(url, text)
        result["raw_file"] = str(raw_path)

    if json_out:
        return result

    print(f"✅ {result['method_used']} — {result['content_length']} chars", file=sys.stderr)
    print(text)
    return result


# ── CLI ────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-tier web scraper for A-Wiki")
    parser.add_argument("--url", help="URL to scrape")
    parser.add_argument(
        "--method", default="auto",
        choices=["auto", "curl-impersonate", "scrapling", "autoscraper", "crawl4ai", "firecrawl", "browser-use"],
        help="Scraping method (default: auto-pick from installed+allowed)",
    )
    parser.add_argument("--domain", choices=VALID_DOMAINS, help="Knowledge domain (for raw/ organization)")
    parser.add_argument("--save-raw", help="Override raw output path")
    parser.add_argument("--fallback", action="store_true", help="Allow fallback to other methods if chosen method fails")
    parser.add_argument("--wizard", action="store_true", help="AutoScraper exemplar wizard (prompts for examples)")
    parser.add_argument("--list", action="store_true", help="List available scraping methods")
    parser.add_argument("--json", action="store_true", help="Output result JSON (compact, for agent consumption)")

    args = parser.parse_args()

    if args.list:
        device = detect_device()
        methods = list_methods(device)
        print(f"Device: {device}")
        print(f"{'Method':<20} {'Tier':<6} {'Available':<10} {'Installed':<10} Description")
        print("-" * 80)
        for m in methods:
            av = "✅" if m["available"] else "❌"
            inst = "✅" if m["installed"] else "❌"
            print(f"{m['method']:<20} {m['tier']:<6} {av:<10} {inst:<10} {m['desc']}")
        return

    if not args.url:
        parser.print_help()
        sys.exit(1)

    result = scrape(
        url=args.url,
        method=args.method,
        force_method=not args.fallback,
        wizard=args.wizard,
        domain=args.domain,
        save_raw=not args.save_raw or True,
        json_out=args.json,
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))

    if result.get("error"):
        sys.exit(1)


if __name__ == "__main__":
    main()
