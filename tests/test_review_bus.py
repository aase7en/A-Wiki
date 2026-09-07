"""Review Bus engine — Phase 8 (eval/promotion + automated reviewer
foundations), acceptance criteria from
docs/migration/awiki-agent-review-bus-plan.md §16.

12 criteria under test, mapped 1:1 (see each test docstring). The engine
owns STATE only — it never touches git (no merge/push anywhere), and every
state it writes validates against schemas/awiki-review/v1.schema.json.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

import review_bus as rb  # noqa: E402

SCHEMA = json.loads(
    (REPO_ROOT / "schemas" / "awiki-review" / "v1.schema.json").read_text(
        encoding="utf-8"))


def _bus(tmp_path, **kw):
    return rb.ReviewBus(tmp_path / "review-bus", phase=kw.pop("phase", "P8"))


def _publish(bus, sha="a1b2c3d", **kw):
    return bus.publish(head_sha=sha, executor="glm-executor",
                       required_tests=["python -m pytest tests/ -q"], **kw)


# ── engine primitives ─────────────────────────────────────────────────
def test_publish_creates_schema_valid_cycle(tmp_path):
    bus = _bus(tmp_path)
    doc = _publish(bus)
    jsonschema_validate(doc)
    assert doc["status"] == "REVIEW_REQUESTED"
    assert (bus.dir / "P8-c1.json").is_file()


def test_jsonschema_available():
    import jsonschema  # noqa: F401 — CI authority per R-P3-002


def jsonschema_validate(doc):
    import jsonschema
    jsonschema.validate(doc, SCHEMA)


def test_finding_ids_are_stable_and_sequential(tmp_path):
    bus = _bus(tmp_path)
    _publish(bus)
    f1 = bus.add_finding(severity="blocker", area="engine",
                         summary="logic error in window calc")
    f2 = bus.add_finding(severity="note", area="docs", summary="typo")
    assert f1["id"] == "R-P8-001" and f2["id"] == "R-P8-002"
    assert re.fullmatch(r"R-[A-Za-z0-9-]+-\d{3}", f1["id"])


# ── §16 acceptance criteria ───────────────────────────────────────────
def test_executor_publishes_without_human_copy_paste(tmp_path):
    """§16-1: publish is an API call, output is durable state on disk."""
    bus = _bus(tmp_path)
    doc = _publish(bus)
    reloaded = rb.ReviewBus(tmp_path / "review-bus", phase="P8").load("P8-c1")
    assert reloaded == doc  # round-trips through disk


def test_review_targets_exact_head_sha(tmp_path):
    """§16-2: the cycle is attributable to exactly one HEAD SHA."""
    bus = _bus(tmp_path)
    doc = _publish(bus, sha="deadbee")
    assert doc["head_sha"] == "deadbee"


def test_executor_ingests_findings_automatically(tmp_path):
    """§16-4: findings live in the same durable doc the executor reads."""
    bus = _bus(tmp_path)
    _publish(bus)
    bus.add_finding(severity="major", area="hooks", summary="race in sweep")
    assert bus.load("P8-c1")["findings"][0]["summary"] == "race in sweep"


def test_fixes_map_back_to_finding_ids(tmp_path):
    """§16-5: resolving records the finding id; verified state closes it."""
    bus = _bus(tmp_path)
    _publish(bus)
    f = bus.add_finding(severity="blocker", area="engine", summary="off-by-one")
    bus.resolve_finding(f["id"], fix_sha="f00dcafe")
    bus.verify_finding(f["id"])
    stored = [x for x in bus.load("P8-c1")["findings"] if x["id"] == f["id"]][0]
    assert stored["state"] == "verified"


def test_tests_rerun_recorded_after_fixes(tmp_path):
    """§16-6: retest result + sha recorded on the cycle."""
    bus = _bus(tmp_path)
    _publish(bus, sha="a1b2c3d")
    bus.record_retest(sha="a1b2c3d", ok=True)
    doc = bus.load("P8-c1")
    assert doc["retest"]["ok"] is True and doc["retest"]["sha"] == "a1b2c3d"


def test_new_sha_invalidates_old_approval(tmp_path):
    """§16-7: approval at old SHA collapses when a new SHA is retested."""
    bus = _bus(tmp_path)
    _publish(bus, sha="a1b2c3d")
    bus.add_finding(severity="blocker", area="e", summary="s")
    bus.resolve_finding("R-P8-001", fix_sha="f00dcafe")
    bus.verify_finding("R-P8-001")
    bus.set_verdict(reviewer="reviewer-adapter", verdict="PASS_WITH_NOTES")
    assert bus.load("P8-c1")["status"] == "APPROVED"
    # fix landed as a NEW head — retest at the new sha must invalidate
    bus.record_retest(sha="f00dcafe", ok=True)
    doc = bus.load("P8-c1")
    assert doc["status"] != "APPROVED", "stale approval must be invalidated"


def test_ci_status_included_in_readiness(tmp_path):
    """§16-8/9: readiness folds CI + unresolved blockers."""
    bus = _bus(tmp_path)
    _publish(bus)
    bus.set_verdict(reviewer="r", verdict="PASS")
    bus.record_retest(sha="a1b2c3d", ok=True)
    bus.record_ci(ok=False)
    r = bus.readiness("P8-c1")
    assert r["ready"] is False and any("ci" in x for x in r["reasons"])


def test_unresolved_blocker_prevents_ready(tmp_path):
    bus = _bus(tmp_path)
    _publish(bus)
    bus.add_finding(severity="blocker", area="e", summary="s")  # left open
    with pytest.raises(rb.ReviewBusError):
        bus.set_verdict(reviewer="r", verdict="PASS")  # schema refuses
    bus.record_retest(sha="a1b2c3d", ok=True)
    bus.record_ci(ok=True)
    r = bus.readiness("P8-c1")
    assert r["ready"] is False


def test_ready_requires_everything_aligned(tmp_path):
    bus = _bus(tmp_path)
    _publish(bus, sha="a1b2c3d")
    bus.add_finding(severity="note", area="docs", summary="t")
    bus.verify_finding("R-P8-001")
    bus.set_verdict(reviewer="reviewer-adapter", verdict="PASS_WITH_NOTES")
    bus.record_retest(sha="a1b2c3d", ok=True)
    bus.record_ci(ok=True)
    r = bus.readiness("P8-c1")
    assert r["ready"] is True, r["reasons"]
    assert bus.load("P8-c1")["status"] == "READY"
    jsonschema_validate(bus.load("P8-c1"))


def test_state_survives_process_restart(tmp_path):
    """§16-11: state is disk JSON; a fresh instance sees everything."""
    _bus(tmp_path)  # first instance scope
    bus = _bus(tmp_path)
    _publish(bus)
    bus.add_finding(severity="minor", area="x", summary="y")
    fresh = rb.ReviewBus(tmp_path / "review-bus", phase="P8")
    assert len(fresh.load("P8-c1")["findings"]) == 1


def test_reviewer_implementation_swappable(tmp_path):
    """§16-12: reviewer is data (name/transport), not a wired dependency."""
    bus = _bus(tmp_path)
    _publish(bus, reviewer="gpt-ultra", transport="github")
    doc = bus.load("P8-c1")
    assert doc["reviewer"] == "gpt-ultra" and doc["transport"] == "github"


def test_engine_has_no_git_machinery():
    """§16-10 + repo rule: no automatic merge — the engine never merges."""
    src = (REPO_ROOT / "scripts" / "lib" / "review_bus.py").read_text(
        encoding="utf-8")
    assert "git merge" not in src and "git push" not in src
    assert "subprocess" not in src, "state engine must not shell out"


def test_every_written_state_validates_against_schema(tmp_path):
    """The schema is the contract — every transition must stay valid."""
    bus = _bus(tmp_path)
    _publish(bus)
    bus.add_finding(severity="major", area="a", summary="s")
    bus.resolve_finding("R-P8-001", fix_sha="ff001aa")
    bus.verify_finding("R-P8-001")
    bus.set_verdict(reviewer="r", verdict="PASS")
    bus.record_retest(sha="a1b2c3d", ok=True)
    bus.record_ci(ok=True)
    bus.readiness("P8-c1")
    jsonschema_validate(bus.load("P8-c1"))


# ── Slice E1: loop budget + first-class halt reason ────────────────────
def test_budget_retries_exhausted_halts(tmp_path):
    """A loop may not spin forever: exceeding max_retries records a
    halt_reason and readiness refuses until a human resets it."""
    bus = _bus(tmp_path)
    _publish(bus, sha="a1b2c3d")
    for i in range(3):
        bus.record_retest(sha="a1b2c3d", ok=False)
    doc = bus.load("P8-c1")
    assert doc["halt_reason"] == "retries-exceeded"
    bus.set_verdict(reviewer="r", verdict="PASS")
    r = bus.readiness()
    assert r["ready"] is False
    assert any("halt" in x for x in r["reasons"])
    # human reset clears the halt
    bus.clear_halt("P8-c1")
    assert bus.load("P8-c1").get("halt_reason") is None


def test_retries_within_budget_do_not_halt(tmp_path):
    bus = _bus(tmp_path)
    _publish(bus, sha="a1b2c3d")
    bus.record_retest(sha="a1b2c3d", ok=False)
    bus.record_retest(sha="a1b2c3d", ok=False)
    assert bus.load("P8-c1").get("halt_reason") is None


# ── Issue #54: addressed blockers remain blocking until verified ──────
def test_issue54_addressed_blocker_rejects_pass(tmp_path):
    """Issue #54 RED-1: a merely ADDRESSED blocker must reject PASS."""
    bus = _bus(tmp_path)
    _publish(bus)
    bus.add_finding(severity="blocker", area="e", summary="s")
    bus.resolve_finding("R-P8-001", fix_sha="f00dcafe")  # addressed, NOT verified
    with pytest.raises(rb.ReviewBusError):
        bus.set_verdict(reviewer="r", verdict="PASS")


