"""skill_pipeline.py — Slice B: unlimited skill updates, framed.

Flow (Iron Law #3 — the user is the Senior Critic, nothing auto-applies):

  signal (promoted wiki page / external find / failure pattern)
      -> propose_*()  : durable proposal queued at <queue_dir>/<id>.json
                        with a DRAFT SKILL.md inside
      -> run_eval()   : auto-generated deterministic suite (skillopt
                        awiki_eval, no LLM) marks ready / failed
      -> approve()    : ONE command -> new-skill --apply + regen +
                        provenance in the proposal + ledger note

Storage: one JSON per proposal; status in draft|ready|failed|approved.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Callable

_MIN_DRAFT_CHARS = 200
_FORBIDDEN_HINTS = ["sk-", "ghp_", "AKIA", "password ="]


def _now() -> float:
    return round(time.time(), 3)


def _slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9-]+", "-", name.strip().lower()).strip("-")
    if not s:
        raise ValueError(f"cannot derive a skill id from {name!r}")
    return s


def _parse_fm(text: str) -> tuple[dict, str]:
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if not m:
        return {}, text
    fm: dict[str, Any] = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip()] = v.strip()
    return fm, m.group(2)


def _first_sentence(body: str) -> str:
    for para in body.split("\n\n"):
        t = para.strip().lstrip("# ").strip()
        if t:
            return t[:160]
    return ""


def _draft_skill_md(pid: str, description: str, when_to_use: str,
                    provenance: str) -> str:
    return f"""---
name: {pid}
description: "{description}"
version: 0.1.0
domain: [general]
lifecycle_phase: none
category: pipeline
agents: [all]
status: canonical
invocation: auto
---

# {pid}

> Draft จาก skill pipeline — รอผู้ใช้ approve

## เมื่อไหร่ใช้
{when_to_use}

## สิ่งที่ทำ
{description}

