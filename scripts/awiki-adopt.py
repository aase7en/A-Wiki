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


def _write_json_if(path: Path, build) -> bool:
    """Merge-shaped write; returns True when the file changed."""
    data = {}
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
    new = build(data)
    if new == data:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(new, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    return True


def _install_provider_configs(target: Path, brain: Path) -> dict:
    changed = {}
    changed["claude"] = _write_json_if(
        target / ".claude" / "settings.json",
        lambda d: {**d, "hooks": _sweeps(brain, "claude")})
    changed["zcode"] = _write_json_if(
        target / ".zcode" / "config.json",
        lambda d: {**d, "hooks": {"enabled": True,
                                   "events": _sweeps(brain, "zcode")}})
    changed["codex"] = _write_json_if(
        target / ".codex" / "hooks.json",
        lambda d: {**d, "hooks": _sweeps(brain, "codex")})
    return changed


def _install_mcp(target: Path, brain: Path) -> bool:
    def build(d):
        # copy — mutating the loaded dict in place would make `new == data`
        # trivially true and silently skip the write (caught by tests)
        servers = dict(d.get("mcpServers", {}))
        servers["awiki"] = {
            "command": sys.executable,
            "args": [str(brain / "scripts" / "mcp-wiki-server.py")],
            "env": {"AWIKI_ROOT": str(brain)},
        }
        return {**d, "mcpServers": servers}
    return _write_json_if(target / ".mcp.json", build)


def _install_seeds(target: Path, brain: Path) -> dict:
    out = {}
    for name, body in (("BRAIN-ENTRY.md", BRAIN_ENTRY), ("COLLAB.md", COLLAB)):
        f = target / name
        if not f.is_file():
            f.write_text(body, encoding="utf-8")
            out[name] = True
        else:
            out[name] = False
    agents = target / "AGENTS.md"
    text = agents.read_text(encoding="utf-8") if agents.is_file() else ""
    if AGENT_SECTION_MARKER not in text:
        section = (f"\n\n## {AGENT_SECTION_MARKER}\n\n"
                   f"- Brain root: `{brain}` (จุดเดียวที่จริง — hooks/MCP/สมองชี้มาที่นี่)\n"
                   f"- อ่าน `BRAIN-ENTRY.md` ทุกครั้งที่เริ่ม session ใน repo นี้\n"
                   f"- เริ่มงาน: `/A <objective>` · ค้นสมอง: `awiki search` หรือ MCP `awiki`\n")
        agents.write_text(text + section, encoding="utf-8")
        out["AGENTS.md"] = True
    else:
        out["AGENTS.md"] = False
    gi = target / ".gitignore"
    gi_text = gi.read_text(encoding="utf-8") if gi.is_file() else ""
    if ".tmp/" not in gi_text:
        gi.write_text(gi_text.rstrip() + "\n.tmp/\n", encoding="utf-8")
        out[".gitignore"] = True
    else:
        out[".gitignore"] = False
    return out


def _verify(target: Path, brain: Path) -> list[str]:
    """Drift check: everything we install must be exactly present."""
    problems = []
    try:
        claude = json.loads((target / ".claude" / "settings.json").read_text(encoding="utf-8"))
        if "PreToolUse" not in claude.get("hooks", {}):
            problems.append(".claude/settings.json missing PreToolUse sweeps")
    except (OSError, json.JSONDecodeError):
        problems.append(".claude/settings.json unreadable/missing")
    for rel in (".zcode/config.json", ".codex/hooks.json"):
        try:
            json.loads((target / rel).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            problems.append(f"{rel} unreadable/missing")
    try:
        mcp = json.loads((target / ".mcp.json").read_text(encoding="utf-8"))
        if "awiki" not in mcp.get("mcpServers", {}):
            problems.append(".mcp.json missing awiki server")
    except (OSError, json.JSONDecodeError):
        problems.append(".mcp.json unreadable/missing")
    for name in ("BRAIN-ENTRY.md", "COLLAB.md"):
        if not (target / name).is_file():
            problems.append(f"{name} missing")
    agents = target / "AGENTS.md"
    if not (agents.is_file() and AGENT_SECTION_MARKER in agents.read_text(encoding="utf-8")):
        problems.append("AGENTS.md adopted section missing")
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
