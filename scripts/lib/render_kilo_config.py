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

Agent prompts (p1):
  Prompts are now read from .kilo/agents/*.md — the template specifies only
  model + variant per agent. Editing a prompt in .kilo/agents/ automatically
  propagates on the next render.

Command sync (p2):
  Repo commands (.kilo/command/) are synced first, then Drive commands
  (.config/kilo/command/) overwrite any duplicates. Drive = user-local overrides.

Placeholders resolved at render time:
  __DRIVE_DATA__      -> A-Wiki-Data dir on THIS machine
  __DRIVE_PERSONAL__  -> <data>/personal          (MCP filesystem target; never .secrets)
  __DRIVE_SKILLS__    -> <data>/.config/kilo/skills
  __REPO_ROOT__       -> this repository root
  __SECRET_<ENV>__    -> provider apiKey from Drive .secrets (entry dropped if missing)

CLI:
  python3 scripts/lib/render_kilo_config.py             # render (idempotent)
  python3 scripts/lib/render_kilo_config.py --check     # report only, no write
  python3 scripts/lib/render_kilo_config.py --force     # overwrite even if unchanged
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BUNDLED_TEMPLATE = REPO_ROOT / "scripts" / "lib" / "kilo.jsonc.template"
Kilo_GLOBAL_DIR = Path.home() / ".config" / "kilo"
Kilo_CONFIG = Kilo_GLOBAL_DIR / "kilo.jsonc"
Kilo_COMMAND_DIR = Kilo_GLOBAL_DIR / "command"
DRIVE_CONFIG_SUBDIR = Path(".config") / "kilo"
AGENTS_DIR = REPO_ROOT / ".kilo" / "agents"
REPO_COMMAND_DIR = REPO_ROOT / ".kilo" / "command"

# provider id -> .secrets env var name. Additive only; default model/agents untouched.
PROVIDER_SECRET_MAP: dict[str, str] = {
    "google": "GEMINI_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "groq": "GROQ_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "fireworks-ai": "FIREWORKS_API_KEY",
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

    # 2. Standalone glob -- does NOT require the drive/ symlink to exist.
    try:
        from drive_secrets import _glob_cloudstorage_drive  # type: ignore
        for secrets_file in _glob_cloudstorage_drive():
            data = secrets_file.parent  # <data>/.secrets -> <data>
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


# ── Agent merging (p1) ─────────────────────────────────────────────────────

def merge_agents(template_agents: dict, agents_from_md: dict) -> dict:
    """Merge .md agent definitions with template overrides.

    The template (after p1) provides only model/variant/disable per agent.
    Everything else (prompt, description, mode, options, permission) comes
    from .kilo/agents/*.md.

    Template-only agents (no .md file, e.g. plan, code, ask) are preserved.
    .md-only agents (no template entry) are added.
    """
    result = {}

    for agent_id, tpl_entry in template_agents.items():
        if agent_id in agents_from_md:
            merged = dict(agents_from_md[agent_id])
            for override_key in ("model", "variant", "disable"):
                if override_key in tpl_entry:
                    merged[override_key] = tpl_entry[override_key]
            result[agent_id] = merged
        else:
            result[agent_id] = dict(tpl_entry)

    for agent_id, md_entry in agents_from_md.items():
        if agent_id not in result:
            result[agent_id] = dict(md_entry)

    return result


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
            continue  # provider without an apiKey placeholder -- leave untouched
        ak = opts.get("apiKey", "")
        if isinstance(ak, str) and ak.startswith("__SECRET_") and ak.endswith("__"):
            env_name = ak[len("__SECRET_"):-len("__")]
            val = secrets.get(env_name, "")
            if env_name in NEVER_INJECT or not val:
                del providers[pname]  # no usable key -> don't advertise the provider
            else:
                opts["apiKey"] = val


def resolve_path_tokens(obj, path_map: dict[str, str], secrets: dict[str, str] | None = None):
    """Recursively replace __TOKEN__ substrings in every string value.
    Also resolves __SECRET_X__ placeholders if secrets dict provided."""
    if isinstance(obj, str):
        for tok, val in path_map.items():
            if tok in obj:
                obj = obj.replace(tok, val)
        if secrets is not None:
            for env_name, val in secrets.items():
                placeholder = f"__SECRET_{env_name}__"
                if placeholder in obj:
                    obj = obj.replace(placeholder, val)
        return obj
    if isinstance(obj, list):
        return [resolve_path_tokens(x, path_map, secrets) for x in obj]
    if isinstance(obj, dict):
        return {k: resolve_path_tokens(v, path_map, secrets) for k, v in obj.items()}
    return obj


def _write_config_cache() -> None:
    """Write a hash of template + .kilo/agents/*.md for staleness detection (p4)."""
    cache_file = REPO_ROOT / ".kilo" / ".kilo-config-cache"
    tpl = BUNDLED_TEMPLATE
    agents_dir = AGENTS_DIR
    hasher = hashlib.sha256()
    try:
        if tpl.is_file():
            hasher.update(tpl.read_bytes())
        if agents_dir.is_dir():
            for f in sorted(agents_dir.glob("*.md")):
                hasher.update(f.name.encode())
                hasher.update(f.read_bytes())
    except OSError:
        pass  # best-effort
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(hasher.hexdigest(), encoding="utf-8")


def _assert_no_placeholders(rendered: str, path_map: dict[str, str], secrets: dict[str, str] | None = None) -> None:
    for tok in path_map:
        if tok in rendered:
            raise ValueError(f"Unresolved path placeholder {tok} in rendered config")
    if secrets is not None:
        for env_name in PROVIDER_SECRET_MAP.values():
            if f"__SECRET_{env_name}__" in rendered:
                raise ValueError(f"Unresolved __SECRET_{env_name}__ placeholder in rendered config")
    elif "__SECRET_" in rendered:
        raise ValueError("Unresolved __SECRET_*__ placeholder in rendered config")


def render_config(template_text: str, drive_data: Path, repo_root: Path,
                  secrets: dict[str, str],
                  agents_from_md: dict | None = None) -> str:
    """Render template text -> machine-specific JSONC string.

    If agents_from_md is provided, it is merged into the template's agent
    definitions (p1). Otherwise template agents are used verbatim.
    """
    config = json.loads(template_text)  # template is strict JSON (no // comments)

    if agents_from_md is not None:
        template_agents = config.get("agent", {})
        config["agent"] = merge_agents(template_agents, agents_from_md)

    resolve_provider_secrets(config, secrets)
    path_map = build_path_map(drive_data, repo_root)
    config = resolve_path_tokens(config, path_map, secrets)
    rendered = json.dumps(config, indent=2, ensure_ascii=False) + "\n"
    _assert_no_placeholders(rendered, path_map, secrets)
    return rendered


# ── Command copying ────────────────────────────────────────────────────────

def copy_commands(src_dir: Path, dest_dir: Path) -> list[Path]:
    """Copy *.md slash-command files src->dest (overwrite). Returns copied paths.
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
        "No kilo.jsonc.template found -- neither in Drive (.config/kilo/) nor "
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
    # Repo commands
    if REPO_COMMAND_DIR.is_dir():
        repo_cmds = sorted(p.name for p in REPO_COMMAND_DIR.glob("*.md"))
        lines.append(f"Repo /commands  : {', '.join(repo_cmds) if repo_cmds else '(none in repo)'}")
    # Agents from .kilo/agents/
    agents_found = sorted(AGENTS_DIR.glob("*.md")) if AGENTS_DIR.is_dir() else []
    lines.append(f"Agent .md files : {len(agents_found)} found in {AGENTS_DIR}"
                 if agents_found else "Agent .md files : (none)")
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

    # Read .kilo/agents/*.md (p1)
    from parse_agent_md import read_agents_dir  # type: ignore
    agents_from_md = read_agents_dir(AGENTS_DIR)

    if args.check:
        print(_report(drive_data, template_path, secrets))
        return 0

    rendered = render_config(template_text, drive_data, REPO_ROOT, secrets,
                             agents_from_md=agents_from_md)
    out_path = Path(args.out)

    if not args.force and out_path.is_file() and out_path.read_text(encoding="utf-8") == rendered:
        print(f"OK -- {out_path} already up to date")
    else:
        _atomic_write(out_path, rendered)
        print(f"OK -- wrote {out_path}")

    # Write staleness cache (p4): hash of template + agents for SessionStart check
    _write_config_cache()

    # Sync repo commands first, then Drive overrides (p2)
    repo_copied = copy_commands(REPO_COMMAND_DIR, Kilo_COMMAND_DIR)
    if repo_copied:
        print(f"OK -- synced {len(repo_copied)} repo command(s) -> {Kilo_COMMAND_DIR}")

    drive_cmds = drive_data / DRIVE_CONFIG_SUBDIR / "command"
    drive_copied = copy_commands(drive_cmds, Kilo_COMMAND_DIR)
    if drive_copied:
        print(f"OK -- synced {len(drive_copied)} Drive command(s) -> {Kilo_COMMAND_DIR}")

    print(_report(drive_data, template_path, secrets))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
