#!/usr/bin/env python3
"""
provider_registry.py — Central provider/model registry + generic adapter.

Single source of truth for LLM providers. Adding a provider = one entry in
wiki/context/providers.json (public-safe: env var NAME only, never the key).
This replaces the per-provider `try_<name>_direct()` duplication in delegate.sh
with one request builder per api_style (openai | gemini | anthropic).

Library
  load_registry(path=None) -> dict
  resolve_transport(name, registry=None, env=None) -> (transport_name, conf)
  build_request(provider, model, prompt, registry=None, env=None) -> spec dict
  list_providers(registry=None, enabled_only=False) -> list[dict]

CLI
  provider_registry.py list [--enabled] [--json]
  provider_registry.py resolve <provider> [--json]
  provider_registry.py build <provider> <model>   # prompt on stdin; key REDACTED
  provider_registry.py call  <provider> <model>   # prompt on stdin; does HTTP, prints text

`call` reuses scripts/_extract_response.py to parse responses + classify errors,
so the bash router only handles orchestration (event logging, timing, self-heal).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY = REPO_ROOT / "wiki" / "context" / "providers.json"
EXTRACT_PY = REPO_ROOT / "scripts" / "_extract_response.py"


# ── registry loading ───────────────────────────────────────────────────────

def load_registry(path: str | Path | None = None) -> dict[str, Any]:
    p = Path(path) if path else DEFAULT_REGISTRY
    data = json.loads(p.read_text(encoding="utf-8"))
    if "providers" not in data:
        raise ValueError(f"registry {p} missing 'providers'")
    return data


def _providers(registry: dict[str, Any] | None) -> dict[str, Any]:
    registry = registry or load_registry()
    return registry["providers"]


def resolve_transport(
    name: str,
    registry: dict[str, Any] | None = None,
    env: dict[str, str] | None = None,
) -> tuple[str, dict[str, Any]]:
    """Return the (provider_name, conf) that actually carries the request.

    A provider with `via` falls back to that transport until its own
    `auth_env` key is present in env (then it goes direct).
    """
    env = os.environ if env is None else env
    provs = _providers(registry)
    if name not in provs:
        raise KeyError(f"unknown provider '{name}'")
    conf = provs[name]
    via = conf.get("via")
    if via and not env.get(conf.get("auth_env", "")):
        if via not in provs:
            raise KeyError(f"provider '{name}' via unknown '{via}'")
        return via, provs[via]
    return name, conf


def _redact(headers: dict[str, str]) -> dict[str, str]:
    out = {}
    for k, v in headers.items():
        if k.lower() in ("authorization", "x-api-key"):
            out[k] = "Bearer ***" if k.lower() == "authorization" else "***"
        else:
            out[k] = v
    return out


def build_request(
    provider: str,
    model: str,
    prompt: str,
    registry: dict[str, Any] | None = None,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Build a provider-agnostic request spec for `model` with `prompt`.

    Returns: {url, method, headers, body, extractor, model, provider,
              transport_provider, has_key, auth_env}
    The real key is embedded in headers; use _redact() before printing.
    """
    env = os.environ if env is None else env
    registry = registry or load_registry()
    transport_name, conf = resolve_transport(provider, registry, env)
    api_style = conf["api_style"]
    auth_env = conf.get("auth_env", "")
    key = env.get(auth_env, "") or ""
    endpoint = conf["endpoint"]

    if api_style == "openai":
        url = endpoint
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        body = {"model": model, "messages": [{"role": "user", "content": prompt}]}
        extractor = "openai"
    elif api_style == "gemini":
        url = f"{endpoint}/models/{model}:generateContent?key={key}"
        headers = {"Content-Type": "application/json"}
        body = {"contents": [{"parts": [{"text": prompt}]}]}
        extractor = "gemini"
    elif api_style == "anthropic":
        url = endpoint
        headers = {
            "x-api-key": key,
            "anthropic-version": conf.get("anthropic_version", "2023-06-01"),
            "Content-Type": "application/json",
        }
        body = {
            "model": model,
            "max_tokens": int(conf.get("max_tokens", 2048)),
            "messages": [{"role": "user", "content": prompt}],
        }
        extractor = "anthropic"
    else:
        raise ValueError(f"unsupported api_style '{api_style}' for {transport_name}")

    return {
        "url": url,
        "method": "POST",
        "headers": headers,
        "body": body,
        "extractor": extractor,
        "model": model,
        "provider": provider,
        "transport_provider": transport_name,
        "auth_env": auth_env,
        "has_key": bool(key),
    }


