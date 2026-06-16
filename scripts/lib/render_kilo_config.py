#!/usr/bin/env python3
"""
render_kilo_config.py — Render a machine-specific global Kilo config from a
portable, Drive-synced template.

Why a renderer (not a static file or env vars):
  Kilo's global config (~/.config/kilo/kilo.jsonc) is static JSONC with no
  ${VAR} interpolation. The only robust, cross-OS way to keep one config
  consistent across machines with different Google Drive mount paths is to
  keep a secret-free, path-free TEMPLATE in Google Drive and render the
  machine-specific file here, substituting the detected Drive path, repo
  path, and provider keys from Drive .secrets.

Three locations:
  - TEMPLATE source-of-truth : <Drive>/A-Wiki-Data/.config/kilo/kilo.jsonc.template
  - repo fallback template   : scripts/lib/kilo.jsonc.template  (bundled, git-synced)
  - rendered output          : ~/.config/kilo/kilo.jsonc        (local, per-machine)

Placeholders resolved at render time:
  __DRIVE_DATA__      → A-Wiki-Data dir on THIS machine
  __DRIVE_PERSONAL__  → <data>/personal          (MCP filesystem target; never .secrets)
  __DRIVE_SKILLS__    → <data>/.config/kilo/skills
  __REPO_ROOT__       → this repository root
  __SECRET_<ENV>__    → provider apiKey from Drive .secrets (entry dropped if missing)

CLI:
  python3 scripts/lib/render_kilo_config.py             # render (idempotent)
  python3 scripts/lib/render_kilo_config.py --check     # report only, no write
  python3 scripts/lib/render_kilo_config.py --force     # overwrite even if unchanged
"""
from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BUNDLED_TEMPLATE = REPO_ROOT / "scripts" / "lib" / "kilo.jsonc.template"
Kilo_GLOBAL_DIR = Path.home() / ".config" / "kilo"
Kilo_CONFIG = Kilo_GLOBAL_DIR / "kilo.jsonc"
Kilo_COMMAND_DIR = Kilo_GLOBAL_DIR / "command"
DRIVE_CONFIG_SUBDIR = Path(".config") / "kilo"

# provider id → .secrets env var name. Additive only; default model/agents untouched.
PROVIDER_SECRET_MAP: dict[str, str] = {
    "google": "GEMINI_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "groq": "GROQ_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
}
# High-sensitivity secrets never injected into any config file (mirror import-keys.py).
NEVER_INJECT = {"WIKI_UNLOCK"}

PATH_TOKENS = ("__DRIVE_DATA__", "__DRIVE_PERSONAL__", "__DRIVE_SKILLS__", "__REPO_ROOT__")


# ── Drive + secrets detection (reuses A-Wiki's cross-OS resolvers) ─────────

def detect_drive_data_root() -> Path | None:
    """Find the A-Wiki-Data dir on THIS machine. Resolution order:
    1. A_WIKI_DRIVE_PATH env override
    2. drive_secrets._glob_cloudstorage_drive() (standalone cloud auto-detect)
    3. drive_path.get_drive_root() (drive/ symlink)
    Returns None if nothing is found.
    """
    env = os.environ.get("A_WIKI_DRIVE_PATH")
    if env and Path(env).is_dir():
        return Path(env)

    lib = REPO_ROOT / "scripts" / "lib"
    if str(lib) not in sys.path:
        sys.path.insert(0, str(lib))

    # 2. Standalone glob — does NOT require the drive/ symlink to exist.
    try:
        from drive_secrets import _glob_cloudstorage_drive  # type: ignore
        for secrets_file in _glob_cloudstorage_drive():
            data = secrets_file.parent  # <data>/.secrets → <data>
            if data.is_dir():
                return data
    except Exception:
        pass

    # 3. drive/ symlink / .drive-path fallback.
    try:
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        from drive_path import get_drive_root  # type: ignore
        root = get_drive_root()
        if root.is_dir():
            return root
    except Exception:
        pass

    return None


def load_secrets(data_root: Path) -> dict[str, str]:
    """Parse <data_root>/.secrets KEY=VALUE (empty if missing/unreadable)."""
    lib = REPO_ROOT / "scripts" / "lib"
    if str(lib) not in sys.path:
        sys.path.insert(0, str(lib))
    secrets_file = data_root / ".secrets"
    try:
        from drive_secrets import parse_secrets_file  # type: ignore
        return parse_secrets_file(secrets_file)
    except Exception:
        pass
    # Fallback inline parser
    values: dict[str, str] = {}
    try:
        for raw in secrets_file.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            if line.startswith("export "):
                line = line[7:].strip()
            k, _, v = line.partition("=")
            k, v = k.strip(), v.strip().strip('"').strip("'")
            if k and k not in NEVER_INJECT:
                values[k] = v
    except OSError:
        pass
    return values


# ── Rendering (pure, unit-tested) ──────────────────────────────────────────

def build_path_map(drive_data: Path, repo_root: Path) -> dict[str, str]:
    return {
        "__DRIVE_DATA__": str(drive_data),
        "__DRIVE_PERSONAL__": str(drive_data / "personal"),
        "__DRIVE_SKILLS__": str(drive_data / DRIVE_CONFIG_SUBDIR / "skills"),
        "__REPO_ROOT__": str(repo_root),
    }