def test_issue54_addressed_blocker_keeps_readiness_false(tmp_path):
    """Issue #54 RED-2: end-to-end — an addressed blocker must reject the
    PASS verdict AND keep readiness FALSE even with current-head retest +
    green CI. (On the unfixed bus, set_verdict(PASS) SUCCEEDS here and
    readiness flips READY — the exact hole Issue #54 names.)"""
    bus = _bus(tmp_path)
    _publish(bus)
    bus.add_finding(severity="blocker", area="e", summary="s")
    bus.resolve_finding("R-P8-001", fix_sha="f00dcafe")
    with pytest.raises(rb.ReviewBusError):
        bus.set_verdict(reviewer="r", verdict="PASS")
    bus.record_retest(sha="a1b2c3d", ok=True)
    bus.record_ci(ok=True)
    r = bus.readiness("P8-c1")
    assert r["ready"] is False, r
    assert any("blocker" in x for x in r["reasons"]), r["reasons"]


def test_issue54_addressed_blocker_blocks_even_with_fresh_evidence(tmp_path):
    """Issue #54 RED-3: retest+CI evidence at the CURRENT head does NOT
    release an addressed-but-unverified blocker."""
    bus = _bus(tmp_path)
    _publish(bus, sha="f00dcafe")
    bus.add_finding(severity="blocker", area="e", summary="s")
    bus.resolve_finding("R-P8-001", fix_sha="f00dcafe")
    # head moves to the fix sha and ALL evidence is re-earned there
    bus.record_retest(sha="f00dcafe", ok=True)
    bus.record_ci(ok=True)
    with pytest.raises(rb.ReviewBusError):
        bus.set_verdict(reviewer="r", verdict="PASS_WITH_NOTES")
    r = bus.readiness("P8-c1")
    assert r["ready"] is False and any("blocker" in x for x in r["reasons"])


