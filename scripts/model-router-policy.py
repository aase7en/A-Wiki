#!/usr/bin/env python3
"""Build local model-router policy from roster + volatile model intel cache.

The output is a shell-safe `.conf` file consumed by `scripts/swarm/delegate.sh`.
It stays in `.tmp/` by default so current model news does not dirty git.
"""
from __future__ import annotations

import argparse
import json
import re
import shlex
import sys
from datetime import datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROSTER = REPO_ROOT / "wiki" / "context" / "model-roster.conf"
DEFAULT_INTEL = REPO_ROOT / ".tmp" / "model-intel" / "latest.md"
DEFAULT_SCOUT = REPO_ROOT / ".tmp" / "model-scout-current.json"
DEFAULT_OUT = REPO_ROOT / ".tmp" / "model-router-policy.conf"

# Emergency seed defaults only; replaced by scout/roster at runtime.
SEED_DEFAULTS = {
    "TIER1_PRIMARY": "google/gemini-2.5-flash:free",
    "TIER1_FALLBACK1": "deepseek/deepseek-chat-v3-0324:free",
    "TIER1_FALLBACK2": "qwen/qwen3-235b-a22b:free",
    "TIER1_FALLBACK3": "meta-llama/llama-3.3-70b-instruct:free",
    "TIER2_PRIMARY": "google/gemini-2.5-flash:free",
    "TIER2_FALLBACK1": "deepseek/deepseek-r1:free",
    "TIER2_FALLBACK2": "qwen/qwen3-235b-a22b:free",
    "TIER2_FALLBACK3": "openrouter/auto",
    "TIER3_PRIMARY": "google/gemini-2.5-flash:free",
    "TIER3_FALLBACK1": "qwen/qwen3-30b-a3b:free",
    "TIER3_FALLBACK2": "openai/gpt-4o-mini",
    "RACE_MODELS": "google/gemini-2.5-flash:free deepseek/deepseek-chat-v3-0324:free qwen/qwen3-235b-a22b:free",
}


def parse_roster(path: Path) -> dict[str, str]:
    values = dict(SEED_DEFAULTS)
    if not path.exists():
        return values
    pattern = re.compile(r"^([A-Z0-9_]+)=(.*)$")
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = pattern.match(line)
        if not match:
            continue
        key, value = match.groups()
        if key not in SEED_DEFAULTS:
            continue
        try:
            parts = shlex.split(value, posix=True)
            values[key] = parts[0] if parts else ""
        except ValueError:
            values[key] = value.strip().strip('"')
    return values


