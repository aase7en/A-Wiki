"""awiki-adopt.py — embed the A-Wiki brain into any repo (Slice A).

    python scripts/awiki-adopt.py <target-repo> [--brain <A-Wiki>] [--check]

What lands in the TARGET repo (never anywhere else):
  .claude/settings.json   hook sweeps -> "<python> <brain>/hooks_runner.py"
  .zcode/config.json      hook sweeps (same brain runner, abs path)
  .codex/hooks.json       hook sweeps (same)
  .mcp.json               awiki server -> <brain>/scripts/mcp-wiki-server.py
  BRAIN-ENTRY.md          wake-up index for agents landing in this repo
  COLLAB.md               claim lanes (cross-agent-work-orders protocol)
  AGENTS.md               appended "A-Wiki Brain (adopted)" section
  .gitignore              + .tmp/ (runtime claims/ledgers live there)

Design: idempotent (re-adopt is a no-op), --check reports drift (rc 1),
absolute brain paths so nothing about the target's layout is assumed.
"""
from __future__ import annotations

import argparse
import json
import stat
import sys
from pathlib import Path

AGENT_SECTION_MARKER = "A-Wiki Brain (adopted)"

BRAIN_ENTRY = """# BRAIN-ENTRY — สมองอยู่ที่ไหนสำหรับ agent ที่ตื่นมาใน repo นี้

> คำสั่งทั้งหมดชี้กลับ **A-Wiki brain** (ดู path ใน `AGENTS.md` ส่วน adopted)

1. อ่าน `COLLAB.md` ก่อนแตะอะไร (จอง claim ตาม lane)
2. ถามสมอง: `awiki search "<คำถาม>"` หรือเรียก MCP tool `awiki`
3. Gates ทำงานอยู่แล้วผ่าน hooks — ห้ามแก้ `raw/`, ห้าม secret ขึ้น git,
   งานไม่ trivial เดิน spine `/A <objective>`

กฎเหล็กฉบับย่อ: test ก่อนโค้ด · root cause ก่อนแก้บั๊ก · raw/ immutable
"""

COLLAB = """# COLLAB — lanes & claims (A-Wiki cross-agent-work-orders standard)

| Lane | ขอบเขต | ผู้ถือ |
|---|---|---|
| app | โค้ดหลักของ repo นี้ | — |

**กติกา:** ก่อนแตะไฟล์ร่วม → จองแถวในตารางนี้ (topic/agent/วัน/ไฟล์) ·
จบงานหรือพัก → ปิดแถว · conflict สงสัย → ถาม user ก่อนเขียน
"""


def _hook_cmd(brain: Path, provider: str, event: str) -> str:
    py = sys.executable.replace("\\", "/")
    return (f'"{py}" "{brain}/scripts/hooks_runner.py" '
            f"--provider {provider} --event {event}")


def _sweeps(brain: Path, provider: str) -> dict:
    ev = lambda e: [{"matcher": "", "hooks": [
        {"type": "command", "command": _hook_cmd(brain, provider, e),
         "timeout": 30}]}]
    ptu = lambda m: [{"matcher": m, "hooks": [
        {"type": "command", "command": _hook_cmd(brain, provider, "PreToolUse"),
         "timeout": 30}]}]
    return {
        "SessionStart": ev("SessionStart"),
        "UserPromptSubmit": ev("UserPromptSubmit"),
        "PreToolUse": ptu("Edit|Write|MultiEdit") + ptu("Bash") + ptu("Agent"),
        "PostToolUse": [
            {"matcher": "Edit|Write|MultiEdit",
             "hooks": [{"type": "command",
                        "command": _hook_cmd(brain, provider, "PostToolUse"),
                        "timeout": 30}]},
        ],
        "Stop": ev("Stop"),
    }


def _path_is_link_like(path: Path) -> bool:
    """Detect symlinks and Windows reparse points without following them."""
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    except OSError as exc:
        raise ValueError(f"cannot inspect config surface {path}: {exc}") from exc
    attrs = getattr(info, "st_file_attributes", 0)
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    return bool(stat.S_ISLNK(info.st_mode) or (reparse and attrs & reparse))


def _assert_safe_surface(target: Path, path: Path) -> None:
    """Reject any linked/reparse component below the resolved target root."""
    try:
        relative = path.relative_to(target)
    except ValueError as exc:
        raise ValueError(f"config surface escapes target repo: {path}") from exc
    current = target
    for part in relative.parts:
        current = current / part
        if _path_is_link_like(current):
            raise ValueError(f"linked config surface is not writable/readable: {current}")