def list_providers(
    registry: dict[str, Any] | None = None, enabled_only: bool = False
) -> list[dict[str, Any]]:
    rows = []
    for name, conf in _providers(registry).items():
        if enabled_only and not conf.get("enabled", False):
            continue
        rows.append(
            {
                "name": name,
                "label": conf.get("label", name),
                "api_style": conf.get("api_style"),
                "enabled": conf.get("enabled", False),
                "via": conf.get("via"),
                "auth_env": conf.get("auth_env"),
                "default_model": conf.get("default_model"),
            }
        )
    return rows


# ── HTTP call (reuses _extract_response.py extractors) ─────────────────────

def _extractors():
    import importlib.util

    spec = importlib.util.spec_from_file_location("_extract_response", EXTRACT_PY)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def call(
    provider: str,
    model: str,
    prompt: str,
    timeout: int = 60,
    registry: dict[str, Any] | None = None,
    env: dict[str, str] | None = None,
) -> tuple[int, str, str]:
    """Perform the request. Returns (exit_code, stdout_text, stderr_msg).

    exit 0 + text on success; exit 1 + classified error (RATE_LIMIT / AUTH_ERROR
    / MODEL_NOT_FOUND / network-timeout / ...) on failure.
    """
    spec = build_request(provider, model, prompt, registry=registry, env=env)
    if not spec["has_key"]:
        return 1, "", f"AUTH_ERROR: no key for {spec['auth_env']}"

    ex = _extractors()
    data_bytes = json.dumps(spec["body"]).encode("utf-8")
    req = urllib.request.Request(
        spec["url"], data=data_bytes, headers=spec["headers"], method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace") if hasattr(e, "read") else ""
        cls = ex.classify_api_error(e.code, body) or f"HTTP_{e.code}"
        return 1, "", f"{cls}: {body[:200]}"
    except (urllib.error.URLError, OSError) as e:
        return 1, "", f"network-timeout: {e}"

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        return 1, "", f"JSON_PARSE_ERROR: {e}"

    try:
        fn = {
            "openai": ex.extract_openai,
            "gemini": ex.extract_gemini,
            "anthropic": ex.extract_anthropic,
        }[spec["extractor"]]
        return 0, fn(parsed), ""
    except ex.ExtractionError as e:
        return 1, "", str(e)


# ── CLI ─────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="A-Wiki provider registry")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="list providers")
    p_list.add_argument("--enabled", action="store_true")
    p_list.add_argument("--json", action="store_true")

    p_res = sub.add_parser("resolve", help="show effective transport provider")
    p_res.add_argument("provider")
    p_res.add_argument("--json", action="store_true")

    p_build = sub.add_parser("build", help="print request spec (key redacted)")
    p_build.add_argument("provider")
    p_build.add_argument("model")

    p_call = sub.add_parser("call", help="do HTTP call; prompt on stdin")
    p_call.add_argument("provider")
    p_call.add_argument("model")
    p_call.add_argument("--timeout", type=int, default=60)

    args = parser.parse_args(argv)

    if args.cmd == "list":
        rows = list_providers(enabled_only=args.enabled)
        if args.json:
            print(json.dumps(rows, ensure_ascii=False))
        else:
            for r in rows:
                flag = "on " if r["enabled"] else "off"
                via = f" via={r['via']}" if r["via"] else ""
                print(f"[{flag}] {r['name']:<11} {r['api_style']:<10}{via}")
        return 0

    if args.cmd == "resolve":
        name, conf = resolve_transport(args.provider)
        if args.json:
            print(json.dumps({"transport_provider": name, "api_style": conf["api_style"]}))
        else:
            print(name)
        return 0

    if args.cmd == "build":
        prompt = sys.stdin.read()
        spec = build_request(args.provider, args.model, prompt)
        spec["headers"] = _redact(spec["headers"])
        if "key=" in spec["url"]:
            import re

            spec["url"] = re.sub(r"key=[^&]+", "key=***", spec["url"])
        print(json.dumps(spec, ensure_ascii=False))
        return 0

    if args.cmd == "call":
        prompt = sys.stdin.read()
        code, out, err = call(args.provider, args.model, prompt, timeout=args.timeout)
        if code == 0:
            print(out)
        else:
            print(err, file=sys.stderr)
        return code

    return 1


if __name__ == "__main__":
    sys.exit(main())
