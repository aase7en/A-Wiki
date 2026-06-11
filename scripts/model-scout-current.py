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
        if model_id.endswith(":free") or (prompt == 0 and completion == 0):
            free.append(candidate)
        elif prompt is not None and completion is not None:
            paid.append((prompt + completion, candidate))
    paid.sort(key=lambda row: row[0])
    result["status"] = "ok"
    result["free_candidates"] = free[:8]
    result["cheap_candidates"] = [candidate for _, candidate in paid[:8]]
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


def build_payload(offline: bool, timeout: int) -> dict[str, Any]:
    openrouter = scout_openrouter(offline, timeout)
    return {
        "generated_at": now_iso(),
        "volatile": True,
        "offline": offline,
        "sources": SOURCES,
        "providers": {
            "openrouter": openrouter,
            "deepseek": scout_deepseek(offline, timeout),
            "platform_agents": platform_agents(),
        },
        "recommendations": recommendations(openrouter),
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
    parser.add_argument("--json", action="store_true", help="print JSON summary")
    parser.add_argument("--quiet", action="store_true", help="suppress text output")
    args = parser.parse_args()

    out = Path(args.out)
    report = Path(args.report)
    payload = build_payload(args.offline, args.timeout)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(report, payload)

    summary = {
        "scout_path": str(out),
        "report_path": str(report),
        "generated_at": payload["generated_at"],
        "offline": payload["offline"],
        "openrouter_status": payload["providers"]["openrouter"]["status"],
        "deepseek_status": payload["providers"]["deepseek"]["status"],
    }
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    elif not args.quiet:
        print(f"model scout written: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