def _read_json_object(path: Path) -> dict:
    """Read a JSON object without ever treating malformed input as empty."""
    if not path.is_file():
        return {}
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ValueError(f"{path} unreadable: {exc}") from exc
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path} invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path} root must be a JSON object")
    return data


def _write_json_if(path: Path, build, *, target: Path) -> bool:
    """Non-destructive merge-shaped write; linked/malformed input fails closed."""
    _assert_safe_surface(target, path)
    data = _read_json_object(path)
    new = build(data)
    if not isinstance(new, dict):
        raise ValueError(f"{path} builder must return a JSON object")
    if new == data:
        return False
    _assert_safe_surface(target, path)
    path.parent.mkdir(parents=True, exist_ok=True)
    _assert_safe_surface(target, path)
    path.write_text(json.dumps(new, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    return True


def _is_awiki_hook(hook: dict) -> bool:
    """Identify hook entries owned by A-Wiki, including stale brain/provider paths."""
    if not isinstance(hook, dict):
        return False
    command = hook.get("command")
    if not isinstance(command, str):
        return False
    normalized = command.replace("\\", "/")
    return ("scripts/hooks_runner.py" in normalized
            and "--provider " in command
            and "--event " in command)


def _foreign_blocks(blocks, *, where: str) -> list:
    """Strip only A-Wiki hook entries while preserving foreign block metadata."""
    if not isinstance(blocks, list):
        raise ValueError(f"{where} must be a list")
    kept = []
    for index, block in enumerate(blocks):
        if not isinstance(block, dict):
            raise ValueError(f"{where}[{index}] must be an object")
        if "hooks" not in block:
            kept.append(dict(block))
            continue
        hooks = block["hooks"]
        if not isinstance(hooks, list):
            raise ValueError(f"{where}[{index}].hooks must be a list")
        foreign = []
        for hook_index, hook in enumerate(hooks):
            if not isinstance(hook, dict):
                raise ValueError(
                    f"{where}[{index}].hooks[{hook_index}] must be an object")
            if not _is_awiki_hook(hook):
                foreign.append(hook)
        if foreign:
            out = dict(block)
            out["hooks"] = foreign
            kept.append(out)
        elif not hooks:
            kept.append(dict(block))
    return kept


def _merge_sweeps(existing: dict, brain: Path, provider: str) -> dict:
    if not isinstance(existing, dict):
        raise ValueError(f"{provider} hooks/events must be an object")
    canonical = _sweeps(brain, provider)
    merged = {}
    for event, blocks in existing.items():
        foreign = _foreign_blocks(blocks, where=f"{provider}.{event}")
        if foreign or blocks == []:
            merged[event] = foreign
    for event, blocks in canonical.items():
        merged.setdefault(event, []).extend(blocks)
    return merged


def _provider_events(data: dict, provider: str) -> dict:
    hooks = data.get("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError(f"{provider} hooks must be an object")
    if provider != "zcode":
        return hooks
    events = hooks.get("events", {})
    if not isinstance(events, dict):
        raise ValueError("zcode hooks.events must be an object")
    return events


def _build_provider(data: dict, brain: Path, provider: str) -> dict:
    existing = _provider_events(data, provider)
    merged_events = _merge_sweeps(existing, brain, provider)
    if provider != "zcode":
        return {**data, "hooks": merged_events}
    hooks = dict(data.get("hooks", {}))
    hooks["enabled"] = True
    hooks["events"] = merged_events
    return {**data, "hooks": hooks}


def _provider_path(target: Path, provider: str) -> Path:
    return {
        "claude": target / ".claude" / "settings.json",
        "zcode": target / ".zcode" / "config.json",
        "codex": target / ".codex" / "hooks.json",
    }[provider]


def _canonical_mcp_entry(brain: Path) -> dict:
    return {
        "command": sys.executable,
        "args": [str(brain / "scripts" / "mcp-wiki-server.py")],
        "env": {"AWIKI_ROOT": str(brain)},
    }


def _build_mcp(data: dict, brain: Path) -> dict:
    servers = data.get("mcpServers", {})
    if not isinstance(servers, dict):
        raise ValueError(".mcp.json mcpServers must be an object")
    servers = dict(servers)
    servers["awiki"] = _canonical_mcp_entry(brain)
    return {**data, "mcpServers": servers}


def _mutable_surfaces(target: Path) -> list[Path]:
    return [
        _provider_path(target, "claude"),
        _provider_path(target, "zcode"),
        _provider_path(target, "codex"),
        target / ".mcp.json",
        target / "BRAIN-ENTRY.md",
        target / "COLLAB.md",
        target / "AGENTS.md",
        target / ".gitignore",
    ]


def _validate_install_inputs(target: Path, brain: Path) -> None:
    """Validate every mutable surface before writing any of them."""
    for path in _mutable_surfaces(target):
        _assert_safe_surface(target, path)
    for provider in ("claude", "zcode", "codex"):
        data = _read_json_object(_provider_path(target, provider))
        _build_provider(data, brain, provider)
    mcp = _read_json_object(target / ".mcp.json")
    _build_mcp(mcp, brain)


def _install_provider_configs(target: Path, brain: Path) -> dict:
    changed = {}
    for provider in ("claude", "zcode", "codex"):
        changed[provider] = _write_json_if(
            _provider_path(target, provider),
            lambda d, p=provider: _build_provider(d, brain, p),
            target=target)
    return changed


def _install_mcp(target: Path, brain: Path) -> bool:
    return _write_json_if(target / ".mcp.json",
                          lambda d: _build_mcp(d, brain), target=target)

def _brain_root_line(brain: Path) -> str:
    return f"- Brain root: `{brain}` (จุดเดียวที่จริง — hooks/MCP/สมองชี้มาที่นี่)"


def _has_exact_line(text: str, expected: str) -> bool:
    return any(line.strip() == expected for line in text.splitlines())


def _repair_brain_root_line(text: str, brain: Path) -> str:
    """Repair only the A-Wiki-owned Brain root line; preserve target text."""
    marker_line = f"## {AGENT_SECTION_MARKER}"
    lines = text.splitlines(keepends=True)
    marker_index = next((i for i, line in enumerate(lines)
                         if line.rstrip("\r\n") == marker_line), None)
    if marker_index is None:
        return text
    expected = _brain_root_line(brain)
    for index in range(marker_index + 1, len(lines)):
        stripped = lines[index].rstrip("\r\n")
        if stripped.startswith("## "):
            break
        if stripped.startswith("- Brain root: `"):
            ending = "\r\n" if lines[index].endswith("\r\n") else "\n"
            lines[index] = expected + ending
            return "".join(lines)
    ending = "\r\n" if any(line.endswith("\r\n") for line in lines) else "\n"
    lines.insert(marker_index + 1, ending + expected + ending)
    return "".join(lines)


def _install_seeds(target: Path, brain: Path) -> dict:
    out = {}
    for name, body in (("BRAIN-ENTRY.md", BRAIN_ENTRY), ("COLLAB.md", COLLAB)):
        f = target / name
        _assert_safe_surface(target, f)
        if not f.is_file():
            f.write_text(body, encoding="utf-8")
            out[name] = True
        else:
            out[name] = False
    agents = target / "AGENTS.md"
    _assert_safe_surface(target, agents)
    text = agents.read_text(encoding="utf-8") if agents.is_file() else ""
    if AGENT_SECTION_MARKER not in text:
        section = (f"\n\n## {AGENT_SECTION_MARKER}\n\n"
                   f"{_brain_root_line(brain)}\n"
                   f"- อ่าน `BRAIN-ENTRY.md` ทุกครั้งที่เริ่ม session ใน repo นี้\n"
                   f"- เริ่มงาน: `/A <objective>` · ค้นสมอง: `awiki search` หรือ MCP `awiki`\n")
        agents.write_text(text + section, encoding="utf-8")
        out["AGENTS.md"] = True
    else:
        repaired = _repair_brain_root_line(text, brain)
        if repaired != text:
            agents.write_text(repaired, encoding="utf-8")
            out["AGENTS.md"] = True
        else:
            out["AGENTS.md"] = False
    gi = target / ".gitignore"
    _assert_safe_surface(target, gi)
    gi_text = gi.read_text(encoding="utf-8") if gi.is_file() else ""
    if not _has_exact_line(gi_text, ".tmp/"):
        gi.write_text(gi_text.rstrip() + "\n.tmp/\n", encoding="utf-8")
        out[".gitignore"] = True
    else:
        out[".gitignore"] = False
    return out


def _owned_sweeps(events: dict, provider: str) -> dict:
    """Normalize only A-Wiki-owned wiring; foreign additions are intentionally ignored."""
    if not isinstance(events, dict):
        raise ValueError(f"{provider} hooks/events must be an object")
    owned = {}
    for event, blocks in events.items():
        if not isinstance(blocks, list):
            raise ValueError(f"{provider}.{event} must be a list")
        owned_blocks = []
        for index, block in enumerate(blocks):
            if not isinstance(block, dict):
                raise ValueError(f"{provider}.{event}[{index}] must be an object")
            hooks = block.get("hooks", [])
            if not isinstance(hooks, list):
                raise ValueError(f"{provider}.{event}[{index}].hooks must be a list")
            owned_hooks = []
            for hook_index, hook in enumerate(hooks):
                if not isinstance(hook, dict):
                    raise ValueError(
                        f"{provider}.{event}[{index}].hooks[{hook_index}] must be an object")
                if _is_awiki_hook(hook):
                    owned_hooks.append(hook)
            if owned_hooks:
                normalized = {key: value for key, value in block.items()
                              if key != "hooks"}
                normalized["hooks"] = owned_hooks
                owned_blocks.append(normalized)
        if owned_blocks:
            owned[event] = owned_blocks
    return owned


def _verify(target: Path, brain: Path) -> list[str]:
    """Verify exact A-Wiki-owned wiring while allowing unrelated foreign config."""
    problems = []
    for provider in ("claude", "zcode", "codex"):
        path = _provider_path(target, provider)
        rel = path.relative_to(target).as_posix()
        try:
            _assert_safe_surface(target, path)
            data = _read_json_object(path)
            events = _provider_events(data, provider)
            actual = _owned_sweeps(events, provider)
            expected = _sweeps(brain, provider)
            if actual != expected:
                problems.append(f"{rel} A-Wiki hook wiring drift")
            if provider == "zcode" and data.get("hooks", {}).get("enabled") is not True:
                problems.append(f"{rel} A-Wiki hooks not enabled")
        except ValueError as exc:
            problems.append(f"{rel} invalid: {exc}")

    try:
        _assert_safe_surface(target, target / ".mcp.json")
        mcp = _read_json_object(target / ".mcp.json")
        servers = mcp.get("mcpServers", {})
        if not isinstance(servers, dict):
            problems.append(".mcp.json mcpServers must be an object")
        elif servers.get("awiki") != _canonical_mcp_entry(brain):
            problems.append(".mcp.json A-Wiki server wiring drift")
    except ValueError as exc:
        problems.append(f".mcp.json invalid: {exc}")

    for name in ("BRAIN-ENTRY.md", "COLLAB.md"):
        path = target / name
        try:
            _assert_safe_surface(target, path)
        except ValueError as exc:
            problems.append(f"{name} invalid: {exc}")
            continue
        if not path.is_file():
            problems.append(f"{name} missing")
    agents = target / "AGENTS.md"
    try:
        _assert_safe_surface(target, agents)
        agents_text = agents.read_text(encoding="utf-8") if agents.is_file() else ""
        agents_ok = (AGENT_SECTION_MARKER in agents_text
                     and _has_exact_line(agents_text, _brain_root_line(brain)))
    except (OSError, UnicodeDecodeError, ValueError):
        agents_ok = False
    if not agents_ok:
        problems.append("AGENTS.md adopted wiring drift")

    gi = target / ".gitignore"
    try:
        _assert_safe_surface(target, gi)
        gi_text = gi.read_text(encoding="utf-8") if gi.is_file() else ""
        if not _has_exact_line(gi_text, ".tmp/"):
            problems.append(".gitignore missing A-Wiki .tmp/ rule")
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        problems.append(f".gitignore invalid: {exc}")
    return problems

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Embed the A-Wiki brain into a repo")
    ap.add_argument("target", help="path to the repo adopting the brain")
    ap.add_argument("--brain", default=str(Path(__file__).resolve().parents[1]),
                    help="A-Wiki brain root (default: this brain)")
    ap.add_argument("--check", action="store_true",
                    help="verify only; exit 1 on drift, 2 if not adopted")
    args = ap.parse_args(argv)

    target = Path(args.target).resolve()
    brain = Path(args.brain).resolve()
    if not (brain / "scripts" / "hooks_runner.py").is_file():
        print(f"❌ brain invalid (no scripts/hooks_runner.py): {brain}")
        return 2
    if not (target / ".git").exists():
        print(f"❌ {target} is not a git repo (refusing)")
        return 2

    if args.check:
        problems = _verify(target, brain)
        if problems:
            for p in problems:
                print(f"❌ {p}")
            return 1
        print("✅ adopted brain wiring intact")
        return 0

    try:
        _validate_install_inputs(target, brain)
    except ValueError as exc:
        print(f"❌ refusing to overwrite existing config: {exc}")
        return 1

    print(f"🔧 Adopting A-Wiki brain into {target.name} "
          f"(brain: {brain}) ...")
    changed = _install_provider_configs(target, brain)
    changed["mcp"] = _install_mcp(target, brain)
    changed.update(_install_seeds(target, brain))
    for name, ok in changed.items():
        print(f"  {'✓ installed' if ok else '• already'}  {name}")
    problems = _verify(target, brain)
    if problems:
        for p in problems:
            print(f"❌ {p}")
        return 1
    print("✅ done — any agent opened in this repo now runs under brain gates")
    return 0


if __name__ == "__main__":
    sys.exit(main())