def test_issue54_verified_blocker_permits_pass(tmp_path):
    """Issue #54 RED-4: verified blocker permits PASS when gates pass."""
    bus = _bus(tmp_path)
    _publish(bus)
    bus.add_finding(severity="blocker", area="e", summary="s")
    bus.resolve_finding("R-P8-001", fix_sha="f00dcafe")
    bus.verify_finding("R-P8-001")
    doc = bus.set_verdict(reviewer="r", verdict="PASS")
    assert doc["status"] == "APPROVED"


def test_issue54_verified_blocker_permits_ready(tmp_path):
    """Issue #54 RED-5: verified blocker permits READY when all gates pass."""
    bus = _bus(tmp_path)
    _publish(bus)
    bus.add_finding(severity="blocker", area="e", summary="s")
    bus.resolve_finding("R-P8-001", fix_sha="f00dcafe")
    bus.verify_finding("R-P8-001")
    bus.set_verdict(reviewer="r", verdict="PASS")
    bus.record_retest(sha="a1b2c3d", ok=True)
    bus.record_ci(ok=True)
    r = bus.readiness("P8-c1")
    assert r["ready"] is True, r["reasons"]


def test_issue54_open_blocker_still_blocks(tmp_path):
    """Issue #54 RED-6: existing open-blocker behavior unchanged."""
    bus = _bus(tmp_path)
    _publish(bus)
    bus.add_finding(severity="blocker", area="e", summary="s")
    with pytest.raises(rb.ReviewBusError):
        bus.set_verdict(reviewer="r", verdict="PASS")
    assert bus.readiness("P8-c1")["ready"] is False


