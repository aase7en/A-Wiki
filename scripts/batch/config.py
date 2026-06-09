"""
config.py — Load and resolve the cost-routing policy.

Reads `wiki/context/cost-routing.conf` (single source of truth) and applies
the resolution order: CLI flag > ENV var > conf file > built-in defaults.

Used by:
  - scripts/batch/router.py        (tier selection)
  - scripts/batch/route.py         (CLI entry)
  - scripts/batch/adapters/*.py    (per-tier provider config)
  - scripts/batch/mcp_tools.py     (MCP exposure)
"""
from __future__ import annotations

import configparser
import os
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
CONF_PATH = REPO_ROOT / "wiki" / "context" / "cost-routing.conf"

_BUILTIN_DEFAULTS = {
    "ingest_tier": 1,
    "escalation_threshold_files": 20,
    "escalation_threshold_input_ratio": 3.0,
    "escalation_quality_reject_pct": 30,
    "harness_version": "v1",
}

_BACKEND_TO_TIER = {"free": 0, "deepseek": 1, "openai": 2, "anthropic": 3}

# Valid tier section names in cost-routing.conf, in routing order (lowest = cheapest).
TIER_ORDER = (0, 1, 2, 3)


def load_conf() -> configparser.ConfigParser:
    """Parse cost-routing.conf. Returns empty config if file is missing."""
    parser = configparser.ConfigParser()
    if CONF_PATH.is_file():
        parser.read(CONF_PATH, encoding="utf-8")
    return parser


def get_default(conf: configparser.ConfigParser, key: str) -> Any:
    raw = conf.get("defaults", key, fallback=None) if conf.has_section("defaults") else None
    if raw is None:
        return _BUILTIN_DEFAULTS.get(key)
    builtin = _BUILTIN_DEFAULTS.get(key)
    if isinstance(builtin, bool):
        return raw.strip().lower() in ("1", "true", "yes", "on")
    if isinstance(builtin, int):
        try:
            return int(raw)
        except ValueError:
            return builtin
    if isinstance(builtin, float):
        try:
            return float(raw)
        except ValueError:
            return builtin
    return raw


def get_tier_config(conf: configparser.ConfigParser, tier: int) -> dict[str, Any]:
    """Return the [tier_N] section as a dict, with numeric coercion.

    Accepts numeric tiers 0-3. Tier 00 (subscription) is informational only —
    use `get_tier_config_raw(conf, 'tier_00')` if you need it.
    """
    section = f"tier_{tier}"
    return _coerce_section(conf, section)


def _coerce_section(conf: configparser.ConfigParser, section: str) -> dict[str, Any]:
    if not conf.has_section(section):
        raise ValueError(f"Section [{section}] not configured in {CONF_PATH}")
    out: dict[str, Any] = {}
    for key, value in conf.items(section):
        if key in ("context_tokens", "batch_window_hours", "trivial_max_input_chars", "trivial_max_expected_output_tokens"):
            try:
                out[key] = int(value)
                continue
            except ValueError:
                pass
        if key.startswith("price_"):
            try:
                out[key] = float(value)
                continue
            except ValueError:
                pass
        out[key] = value
    return out


def get_subscription_info(conf: configparser.ConfigParser | None = None) -> dict[str, Any]:
    if conf is None:
        conf = load_conf()
    try:
        return _coerce_section(conf, "tier_00")
    except ValueError:
        return {}


def resolve_tier(
    cli_tier: int | None = None,
    cli_backend: str | None = None,
    conf: configparser.ConfigParser | None = None,
) -> int:
    """Resolve which tier to use.

    Precedence: CLI flag > ENV var > config default > builtin.
    """
    if cli_tier is not None:
        return cli_tier
    if cli_backend is not None:
        if cli_backend not in _BACKEND_TO_TIER:
            raise ValueError(f"Unknown backend: {cli_backend!r}")
        return _BACKEND_TO_TIER[cli_backend]

    env_tier = os.environ.get("A_WIKI_ROUTE_TIER")
    if env_tier:
        try:
            return int(env_tier)
        except ValueError:
            pass

    env_backend = os.environ.get("A_WIKI_BACKEND")
    if env_backend and env_backend in _BACKEND_TO_TIER:
        return _BACKEND_TO_TIER[env_backend]

    if conf is None:
        conf = load_conf()
    return int(get_default(conf, "ingest_tier"))


def get_enforcement(conf: configparser.ConfigParser | None = None) -> dict[str, Any]:
    if conf is None:
        conf = load_conf()
    if not conf.has_section("enforcement"):
        return {"require_routed_via_frontmatter": True, "hook_block_on_bypass": True}
    return {
        "require_routed_via_frontmatter": conf.getboolean(
            "enforcement", "require_routed_via_frontmatter", fallback=True
        ),
        "hook_block_on_bypass": conf.getboolean(
            "enforcement", "hook_block_on_bypass", fallback=True
        ),
    }


def get_harness_version(conf: configparser.ConfigParser | None = None) -> str:
    if conf is None:
        conf = load_conf()
    return str(get_default(conf, "harness_version") or "v1")


if __name__ == "__main__":
    import json

    conf = load_conf()
    summary = {
        "config_path": str(CONF_PATH),
        "config_exists": CONF_PATH.is_file(),
        "default_tier": resolve_tier(conf=conf),
        "harness_version": get_harness_version(conf),
        "enforcement": get_enforcement(conf),
        "subscription": get_subscription_info(conf),
        "tiers": {
            tier: get_tier_config(conf, tier)
            for tier in TIER_ORDER
            if conf.has_section(f"tier_{tier}")
        },
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))