def load_scout(path: Path) -> tuple[bool, dict[str, object]]:
    if not path.exists():
        return False, {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False, {}
    return (True, payload) if isinstance(payload, dict) else (False, {})


def scout_recommendation(payload: dict[str, object], role: str) -> dict[str, object]:
    recommendations = payload.get("recommendations")
    if not isinstance(recommendations, dict):
        return {}
    value = recommendations.get(role)
    return value if isinstance(value, dict) else {}


def apply_scout(values: dict[str, str], payload: dict[str, object]) -> None:
    free_current = scout_recommendation(payload, "free-current")
    cheap_capable = scout_recommendation(payload, "cheap-capable")
    platform_low = scout_recommendation(payload, "platform-low-scout")

    free_model = str(free_current.get("model_id") or "")
    cheap_model = str(cheap_capable.get("model_id") or "")
    if free_model:
        values["TIER1_PRIMARY"] = free_model
    if cheap_model:
        values["TIER2_PRIMARY"] = cheap_model

    race_models = [
        str(candidate.get("model_id"))
        for candidate in free_current.get("candidate_models", [])
        if isinstance(candidate, dict) and candidate.get("model_id")
    ]
    if race_models:
        values["RACE_MODELS"] = " ".join(race_models[:3])

    platform_provider = str(platform_low.get("provider") or "")
    platform_alias = str(platform_low.get("model_alias") or "")
    if platform_provider or platform_alias:
        values["MODEL_PLATFORM_LOW_SCOUT"] = f"{platform_provider}:{platform_alias}".strip(":")


def extract_intel_summary(path: Path, max_chars: int = 700) -> tuple[bool, str]:
    if not path.exists():
        return False, ""
    text = path.read_text(encoding="utf-8", errors="replace")
    body_lines: list[str] = []
    in_frontmatter = False
    for line in text.splitlines():
        if line.strip() == "---":
            in_frontmatter = not in_frontmatter
            continue
        if in_frontmatter or line.startswith("#"):
            continue
        clean = line.strip()
        if clean:
            body_lines.append(clean)
    summary = " ".join(" ".join(body_lines).split())
    return True, summary[:max_chars]


def shell_line(key: str, value: str) -> str:
    return f"{key}={shlex.quote(value)}"


def build_policy(roster: Path, intel: Path, scout: Path) -> tuple[dict[str, str], bool, str, bool]:
    values = parse_roster(roster)
    intel_available, intel_summary = extract_intel_summary(intel)
    scout_available, scout_payload = load_scout(scout)
    if scout_available:
        apply_scout(values, scout_payload)
    values["MODEL_ROUTER_POLICY_SOURCE"] = (
        "model-roster+model-intel+current-scout" if scout_available else "model-roster+model-intel"
    )
    values["MODEL_INTEL_AVAILABLE"] = "1" if intel_available else "0"
    values["MODEL_INTEL_PATH"] = str(intel)
    values["MODEL_INTEL_SUMMARY"] = intel_summary
    values["MODEL_SCOUT_AVAILABLE"] = "1" if scout_available else "0"
    values["MODEL_SCOUT_PATH"] = str(scout)
    values["MODEL_SCOUT_GENERATED_AT"] = str(scout_payload.get("generated_at") or "") if scout_available else ""
    values["MODEL_PLATFORM_LOW_SCOUT"] = values.get("MODEL_PLATFORM_LOW_SCOUT", "")
    values["MODEL_IDS_ARE_SEEDS"] = "0" if scout_available else "1"
    values["MODEL_ROUTER_POLICY_GENERATED_AT"] = datetime.now().isoformat(timespec="seconds")
    return values, intel_available, intel_summary, scout_available


def write_policy(path: Path, values: dict[str, str], roster: Path, scout: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = [
        "TIER1_PRIMARY",
        "TIER1_FALLBACK1",
        "TIER1_FALLBACK2",
        "TIER1_FALLBACK3",
        "TIER2_PRIMARY",
        "TIER2_FALLBACK1",
        "TIER2_FALLBACK2",
        "TIER2_FALLBACK3",
        "TIER3_PRIMARY",
        "TIER3_FALLBACK1",
        "TIER3_FALLBACK2",
        "RACE_MODELS",
        "MODEL_ROUTER_POLICY_SOURCE",
        "MODEL_ROUTER_POLICY_GENERATED_AT",
        "MODEL_INTEL_AVAILABLE",
        "MODEL_INTEL_PATH",
        "MODEL_INTEL_SUMMARY",
        "MODEL_SCOUT_AVAILABLE",
        "MODEL_SCOUT_PATH",
        "MODEL_SCOUT_GENERATED_AT",
        "MODEL_PLATFORM_LOW_SCOUT",
        "MODEL_IDS_ARE_SEEDS",
    ]
    lines = [
        "# model-router-policy.conf - local generated router policy",
        "# Generated by scripts/model-router-policy.py",
        f"# Roster: {roster}",
        f"# Scout: {scout}",
        "# Fixed model ids are seed only; replaced by scout when available.",
        "# Output is gitignored by default under .tmp/.",
        "",
    ]
    for key in ordered:
        lines.append(shell_line(key, values.get(key, "")))
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate local model router policy")
    parser.add_argument("--roster", default=str(DEFAULT_ROSTER), help="model-roster.conf path")
    parser.add_argument("--intel", default=str(DEFAULT_INTEL), help="model intel cache markdown path")
    parser.add_argument("--scout", default=str(DEFAULT_SCOUT), help="current model scout JSON path")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="output shell conf path")
    parser.add_argument("--json", action="store_true", help="print JSON summary")
    parser.add_argument("--quiet", action="store_true", help="suppress text output")
    args = parser.parse_args()

    roster = Path(args.roster)
    intel = Path(args.intel)
    scout = Path(args.scout)
    out = Path(args.out)
    values, intel_available, intel_summary, scout_available = build_policy(roster, intel, scout)
    write_policy(out, values, roster, scout)

    payload = {
        "policy_path": str(out),
        "roster_path": str(roster),
        "intel_path": str(intel),
        "scout_path": str(scout),
        "intel_available": intel_available,
        "scout_available": scout_available,
        "intel_summary_chars": len(intel_summary),
        "tiers": {key: values[key] for key in values if key.startswith("TIER") or key == "RACE_MODELS"},
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif not args.quiet:
        print(f"model router policy written: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