def test_issue54_addressed_note_does_not_block(tmp_path):
    """Issue #54 RED-7: notes/non-blocking findings stay non-blocking
    whether open, addressed or verified."""
    bus = _bus(tmp_path)
    _publish(bus)
    bus.add_finding(severity="note", area="docs", summary="t")
    bus.resolve_finding("R-P8-001", fix_sha="f00dcafe")  # addressed note
    bus.set_verdict(reviewer="r", verdict="PASS")
    bus.record_retest(sha="a1b2c3d", ok=True)
    bus.record_ci(ok=True)
    assert bus.readiness("P8-c1")["ready"] is True


def test_issue54_reload_preserves_addressed_blocking(tmp_path):
    """Issue #54 RED-8: restart/reload (fresh instance, same disk) keeps
    the addressed-blocker semantics."""
    bus = _bus(tmp_path)
    _publish(bus)
    bus.add_finding(severity="blocker", area="e", summary="s")
    bus.resolve_finding("R-P8-001", fix_sha="f00dcafe")
    bus.record_retest(sha="a1b2c3d", ok=True)
    bus.record_ci(ok=True)
    reloaded = rb.ReviewBus(tmp_path / "review-bus", phase="P8")
    with pytest.raises(rb.ReviewBusError):
        reloaded.set_verdict(reviewer="r", verdict="PASS")
    assert reloaded.readiness("P8-c1")["ready"] is False
    reloaded.verify_finding("R-P8-001")
    reloaded.set_verdict(reviewer="r", verdict="PASS")
    assert reloaded.readiness("P8-c1")["ready"] is True


def test_issue54_h1_to_h2_rollover_preserves_addressed_state(tmp_path):
    """Issue #54 RED-9: Issue #53 H1→H2 rollover unchanged — a new head
    clears verdict/CI but findings + addressed state survive and STILL
    block until verified."""
    bus = _bus(tmp_path)
    _publish(bus, sha="a1b2c3d")
    bus.add_finding(severity="blocker", area="e", summary="s")
    bus.resolve_finding("R-P8-001", fix_sha="f00dcafe")
    bus.verify_finding("R-P8-001")
    bus.set_verdict(reviewer="r", verdict="PASS")
    assert bus.load("P8-c1")["status"] == "APPROVED"
    # H2: head moves — ALL acceptance evidence collapses...
    doc = bus.record_retest(sha="f00dcafe", ok=True)
    assert doc["status"] == "REVIEW_REQUESTED"
    assert "verdict" not in doc and "ci" not in doc
    # ...but finding STATE survives (still verified — not reset)
    assert bus.load("P8-c1")["findings"][0]["state"] == "verified"
    # ...and an ADDRESSED (unverified) blocker survives rollover blocking
    bus2 = _bus(tmp_path)
    _publish(bus2, sha="1111222")
    bus2.add_finding(severity="blocker", area="e", summary="s2")
    bus2.resolve_finding("R-P8-001", fix_sha="f00dcafe")
    bus2.set_verdict(reviewer="r", verdict="BLOCK")
    bus2.record_retest(sha="f00dcafe", ok=True)  # H1 -> H2 rollover
    with pytest.raises(rb.ReviewBusError):
        bus2.set_verdict(reviewer="r", verdict="PASS")