def resolve_provider_secrets(config: dict, secrets: dict[str, str]) -> None:
    """In-place: resolve each provider's __SECRET_X__ apiKey.
    Drop the provider entirely if its secret is missing, empty, or never-inject."""
    providers = config.get("provider")
    if not isinstance(providers, dict):
        return
    for pname in list(providers.keys()):
        prov = providers.get(pname)
        if not isinstance(prov, dict):
            continue
        opts = prov.get("options")
        if not isinstance(opts, dict):
            continue  # provider without an apiKey placeholder — leave untouched
        ak = opts.get("apiKey", "")
        if isinstance(ak, str) and ak.startswith("__SECRET_") and ak.endswith("__"):
            env_name = ak[len("__SECRET_"):-len("__")]
            val = secrets.get(env_name, "")
            if env_name in NEVER_INJECT or not val:
                del providers[pname]  # no usable key → don't advertise the provider
            else:
                opts["apiKey"] = val


def resolve_path_tokens(obj, path_map: dict[str, str]):
    """Recursively replace __TOKEN__ substrings in every string value."""
    if isinstance(obj, str):
        for tok, val in path_map.items():
            if tok in obj:
                obj = obj.replace(tok, val)
        return obj
    if isinstance(obj, list):
        return [resolve_path_tokens(x, path_map) for x in obj]
    if isinstance(obj, dict):
        return {k: resolve_path_tokens(v, path_map) for k, v in obj.items()}
    return obj


def _assert_no_placeholders(rendered: str, path_map: dict[str, str]) -> None:
    for tok in path_map:
        if tok in rendered:
            raise ValueError(f"Unresolved path placeholder {tok} in rendered config")
    if "__SECRET_" in rendered:
        raise ValueError("Unresolved __SECRET_*__ placeholder in rendered config")


def render_config(template_text: str, drive_data: Path, repo_root: Path,
                  secrets: dict[str, str]) -> str:
    """Render template text → machine-specific JSONC string."""
    config = json.loads(template_text)  # template is strict JSON (no // comments)
    resolve_provider_secrets(config, secrets)
    path_map = build_path_map(drive_data, repo_root)
    config = resolve_path_tokens(config, path_map)
    rendered = json.dumps(config, indent=2, ensure_ascii=False) + "\n"
    _assert_no_placeholders(rendered, path_map)
    return rendered


# ── Command copying ────────────────────────────────────────────────────────

def copy_commands(src_dir: Path, dest_dir: Path) -> list[Path]:
    """Copy *.md slash-command files src→dest (overwrite). Returns copied paths.
    Creates dest_dir. Ignores non-.md files."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    copied: list[Path] = []
    if not src_dir.is_dir():
        return copied
    for f in sorted(src_dir.glob("*.md")):
        target = dest_dir / f.name
        target.write_bytes(f.read_bytes())
        copied.append(target)
    return copied


# ── Template discovery + atomic write ──────────────────────────────────────

def find_template(drive_data: Path | None) -> Path:
    """Prefer the Drive-synced template; fall back to the repo-bundled one."""
    if drive_data is not None:
        drive_tpl = drive_data / DRIVE_CONFIG_SUBDIR / "kilo.jsonc.template"
        if drive_tpl.is_file():
            return drive_tpl
    if BUNDLED_TEMPLATE.is_file():
        return BUNDLED_TEMPLATE
    raise FileNotFoundError(
        "No kilo.jsonc.template found — neither in Drive (.config/kilo/) nor "
        "bundled at scripts/lib/kilo.jsonc.template"
    )


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".kilo-render-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


# ── CLI ────────────────────────────────────────────────────────────────────

def _report(drive_data: Path, template_path: Path, secrets: dict[str, str]) -> str:
    lines = [
        f"Drive data root : {drive_data}",
        f"Template        : {template_path}",
        f"Output target   : {Kilo_CONFIG}",
    ]
    avail = {p: e for p, e in PROVIDER_SECRET_MAP.items() if secrets.get(e)}
    missing = {p: e for p, e in PROVIDER_SECRET_MAP.items() if not secrets.get(e)}
    lines.append(f"Providers wired : {', '.join(avail) or '(none)'}")
    if missing:
        lines.append(f"Providers drop  : {', '.join(f'{p}({e})' for p,e in missing.items())}")
    drive_cmds = drive_data / DRIVE_CONFIG_SUBDIR / "command"
    cmds = sorted(p.name for p in drive_cmds.glob("*.md")) if drive_cmds.is_dir() else []
    lines.append(f"Drive /commands : {', '.join(cmds) if cmds else '(none in Drive)'}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(description="Render portable global Kilo config")
    ap.add_argument("--check", action="store_true", help="report only; do not write")
    ap.add_argument("--force", action="store_true", help="overwrite even if unchanged")
    ap.add_argument("--out", default=str(Kilo_CONFIG), help="output path")
    args = ap.parse_args(argv)

    drive_data = detect_drive_data_root()
    if drive_data is None:
        print("ERROR: could not detect A-Wiki-Data on this machine.", file=sys.stderr)
        print("Set A_WIKI_DRIVE_PATH=/path/to/A-Wiki-Data or run "
              "bash scripts/setup-cloud-link.sh --auto first.", file=sys.stderr)
        return 2

    template_path = find_template(drive_data)
    secrets = load_secrets(drive_data)
    template_text = template_path.read_text(encoding="utf-8")

    if args.check:
        print(_report(drive_data, template_path, secrets))
        return 0

    rendered = render_config(template_text, drive_data, REPO_ROOT, secrets)
    out_path = Path(args.out)

    if not args.force and out_path.is_file() and out_path.read_text(encoding="utf-8") == rendered:
        print(f"OK — {out_path} already up to date")
    else:
        _atomic_write(out_path, rendered)
        print(f"OK — wrote {out_path}")

    # Copy Drive slash-commands → local command dir
    drive_cmds = drive_data / DRIVE_CONFIG_SUBDIR / "command"
    copied = copy_commands(drive_cmds, Kilo_COMMAND_DIR)
    if copied:
        print(f"OK — copied {len(copied)} command(s) → {Kilo_COMMAND_DIR}")
    print(_report(drive_data, template_path, secrets))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
