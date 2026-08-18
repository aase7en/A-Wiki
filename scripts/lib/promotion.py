"""A-Wiki Memory Plane — promotion pipeline (Phase 5).

The ONLY path from project experience to L3 global knowledge (kernel §5):

    Distill → Privacy Check → Generalize → Evidence Check → Global Promotion

Hard contract:
  - default mode: manual-with-evidence, DRY-RUN first (no writes)
  - no automatic L0/L1/L4 → L3; no background/scheduled promotion
  - privacy gate reuses the kernel's single security-pattern source +
    the Phase-4 absolute/private path detector (no parallel scanner)
  - evidence gate: provenance must be an accepted type with a real value
    and no private-machine paths
  - apply writes ONE reviewable candidate file under
    wiki/promotion-candidates/ — never Git refs, remotes, push, merge, deploy
"""
from __future__ import annotations

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "project"))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "hooks"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import validate as project_validate          # noqa: E402 -- Phase-4 validator
from project_memory import ScopeDenied       # noqa: E402 -- one scope-denial contract
from _scan_staged_diff import PATTERNS, PLACEHOLDERS  # noqa: E402 -- one pattern source

CANDIDATES_DIR = REPO_ROOT / "wiki" / "promotion-candidates"

ACCEPTED_EVIDENCE_TYPES = {
    "commit_sha", "tests_passed", "experiment_id", "adr_path",
    "wiki_ref", "review_finding", "task_ref", "handoff_ref",
}

# Generalization gate: project-specific shapes that must not survive into L3.
_PROJECT_SPECIFIC_RE = re.compile(
    r"\b(?:at\s+project\s+[a-z0-9-]+|"
    r"(?:prod|staging|dev)-[a-z0-9-]*\d+|"
    r"server-[a-z0-9-]+|"
    r"\b\d{1,3}(?:\.\d{1,3}){3}\b)"
)

_SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")
# (ScopeDenied imported from project_memory — one contract across the plane)
_EVIDENCE_VALUE_PATTERNS = {
    "commit_sha": _SHA_RE,
    "experiment_id": re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$"),
}


# ScopeDenied is imported from project_memory (one contract across the plane).

def _gate(name: str, passed: bool, detail: str) -> dict:
    return {"gate": name, "passed": passed, "detail": detail}


def _privacy_findings(text: str) -> list[str]:
    findings = []
    lowered = text.lower()
    for name, regex, allowlist in PATTERNS:
        m = regex.search(text)
        if not m:
            continue
        window = lowered[max(0, m.start() - 40): m.end() + 40]
        if any(a in window for a in allowlist) or any(p in window for p in PLACEHOLDERS):
            continue
        findings.append(f"secret-shaped match [{name}]")
        break
    if project_validate.ABSOLUTE_PATH_RE.search(text):
        findings.append("absolute/private machine path")
    return findings


def _provenance_errors(provenance: dict | None) -> list[str]:
    if not isinstance(provenance, dict):
        return ["provenance missing (no evidence → no promotion)"]
    etype = provenance.get("type")
    value = provenance.get("value")
    errors: list[str] = []
    if etype not in ACCEPTED_EVIDENCE_TYPES:
        errors.append(f"evidence type not accepted: {etype!r}")
        return errors
    if not isinstance(value, str) or not value.strip():
        errors.append("evidence value empty")
        return errors
    pat = _EVIDENCE_VALUE_PATTERNS.get(etype)
    if pat and not pat.match(value):
        errors.append(f"evidence value malformed for {etype}: {value!r}")
    if project_validate.ABSOLUTE_PATH_RE.search(value):
        errors.append("provenance contains a private-machine path")
    return errors


def promote(project_root: Path, distilled: str, provenance: dict | None,
            *, dry_run: bool = True) -> dict:
    """Run the five-gate pipeline. Returns a gate-by-gate report.

    dry_run=True (default) performs ZERO writes. dry_run=False writes exactly
    one reviewable markdown candidate into CANDIDATES_DIR — nothing else.
    """
    project_root = Path(project_root).resolve()

    # ── adapter + scope gates (fail closed; reuse Phase 4) ──
    result = project_validate.validate(project_root)
    if result.exit_code() != 0:
        return {"ok": False, "gates": [_gate("adapter", False,
                                             "project adapter invalid (fail closed)")]}
    data = yaml.safe_load(
        (project_root / ".awiki" / "project.yaml").read_text(encoding="utf-8"))
    scopes = (data.get("memory") or {}).get("scopes") or {}
    if scopes.get("global") is not True:
        raise ScopeDenied("memory.scopes.global is not enabled — promotion denied")

    pid = data.get("id", "project")
    gates: list[dict] = []

    # ── 1. Distill ──
    text = (distilled or "").strip()
    is_distilled = bool(text) and len(text) <= 2000 and "\n\n\n" not in text
    gates.append(_gate("distill", is_distilled,
                       "concise candidate lesson" if is_distilled else
                       "empty or transcript-dump-shaped candidate"))

    # ── 2. Privacy ──
    priv = _privacy_findings(text)
    gates.append(_gate("privacy", not priv, "; ".join(priv) or "clean"))

    # ── 3. Generalize ──
    specific = _PROJECT_SPECIFIC_RE.findall(text)
    gates.append(_gate("generalize", not specific,
                       "project-specific references removed" if not specific else
                       f"project-specific detail present: {sorted(set(specific))[:5]}"))

    # ── 4. Evidence ──
    ev_errors = _provenance_errors(provenance)
    gates.append(_gate("provenance-evidence", not ev_errors,
                       "; ".join(ev_errors) or "provenance accepted"))

    ok = all(g["passed"] for g in gates)
    outcome = {"ok": ok, "gates": gates, "written": False}

    # ── 5. Global Promotion (dry-run first) ──
    if ok:
        slug = re.sub(r"[^a-z0-9-]+", "-", text.lower())[:60].strip("-") or "candidate"
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        path = CANDIDATES_DIR / f"{stamp}-{slug}.md"
        front = (
            "---\n"
            "schema: awiki-promotion-candidate/v1\n"
            f"project: {pid}\n"
            f"provenance: {provenance['type']}={provenance['value']}\n"
            f"created_at: {datetime.now(timezone.utc).isoformat()}\n"
            "---\n\n"
        )
        def _report_path(p: Path) -> str:
            try:
                return str(p.relative_to(REPO_ROOT))
            except ValueError:
                return str(p)  # externally-injected candidates dir (tests)

        if dry_run:
            outcome["dry_run"] = True
            outcome["candidate_path"] = _report_path(path)
            gates.append(_gate("promotion", True,
                               f"DRY-RUN — would write {_report_path(path)}"))
        else:
            CANDIDATES_DIR.mkdir(parents=True, exist_ok=True)
            path.write_text(front + text + "\n", encoding="utf-8")
            outcome["written"] = True
            outcome["candidate_path"] = _report_path(path)
            gates.append(_gate("promotion", True,
                               f"candidate written: {_report_path(path)} "
                               f"(no Git refs/remotes touched)"))
    return outcome
