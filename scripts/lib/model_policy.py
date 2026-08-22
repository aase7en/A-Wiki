"""model_policy.py — brain-side model POLICY authority (Phase 7).

Loads config/models/policy.yaml fail-closed and resolves the optional
machine-local runtime bindings (gitignored). The A-Conductor control
plane reads this via the conductor bridge; it OWNS dispatch, never policy.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POLICY = REPO_ROOT / "config" / "models" / "policy.yaml"
DEFAULT_RUNTIME = REPO_ROOT / "config" / "models" / "runtime.local.yaml"
SCHEMA = "awiki-model-policy/v1"
TIER_ORDER = ("free", "cheap", "capable", "primary")


class PolicyError(RuntimeError):
    """Invalid/unreadable policy — callers must fail closed."""


def _load_yaml(path: Path) -> dict:
    # PyYAML is declared in requirements.txt but a fresh machine may not
    # have installed it yet — surface that as PolicyError (clean, catchable
    # by the conductor CLI) instead of crashing the import itself.
    try:
        import yaml
    except ModuleNotFoundError as e:
        raise PolicyError(
            "PyYAML not installed — run: pip install -r requirements.txt") from e
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (yaml.YAMLError, OSError, UnicodeDecodeError) as e:
        raise PolicyError(f"cannot read {path.name}: {e}") from e
    if not isinstance(data, dict):
        raise PolicyError(f"{path.name} must be a mapping")
    return data


def load_policy(path: Path | None = None) -> dict:
    p = Path(path) if path else DEFAULT_POLICY
    if not p.is_file():
        raise PolicyError(f"policy file missing: {p}")
    data = _load_yaml(p)
    if data.get("schema") != SCHEMA:
        raise PolicyError(f"unknown schema {data.get('schema')!r} (expected {SCHEMA})")
    tiers = data.get("tiers") or {}
    for name in TIER_ORDER:
        if name not in tiers:
            raise PolicyError(f"missing required tier: {name}")
    budgets = data.get("budgets") or {}
    if "default" not in budgets:
        raise PolicyError("budgets must define 'default'")
    for task, rule in budgets.items():
        if rule.get("max_tier") not in tiers:
            raise PolicyError(
                f"budget '{task}' references unknown tier {rule.get('max_tier')!r}")
    return data


def tier_order(policy: dict) -> list[str]:
    order = list(TIER_ORDER)
    extra = [t for t in policy.get("tiers", {}) if t not in order]
    return order + extra


def tier_allowed(policy: dict, tier: str, task: str = "default") -> bool:
    max_tier = (policy.get("budgets", {}).get(task)
                or policy.get("budgets", {}).get("default", {})).get("max_tier")
    if max_tier is None:
        return False
    order = tier_order(policy)
    return order.index(tier) <= order.index(max_tier)


def resolve_runtime() -> dict:
    """Resolve machine-local slot bindings (optional, gitignored).

    Never raises; returns {'resolved': False, 'reason': ...} when absent —
    the conductor decides how to proceed (policy without runtime is valid:
    a fresh machine simply has no bindings yet)."""
    path = Path(os.environ.get("AWIKI_MODELS_RUNTIME", str(DEFAULT_RUNTIME)))
    if not path.is_file():
        return {"resolved": False,
                "reason": f"no runtime bindings at {path.name} (machine-local, optional)"}
    try:
        data = _load_yaml(path)
    except PolicyError as e:
        return {"resolved": False, "reason": str(e)}
    if data.get("schema") != "awiki-model-runtime/v1":
        return {"resolved": False, "reason": "runtime schema mismatch"}
    return {"resolved": True, "slots": data.get("slots", {})}


def policy_summary() -> dict:
    """Read-only bridge payload: policy WITHOUT any local model names."""
    pol = load_policy()
    runtime = resolve_runtime()
    safe_runtime = {
        "resolved": runtime.get("resolved", False),
        "reason": runtime.get("reason", ""),
        "slots_bound": sorted((runtime.get("slots") or {}).keys()),
    }
    return {"schema": pol["schema"], "tiers": pol["tiers"],
            "budgets": pol["budgets"], "rules": pol.get("rules", []),
            "runtime": safe_runtime}
