#!/usr/bin/env python3
"""Scout volatile model availability and pricing before routing work."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = REPO_ROOT / ".tmp" / "model-scout-current.json"
DEFAULT_REPORT = REPO_ROOT / ".tmp" / "model-scout-current.md"
DEFAULT_CATALOG = REPO_ROOT / ".tmp" / "model-catalog.json"

SOURCES = [
    {"label": "DeepSeek pricing", "url": "https://api-docs.deepseek.com/quick_start/pricing", "volatile": True},
    {"label": "DeepSeek V4 release", "url": "https://api-docs.deepseek.com/news/news260424", "volatile": True},
    {
        "label": "OpenRouter Models API",
        "url": "https://openrouter.ai/docs/api/api-reference/models/get-models",
        "api_url": "https://openrouter.ai/api/v1/models",
        "volatile": True,
    },
    {"label": "OpenRouter model guide", "url": "https://openrouter.ai/docs/guides/overview/models", "volatile": True},
]

PLATFORM_AGENTS = [
    ("claude", "Claude Code", "current low/default model via Claude CLI when available"),
    ("codex", "Codex", "current Codex CLI/model picker behavior"),
    ("gemini", "Gemini CLI", "current Gemini default model"),
    ("cursor", "Cursor", "IDE model picker; manual verification if CLI unavailable"),
    ("windsurf", "Windsurf", "IDE model picker; manual verification if CLI unavailable"),
    ("antigravity", "Antigravity", "CLI/API detection when installed"),
    ("manus", "Manus", "CLI/API detection when installed"),
    ("devin", "Devin", "CLI/API detection when installed"),
    ("perplexity", "Perplexity", "CLI/API detection when installed"),
    ("groq", "Groq", "API/CLI detection when installed"),
]


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def price_float(raw: Any) -> float | None:
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def fetch_json(url: str, timeout: int, headers: dict[str, str] | None = None) -> dict[str, Any]:
    request = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def scout_openrouter(offline: bool, timeout: int) -> dict[str, Any]:
    result: dict[str, Any] = {
        "provider": "openrouter",
        "source": "https://openrouter.ai/api/v1/models",
        "status": "skipped" if offline else "unknown",
        "free_candidates": [],
        "cheap_candidates": [],
    }
    if offline:
        result["note"] = "offline mode; run live scout for current model ids"
        return result
    headers: dict[str, str] = {}
    if os.environ.get("OPENROUTER_API_KEY"):
        headers["Authorization"] = f"Bearer {os.environ['OPENROUTER_API_KEY']}"
    try:
        payload = fetch_json("https://openrouter.ai/api/v1/models", timeout, headers)
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        result["status"] = "error"
        result["error"] = type(exc).__name__
        return result
    free: list[dict[str, Any]] = []
    paid: list[tuple[float, dict[str, Any]]] = []
    all_candidates: list[dict[str, Any]] = []
    for item in payload.get("data", []):
        model_id = str(item.get("id", ""))
        pricing = item.get("pricing") or {}
        prompt = price_float(pricing.get("prompt"))
        completion = price_float(pricing.get("completion"))
        candidate = {
            "model_id": model_id,
            "name": item.get("name", model_id),
            "context_length": item.get("context_length"),
            "prompt_price": pricing.get("prompt"),
            "completion_price": pricing.get("completion"),
            "volatile": True,
        }
        all_candidates.append(candidate)
        if model_id.endswith(":free") or (prompt == 0 and completion == 0):
            free.append(candidate)
        elif prompt is not None and completion is not None:
            paid.append((prompt + completion, candidate))
    paid.sort(key=lambda row: row[0])
    result["status"] = "ok"
    result["free_candidates"] = free[:8]
    result["cheap_candidates"] = [candidate for _, candidate in paid[:8]]
    # full normalized list (consumed by build_catalog, then dropped from payload to stay lean)
    result["all_candidates"] = all_candidates[:400]
    result["model_count"] = len(payload.get("data", []))
    return result


def scout_deepseek(offline: bool, timeout: int) -> dict[str, Any]:
    result: dict[str, Any] = {
        "provider": "deepseek",
        "source": "https://api.deepseek.com/models",
        "pricing_source": "https://api-docs.deepseek.com/quick_start/pricing",
        "status": "skipped" if offline else "unknown",
        "models": [],
        "note": "pricing must be checked live before choosing",
    }
    if offline:
        return result
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        result["status"] = "skip-no-key"
        return result
    try:
        payload = fetch_json("https://api.deepseek.com/models", timeout, {"Authorization": f"Bearer {api_key}"})
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        result["status"] = "error"
        result["error"] = type(exc).__name__
        return result
    result["status"] = "ok"
    result["models"] = payload.get("data", [])
    return result


def platform_agents() -> list[dict[str, Any]]:
    rows = []
    for command, label, behavior in PLATFORM_AGENTS:
        path = shutil.which(command)
        rows.append(
            {
                "agent": command,
                "label": label,
                "available": bool(path),
                "path": path or "",
                "scout_behavior": behavior,
                "manual_verification_required": not bool(path),
            }
        )
    return rows


def recommendations(openrouter: dict[str, Any]) -> dict[str, dict[str, Any]]:
    free_candidates = openrouter.get("free_candidates") or []
    cheap_candidates = openrouter.get("cheap_candidates") or []
    free_choice = free_candidates[0] if free_candidates else {}
    cheap_choice = cheap_candidates[0] if cheap_candidates else {}
    return {
        "free-current": {
            "role": "free-current",
            "provider": "openrouter" if free_choice else "dynamic-roster",
            "model_id": free_choice.get("model_id", ""),
            "candidate_models": free_candidates[:5],
            "selection_policy": "free/current dynamic roster; scout before route",
            "volatile": True,
        },
        "cheap-capable": {
            "role": "cheap-capable",
            "provider": "provider-alias",
            "model_id": cheap_choice.get("model_id", ""),
            "candidate_models": cheap_candidates[:5],
            "selection_policy": "cheapest capable paid route discovered at runtime",
            "volatile": True,
        },
        "platform-low-scout": {
            "role": "platform-low-scout",
            "provider": "platform-agent",
            "model_alias": "current-low-default",
            "selection_policy": "ask current low/default model to scout current pricing/capability",
            "volatile": True,
        },
        "platform-primary": {
            "role": "platform-primary",
            "provider": "current-platform",
            "model_alias": "current-primary",
            "selection_policy": "use only after scout says lower tiers are insufficient",
            "volatile": True,
        },
    }


# ── Catalog: classify primary (flagship) vs secondary (cheap/fast/free) ─────
# Keyword + price heuristic, deterministic and explainable. Provider is parsed
# from the model id prefix (OpenRouter aggregates z-ai, anthropic, google, ...).
CHEAP_KEYWORDS = ("flash", "mini", "-air", " air", "lite", "nano", "fast", " small", "tiny", "haiku")
FLAGSHIP_KEYWORDS = (
    "opus", "ultra", "-max", " max", "glm-4.6", "405b", "671b", "235b",
    "reasoner", "-r1", ":r1", "sonnet", "-pro", " pro", "-large", " large",
)
PRIMARY_PRICE_FLOOR = 1.5e-5  # prompt+completion per token → treat as flagship tier


def classify_model(entry: dict[str, Any]) -> dict[str, Any]:
    """Return entry augmented with role (primary|secondary) + tier_hint (L1-L4)."""
    mid = str(entry.get("model_id", "")).lower()
    name = str(entry.get("name", "") or "").lower()
    text = mid + " " + name
    try:
        total = float(entry.get("prompt_price")) + float(entry.get("completion_price"))
    except (TypeError, ValueError):
        total = None
    is_free = mid.endswith(":free") or total == 0
    cheap_kw = any(k in text for k in CHEAP_KEYWORDS)
    flagship_kw = any(k in text for k in FLAGSHIP_KEYWORDS)

    if is_free:
        role, tier = "secondary", "L1"
    elif cheap_kw:
        role, tier = "secondary", "L2"
    elif flagship_kw:
        role, tier = "primary", "L4"
    elif total is not None and total > 0:
        role, tier = ("primary", "L4") if total >= PRIMARY_PRICE_FLOOR else ("secondary", "L2")
    else:
        role, tier = "primary", "L3"

    out = dict(entry)
    out["role"] = role
    out["tier_hint"] = tier
    return out


def build_catalog(
    openrouter: dict[str, Any] | None,
    deepseek: dict[str, Any] | None = None,
    per_provider_limit: int = 6,
) -> dict[str, Any]:
    """Group scouted models by provider into primary/secondary buckets for the chooser."""
    models: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(entry: dict[str, Any], provider: str | None = None) -> None:
        mid = str(entry.get("model_id", ""))
        if not mid or mid in seen:
            return
        seen.add(mid)
        classified = classify_model(entry)
        classified["provider"] = provider or (mid.split("/")[0] if "/" in mid else "direct")
        models.append(classified)

    if isinstance(openrouter, dict) and openrouter.get("status") == "ok":
        for entry in openrouter.get("all_candidates", []) or []:
            add(entry)
    if isinstance(deepseek, dict) and deepseek.get("status") == "ok":
        for m in deepseek.get("models", []) or []:
            mid = str(m.get("id", ""))
            if mid:
                add(
                    {
                        "model_id": mid if "/" in mid else f"deepseek/{mid}",
                        "name": mid,
                        "context_length": None,
                        "prompt_price": None,
                        "completion_price": None,
                    },
                    provider="deepseek",
                )

    by_provider: dict[str, dict[str, list]] = {}
    for m in models:
        bucket = by_provider.setdefault(m["provider"], {"primary": [], "secondary": []})
        bucket[m["role"]].append(m)
    for bucket in by_provider.values():
        for role in ("primary", "secondary"):
            bucket[role].sort(key=lambda x: (x.get("context_length") or 0), reverse=True)
            bucket[role] = bucket[role][:per_provider_limit]

    trimmed = [m for bucket in by_provider.values() for m in (bucket["primary"] + bucket["secondary"])]
    return {
        "providers": sorted(by_provider.keys()),
        "models": trimmed,
        "by_provider": by_provider,
        "model_count": len(models),
    }


def build_payload(offline: bool, timeout: int) -> dict[str, Any]:
    openrouter = scout_openrouter(offline, timeout)
    deepseek = scout_deepseek(offline, timeout)
    catalog = build_catalog(openrouter, deepseek)
    catalog["generated_at"] = now_iso()
    # all_candidates was only needed to build the catalog; drop it to keep payload lean
    openrouter.pop("all_candidates", None)
    return {
        "generated_at": now_iso(),
        "volatile": True,
        "offline": offline,
        "sources": SOURCES,
        "providers": {
            "openrouter": openrouter,
            "deepseek": deepseek,
            "platform_agents": platform_agents(),
        },
        "recommendations": recommendations(openrouter),
        "catalog": catalog,
        "scout_prompt": "Scout current model availability, pricing, and capability without hardcoding versions.",
    }


def write_report(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Current Model Scout Report",
        "",
        f"- generated_at: {payload['generated_at']}",
        "- volatile: true",
        "- policy: scout current model/pricing before choosing a route",
        "- warning: model examples are dated examples only, never binding defaults",
        "",
        "## Runtime Roles",
        "",
    ]
    for role, data in payload["recommendations"].items():
        model_id = data.get("model_id") or data.get("model_alias") or "discovered at runtime"
        lines.append(f"- `{role}`: {model_id}")
    lines.extend(["", "## Sources", ""])
    for source in payload["sources"]:
        lines.append(f"- {source['label']}: {source['url']}")
    lines.extend(
        [
            "",
            "## Dated Examples",
            "",
            "- DeepSeek V4 Flash/Pro can be reviewed as a current example only after live scout confirms price and availability.",
            "- OpenRouter free candidates are runtime candidates from the Models API, not durable policy.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Scout current model availability/pricing")
    parser.add_argument("--offline", action="store_true", help="skip network probes")
    parser.add_argument("--timeout", type=int, default=8, help="network timeout seconds")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="JSON output path")
    parser.add_argument("--report", default=str(DEFAULT_REPORT), help="Markdown report path")
    parser.add_argument("--catalog", default=str(DEFAULT_CATALOG), help="model catalog JSON path (chooser input)")
    parser.add_argument("--json", action="store_true", help="print JSON summary")
    parser.add_argument("--quiet", action="store_true", help="suppress text output")
    args = parser.parse_args()

    out = Path(args.out)
    report = Path(args.report)
    catalog_path = Path(args.catalog)
    payload = build_payload(args.offline, args.timeout)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(report, payload)
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    catalog_path.write_text(json.dumps(payload["catalog"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    summary = {
        "scout_path": str(out),
        "report_path": str(report),
        "catalog_path": str(catalog_path),
        "generated_at": payload["generated_at"],
        "offline": payload["offline"],
        "openrouter_status": payload["providers"]["openrouter"]["status"],
        "deepseek_status": payload["providers"]["deepseek"]["status"],
        "catalog_model_count": payload["catalog"].get("model_count", 0),
    }
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    elif not args.quiet:
        print(f"model scout written: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