## Provenance
- {provenance}
- สร้างอัตโนมัติโดย scripts/lib/skill_pipeline.py {time.strftime('%Y-%m-%d')}
- แก้ไขต่อได้ — นี่คือจุดตั้งต้น ไม่ใช่ของสำเร็จรูป
"""


def _save(queue_dir: Path, prop: dict) -> None:
    queue_dir.mkdir(parents=True, exist_ok=True)
    (queue_dir / f"{prop['id']}.json").write_text(
        json.dumps(prop, ensure_ascii=False, indent=2), encoding="utf-8")


def load(pid: str, queue_dir: Path) -> dict:
    p = Path(queue_dir) / f"{pid}.json"
    if not p.is_file():
        raise FileNotFoundError(f"no proposal {pid!r} in {queue_dir}")
    return json.loads(p.read_text(encoding="utf-8"))


def propose_from_page(page: Path, queue_dir: Path,
                      source_note: str = "") -> dict:
    """Promoted wiki content -> skill proposal (idempotent by page stem)."""
    pid = _slug(Path(page).stem)
    existing = Path(queue_dir) / f"{pid}.json"
    if existing.is_file():
        return json.loads(existing.read_text(encoding="utf-8"))
    fm, body = _parse_fm(Path(page).read_text(encoding="utf-8"))
    title = fm.get("title", pid)
    desc = _first_sentence(body) or f"ทำงานตามความรู้จาก {title}"
    when = fm.get("when_to_use") or f"เมื่องานตรงกับเนื้อหา {title}"
    prop = {
        "id": pid, "source": "content", "status": "draft",
        "created_at": _now(),
        "source_note": source_note or f"wiki page: {page}",
        "page": str(page), "title": title,
        "description": desc,
        "when_to_use": when,
        "skill_md": _draft_skill_md(
            pid, desc, when,
            source_note or f"wiki page: {page}"),
        "eval": None,
    }
    _save(Path(queue_dir), prop)
    return prop


def propose_external(name: str, description: str, url: str,
                     queue_dir: Path) -> dict:
    pid = _slug(name)
    existing = Path(queue_dir) / f"{pid}.json"
    if existing.is_file():
        return json.loads(existing.read_text(encoding="utf-8"))
    prop = {
        "id": pid, "source": "external", "status": "draft",
        "created_at": _now(), "url": url,
        "description": description,
        "when_to_use": f"เมื่องานตรงกับสิ่งที่ {pid} ทำ (จากแหล่งภายนอก)",
        "skill_md": _draft_skill_md(
            pid, description,
            f"เมื่องานตรงกับสิ่งที่ {pid} ทำ",
            f"external find: {url}"),
        "eval": None,
    }
    _save(Path(queue_dir), prop)
    return prop


def _build_suite(prop: dict) -> dict:
    """Deterministic suite from the proposal itself: the draft must carry
    its own identity, be substantial, and leak nothing."""
    required = [f"name: {prop['id']}", f"# {prop['id']}",
                "## เมื่อไหร่ใช้", "## Provenance"]
    keywords = [w for w in re.findall(r"[A-Za-z\u0E00-\u0E7F-]{6,}",
                                      prop["description"])[:3]]
    required.extend(keywords)
    return {
        "suite": f"pipeline-{prop['id']}",
        "description": "Auto-generated quality gate for a pipeline proposal",
        "cases": [{
            "id": "draft-quality",
            "skill": "__DRAFT__",
            "required": required,
            "forbidden": _FORBIDDEN_HINTS,
            "min_chars": _MIN_DRAFT_CHARS,
        }],
    }


def run_eval(pid: str, queue_dir: Path, brain_root: Path,
             scratch: Path) -> dict:
    """Generate a suite, run the deterministic evaluator, mark ready/failed."""
    prop = load(pid, queue_dir)
    scratch = Path(scratch); scratch.mkdir(parents=True, exist_ok=True)
    skill_path = scratch / f"{pid}-draft-SKILL.md"
    skill_path.write_text(prop["skill_md"], encoding="utf-8")
    suite_path = scratch / f"{pid}-suite.json"
    suite = _build_suite(prop)
    suite_path.write_text(json.dumps(suite, ensure_ascii=False, indent=2),
                          encoding="utf-8")

    import sys
    sys.path.insert(0, str(Path(brain_root) / "scripts" / "skillopt"))
    import awiki_eval
    result = awiki_eval.evaluate_suite(suite_path,
                                        skill_override=str(skill_path))
    passed = bool(result.get("passed"))
    case = suite["cases"][0]
    prop["eval"] = {
        "suite": {"required": case["required"],
                   "forbidden": case["forbidden"],
                   "min_chars": case.get("min_chars")},
        "result": result,
        "passed": passed, "ran_at": _now(),
    }
    prop["status"] = "ready" if passed else "failed"
    _save(Path(queue_dir), prop)
    return prop["eval"]


def _default_apply(prop: dict) -> tuple[int, str]:
    import subprocess, sys
    cmd = [sys.executable, "scripts/new-skill.py", prop["id"],
           "--domain", "general", "--phase", "none", "--apply"]
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=300)
    return proc.returncode, (proc.stdout + proc.stderr)[-500:]


def approve(pid: str, queue_dir: Path,
            apply_fn: Callable[[dict], tuple[int, str]] | None = None) -> int:
    """The ONE button. ready proposals only; records provenance."""
    prop = load(pid, queue_dir)
    if prop.get("status") != "ready":
        print(f"❌ {pid} is {prop.get('status')} — run_eval must pass first "
              f"(Iron Law #3: quality gate before apply)")
        return 1
    apply_fn = apply_fn or _default_apply
    rc, log = apply_fn(prop)
    if rc != 0:
        prop["status"] = "apply_failed"
        prop["apply_log"] = log
        _save(Path(queue_dir), prop)
        print(f"❌ apply failed: {log}")
        return rc or 1
    prop["status"] = "approved"
    prop["approved_at"] = _now()
    _save(Path(queue_dir), prop)
    print(f"✅ {pid} approved + applied — run regen-skill-surfaces + commit")
    return 0


def list_proposals(queue_dir: Path) -> list[dict]:
    q = Path(queue_dir)
    if not q.is_dir():
        return []
    out = []
    for f in sorted(q.glob("*.json")):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            out.append({k: d.get(k) for k in
                        ("id", "source", "status", "title", "url",
                         "description", "created_at")})
        except (json.JSONDecodeError, OSError):
            continue
    return out


# ── skill-scout: registry gaps -> external finds -> same queue ──────────
def _search_external(gap: str, limit: int = 3) -> list[dict]:
    """Live search via gh (GitHub). Overridable in tests."""
    import subprocess
    try:
        out = subprocess.run(
            ["gh", "search", "repos", gap, "--limit", str(limit),
             "--json", "name,description,url"],
            capture_output=True, text=True, timeout=60,
        )
        if out.returncode != 0:
            return []
        rows = json.loads(out.stdout or "[]")
        return [{"name": r["name"],
                 "description": (r.get("description") or r["name"])[:200],
                 "url": r["url"]} for r in rows]
    except Exception:
        return []


def _registry_covers(registry_path: Path, gap: str) -> bool:
    """Covered = ONE canonical skill carries >=2 of the gap's terms —
    scattered hits across different skills are NOT coverage (the excel/
    repair trap: excel-generator + debug tools made a bag-of-terms check
    claim a nonexistent 'excel formula repair' skill)."""
    reg = json.loads(Path(registry_path).read_text(encoding="utf-8"))
    terms = {t.lower() for t in re.findall(r"[A-Za-z][A-Za-z0-9-]{3,}", gap)}
    for s in reg.get("skills", []):
        if s.get("status") != "canonical":
            continue
        hay = (s.get("name", "") + " " + (s.get("description") or "")).lower()
        if sum(1 for t in terms if t in hay) >= 2:
            return True
    return False


def scout_gaps(gaps: list[str], queue_dir: Path,
               registry_path: Path, limit: int = 3) -> list[dict]:
    """For each UNCOVERED gap: search externally and queue proposals.
    Returns only newly created proposals."""
    created: list[dict] = []
    q = Path(queue_dir)
    for gap in gaps:
        if _registry_covers(registry_path, gap):
            continue
        for hit in _search_external(gap, limit):
            existing = q / f"{_slug(hit['name'])}.json"
            if existing.is_file():
                continue
            prop = propose_external(hit["name"], hit["description"],
                                     hit["url"], q)
            created.append(prop)
    return created
