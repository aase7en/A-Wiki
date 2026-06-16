#!/usr/bin/env python3
"""
add-provider.py — Guided, public-safe way to add an LLM provider + API key.

What it does (idempotent):
  1. Registers the provider in wiki/context/providers.json — metadata ONLY
     (env var NAME, endpoint, api_style). Never the key value.
  2. Writes the KEY VALUE into drive/.secrets (cloud-synced, gitignored) — the
     ONLY place secrets live (Iron Law #6 + secrets policy). Never the repo.
  3. Optionally refreshes the scout catalog so the new models show up.

Usage:
  add-provider.py --provider zai --env-name ZAI_API_KEY --key <value> --enable
  add-provider.py --provider mistral --env-name MISTRAL_API_KEY \
                  --endpoint https://api.mistral.ai/v1/chat/completions \
                  --api-style openai --key-stdin
  add-provider.py --provider zai --env-name ZAI_API_KEY --dry-run    # preview

Test hooks: --registry <path> and --secrets-file <path> override defaults.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = REPO_ROOT / "wiki" / "context" / "providers.json"
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))


def _default_secrets_path() -> Path | None:
    try:
        from drive_secrets import find_secrets_file  # type: ignore

        found = find_secrets_file()
        if found:
            return found
    except Exception:
        pass
    direct = REPO_ROOT / "drive" / ".secrets"
    return direct if direct.parent.exists() else None


def upsert_provider(registry: dict, name: str, fields: dict) -> dict:
    providers = registry.setdefault("providers", {})
    entry = providers.get(name, {})
    for k, v in fields.items():
        if v is not None:
            entry[k] = v
    entry.setdefault("api_style", "openai")
    entry.setdefault("enabled", False)
    providers[name] = entry
    registry.setdefault("version", 1)
    return registry


def upsert_secret_text(text: str, name: str, value: str) -> str:
    """Replace `NAME=...` in a .secrets file or append it. Returns new text."""
    lines = text.splitlines()
    done = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        body = stripped[len("export "):] if stripped.startswith("export ") else stripped
        if body.startswith(f"{name}="):
            prefix = "export " if stripped.startswith("export ") else ""
            lines[i] = f"{prefix}{name}={value}"
            done = True
            break
    if not done:
        lines.append(f"{name}={value}")
    return "\n".join(lines) + "\n"


def _read_key(args) -> str | None:
    if args.key is not None:
        return args.key
    if args.key_stdin:
        return sys.stdin.read().strip()
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Add an LLM provider + API key (public-safe)")
    parser.add_argument("--provider", required=True, help="provider id, e.g. zai")
    parser.add_argument("--env-name", required=True, help="env var NAME for the key, e.g. ZAI_API_KEY")
    parser.add_argument("--endpoint", help="chat completions endpoint URL")
    parser.add_argument("--models-url", help="models list URL (for scout)")
    parser.add_argument("--api-style", choices=("openai", "gemini", "anthropic"), help="request shape")
    parser.add_argument("--via", help="route through another provider until direct key is set")
    parser.add_argument("--default-model", help="default model id")
    parser.add_argument("--label", help="human label")
    parser.add_argument("--enable", action="store_true", help="mark provider enabled")
    parser.add_argument("--key", help="API key value (prefer --key-stdin)")
    parser.add_argument("--key-stdin", action="store_true", help="read key value from stdin")
    parser.add_argument("--dry-run", action="store_true", help="preview; write nothing")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    parser.add_argument("--secrets-file", default=None)
    args = parser.parse_args(argv)

    # Windows consoles may default to a non-UTF-8 codepage (e.g. cp874); make
    # output encoding-safe so summary glyphs never crash the run.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except Exception:
            pass

    registry_path = Path(args.registry)
    registry = json.loads(registry_path.read_text(encoding="utf-8")) if registry_path.exists() \
        else {"version": 1, "providers": {}}

    fields = {
        "label": args.label or args.provider,
        "api_style": args.api_style,
        "endpoint": args.endpoint,
        "models_url": args.models_url,
        "auth_env": args.env_name,
        "auth_scheme": "bearer",
        "via": args.via,
        "default_model": args.default_model,
    }
    if args.enable:
        fields["enabled"] = True
    upsert_provider(registry, args.provider, fields)

    key_value = _read_key(args)
    secrets_path = Path(args.secrets_file) if args.secrets_file else _default_secrets_path()
    wrote_secret = False
    secret_target = str(secrets_path) if secrets_path else "(no .secrets found)"

    if not args.dry_run:
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if key_value:
            if not secrets_path:
                sys.stderr.write(
                    "⚠️  No drive/.secrets found — link your cloud drive first "
                    "(bash scripts/setup-cloud-link.sh). Provider registered; key NOT stored.\n"
                )
            else:
                existing = secrets_path.read_text(encoding="utf-8") if secrets_path.exists() else ""
                secrets_path.parent.mkdir(parents=True, exist_ok=True)
                secrets_path.write_text(upsert_secret_text(existing, args.env_name, key_value), encoding="utf-8")
                wrote_secret = True

    summary = {
        "provider": args.provider,
        "env_name": args.env_name,
        "registry": str(registry_path),
        "enabled": bool(args.enable),
        "secret_written": wrote_secret,
        "secret_target": secret_target if key_value else None,
        "dry_run": args.dry_run,
    }
    if args.json:
        print(json.dumps(summary, ensure_ascii=False))
    else:
        verb = "would register" if args.dry_run else "registered"
        print(f"{verb} provider '{args.provider}' (auth_env={args.env_name}) in {registry_path}")
        if key_value:
            if args.dry_run:
                print(f"  would store key in {secret_target} (value hidden)")
            elif wrote_secret:
                print(f"  key stored in {secret_target} (value hidden, gitignored)")
        if not args.dry_run:
            print("  next: python3 scripts/model-scout-current.py --catalog  -> refresh catalog")
    return 0


if __name__ == "__main__":
    sys.exit(main())
