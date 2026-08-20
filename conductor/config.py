"""Layered configuration (Serena-inspired): defaults < project < env.

Layers merge shallowly per top-level key; later layers win. Validation is
fail-closed: unknown schema or incompatible mode combinations abort with
ConfigError — the conductor must never start on a config it half-undersstands.
"""
from __future__ import annotations

import os
from pathlib import Path

import yaml

SCHEMA = "awiki-conductor/v1"
PROJECT_FILE = ".awiki-conductor.yaml"

INCOMPATIBLE_MODES = [
    {"interactive", "one-shot"},
    {"no-memories", "onboarding"},
]

DEFAULTS: dict = {
    "schema": SCHEMA,
    "modes": {"base": ["safety"], "default": [], "added": []},
    "limits": {"max_parallel_agents": 3, "verify_gates": True},
}


class ConfigError(RuntimeError):
    """Invalid layered config — loading must fail closed."""


def _deep_merge(base: dict, overlay: dict) -> dict:
    out = dict(base)
    for k, v in overlay.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def _load_yaml_layer(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        raise ConfigError(f"malformed {path.name}: {e}") from e
    if not isinstance(data, dict):
        raise ConfigError(f"{path.name} must be a mapping")
    if data.get("schema", SCHEMA) != SCHEMA:
        raise ConfigError(f"unknown schema {data.get('schema')!r} (expected {SCHEMA})")
    return data


def _env_layer() -> dict:
    modes_added = os.environ.get("AWIKI_CONDUCTOR_MODE_ADDED")
    if not modes_added:
        return {}
    return {"modes": {"added": [m.strip() for m in modes_added.split(",") if m.strip()]}}


def _validate(cfg: dict) -> None:
    modes = cfg.get("modes") or {}
    for group in ("base", "default", "added"):
        v = modes.get(group)
        if v is None:
            continue
        if not isinstance(v, list) or any(not isinstance(m, str) for m in v):
            raise ConfigError(f"modes.{group} must be a list of strings")
    for pair in INCOMPATIBLE_MODES:
        active = set(modes.get("default", [])) | set(modes.get("added", []))
        if pair <= active:
            raise ConfigError(f"incompatible modes together: {sorted(pair)}")


def load_config(repo_root: Path | None = None) -> dict:
    root = Path(repo_root) if repo_root else Path.cwd()
    cfg = _deep_merge(DEFAULTS, _load_yaml_layer(root / PROJECT_FILE))
    cfg = _deep_merge(cfg, _env_layer())
    _validate(cfg)
    return cfg
