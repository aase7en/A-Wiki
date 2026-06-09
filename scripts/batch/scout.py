"""
scout.py — Discover cheaper / better models, refresh the free-tier roster,
and propose updates to cost-routing.conf.

The cost matrix is NOT fixed: new free models drop weekly, providers shift
prices, and rate limits change. Run this manually (or on a schedule) and
review the diff before applying.

Usage:
    python scripts/batch/scout.py --refresh
        Pull OpenRouter free list, cache to drive/batch-state/free-roster.json.

    python scripts/batch/scout.py --benchmark <model-id>
        Run a small fixture against the model, print pass/fail.

    python scripts/batch/scout.py --propose
        Write wiki/context/cost-routing.conf.proposed showing what would change.

    python scripts/batch/scout.py --apply
        After user reviews the .proposed file, swap it into place atomically.

Reuses agent-skills/swarm-intelligence/model-scouter.md (Tier 1 OpenRouter
free filter, Tier 3 Ollama fallback) — read that doc first for the philosophy.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "batch"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

from drive_secrets import fetch_secret  # noqa: E402, F401

from config import CONF_PATH, get_tier_config, load_conf  # noqa: E402
from state import state_dir  # noqa: E402

ROSTER_FILE = "free-roster.json"
PROVIDER_CACHE_FILE = "provider-pricing-cache.json"
OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"
CACHE_TTL_SECONDS = 24 * 3600


def _http_get_json(url: str, headers: dict | None = None, timeout: int = 30) -> Any:
    request = urllib.request.Request(url, headers=headers or {}, method="GET")
    with urllib.request.urlopen(request, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def refresh_openrouter_free() -> dict:
    """Pull OpenRouter /models and filter for free (input + output == 0)."""
    data = _http_get_json(OPENROUTER_MODELS_URL)
    free: list[dict] = []
    for m in data.get("data", []):
        pricing = m.get("pricing", {}) or {}
        try:
            prompt_price = float(pricing.get("prompt", "0") or "0")
            completion_price = float(pricing.get("completion", "0") or "0")
        except (TypeError, ValueError):
            continue
        if prompt_price == 0.0 and completion_price == 0.0:
            free.append({
                "id": m.get("id"),
                "name": m.get("name"),
                "context_length": m.get("context_length"),
                "architecture": m.get("architecture", {}).get("modality"),
            })
    return {
        "scouted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": OPENROUTER_MODELS_URL,
        "count": len(free),
        "models": sorted(free, key=lambda x: -(x.get("context_length") or 0)),
    }


def cache_roster(payload: dict) -> Path:
    path = state_dir() / ROSTER_FILE
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def read_cached_roster() -> dict | None:
    path = state_dir() / ROSTER_FILE
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def pick_best_free(roster: dict, prefer_keywords: tuple[str, ...] = ("gemini", "flash", "qwen", "deepseek")) -> str | None:
    """Pick the top free model by context length + keyword preference."""
    models = roster.get("models", [])
    if not models:
        return None

    def score(m: dict) -> tuple[int, int]:
        ctx = m.get("context_length") or 0
        mid = (m.get("id") or "").lower()
        kw_hit = sum(1 for k in prefer_keywords if k in mid)
        return (kw_hit, ctx)

    best = max(models, key=score)
    return best.get("id")


def benchmark_candidate(model_id: str, *, provider: str = "openrouter") -> dict:
    """Run a tiny fixture against the candidate; assert it produces valid frontmatter.

    Used to gate "should we promote this model to Tier 0/1?". Costs ~$0 (free
    tier) or a few cents (paid candidate).
    """
    from adapters import IngestRequest
    from quality_gate import validate

    fixture_path = REPO_ROOT / "tests" / "fixtures" / "scout-bench.md"
    if not fixture_path.is_file():
        return {"ok": False, "reason": f"fixture missing: {fixture_path}"}

    raw_rel = "raw/.scout-bench.md"
    raw_target = REPO_ROOT / raw_rel
    raw_target.parent.mkdir(parents=True, exist_ok=True)
    raw_target.write_text(fixture_path.read_text(encoding="utf-8"), encoding="utf-8")

    try:
        req = IngestRequest(
            raw_path=raw_rel, slug="scout-bench",
            custom_id="scout-bench-0001",
            date_ingested=datetime.now(timezone.utc).date().isoformat(),
            tier=0,
        )
        if provider == "openrouter":
            from adapters.openrouter_free import OpenRouterFreeAdapter
            cfg = {
                "model": f"openrouter:{model_id}",
                "endpoint": "https://openrouter.ai/api/v1",
                "secret_name": "OPENROUTER_API_KEY",
            }
            adapter = OpenRouterFreeAdapter(cfg)
        else:
            return {"ok": False, "reason": f"unsupported provider: {provider}"}

        submitted = adapter.submit([req])
        result = submitted["results"][0]
        if not result.success:
            return {"ok": False, "reason": result.error, "model": model_id}

        ok, reason = validate(
            result.content.strip(), expected_slug="scout-bench", expected_raw_path=raw_rel,
        )
        return {
            "ok": ok, "reason": reason, "model": model_id,
            "tokens_in": result.tokens_in, "tokens_out": result.tokens_out,
        }
    finally:
        try:
            raw_target.unlink()
        except OSError:
            pass


def propose_changes() -> dict:
    """Read live roster + current cost-routing.conf, produce a diff proposal."""
    roster = read_cached_roster() or refresh_openrouter_free()
    conf = load_conf()
    proposals: list[dict] = []

    if conf.has_section("tier_0"):
        current = get_tier_config(conf, 0)
        best_id = pick_best_free(roster)
        cur_model = (current.get("model") or "").replace("openrouter:", "")
        if best_id and best_id != cur_model:
            proposals.append({
                "section": "tier_0",
                "key": "model",
                "current": current.get("model"),
                "proposed": f"openrouter:{best_id}",
                "reason": f"Higher-context free model available ({best_id})",
            })

    return {
        "scouted_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "n_free_models": len(roster.get("models", [])),
        "proposals": proposals,
    }


def write_proposed(diff: dict) -> Path:
    """Write cost-routing.conf.proposed with the diff embedded as a comment block."""
    proposed = CONF_PATH.with_suffix(".conf.proposed")
    current_text = CONF_PATH.read_text(encoding="utf-8")
    header = ["# === SCOUT PROPOSAL ===", f"# Generated: {diff['scouted_at']}"]
    if not diff["proposals"]:
        header.append("# (no changes proposed — current config is already optimal)")
    else:
        for p in diff["proposals"]:
            header.append(
                f"# [{p['section']}] {p['key']}: {p['current']!r} → {p['proposed']!r}"
            )
            header.append(f"#   reason: {p['reason']}")
    header.append("# Apply: python scripts/batch/scout.py --apply")
    header.append("# Discard: rm " + str(proposed.relative_to(REPO_ROOT)))
    header.append("# =====================")
    proposed.write_text("\n".join(header) + "\n\n" + current_text, encoding="utf-8")
    return proposed


def apply_proposed() -> Path:
    """Apply a previously-generated .proposed file by editing the active conf."""
    proposed = CONF_PATH.with_suffix(".conf.proposed")
    if not proposed.is_file():
        raise FileNotFoundError(f"No proposal at {proposed} — run --propose first")
    diff = propose_changes()
    if not diff["proposals"]:
        proposed.unlink()
        return CONF_PATH

    import configparser
    conf = load_conf()
    for p in diff["proposals"]:
        section = p["section"]
        if conf.has_section(section):
            conf.set(section, p["key"], p["proposed"])

    backup = CONF_PATH.with_suffix(".conf.bak")
    shutil.copy2(CONF_PATH, backup)
    with CONF_PATH.open("w", encoding="utf-8") as fp:
        conf.write(fp)
    proposed.unlink()
    return CONF_PATH


def main() -> int:
    parser = argparse.ArgumentParser(description="A-Wiki model scout: refresh and propose updates")
    parser.add_argument("--refresh", action="store_true", help="Pull OpenRouter free list and cache")
    parser.add_argument("--benchmark", help="Test a specific model id (free tier only)")
    parser.add_argument("--propose", action="store_true", help="Write cost-routing.conf.proposed")
    parser.add_argument("--apply", action="store_true", help="Apply a previously-generated proposal")
    parser.add_argument("--show", action="store_true", help="Show cached roster summary")
    args = parser.parse_args()

    if args.refresh:
        try:
            roster = refresh_openrouter_free()
        except (urllib.error.URLError, urllib.error.HTTPError) as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        path = cache_roster(roster)
        print(f"✓ cached {roster['count']} free models → {path}")
        return 0

    if args.benchmark:
        result = benchmark_candidate(args.benchmark)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result.get("ok") else 1

    if args.propose:
        diff = propose_changes()
        path = write_proposed(diff)
        print(f"✓ wrote {path.relative_to(REPO_ROOT)} ({len(diff['proposals'])} proposed change(s))")
        for p in diff["proposals"]:
            print(f"  - [{p['section']}] {p['key']}: {p['current']!r} → {p['proposed']!r}")
        return 0

    if args.apply:
        try:
            path = apply_proposed()
        except FileNotFoundError as e:
            print(f"error: {e}", file=sys.stderr)
            return 1
        print(f"✓ applied → {path.relative_to(REPO_ROOT)}  (backup: {path.with_suffix('.conf.bak').name})")
        return 0

    if args.show:
        roster = read_cached_roster()
        if roster is None:
            print("(no cached roster — run --refresh)")
            return 1
        print(f"Roster scouted: {roster['scouted_at']}")
        print(f"Free models found: {roster['count']}")
        for m in roster["models"][:15]:
            ctx = m.get("context_length") or 0
            print(f"  {m.get('id'):60s}  ctx={ctx}")
        if len(roster["models"]) > 15:
            print(f"  ... and {len(roster['models']) - 15} more")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
