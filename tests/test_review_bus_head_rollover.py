"""Q18 / A-Wiki Issue #53 — HEAD rollover invalidates ALL acceptance evidence.

RED-first matrix: on any real H1→H2 head change, record_retest must drop the
prior verdict (including CHANGES_REQUIRED), drop stale CI, reset to
REVIEW_REQUESTED, keep task/cycle/findings/retry state, and require fresh H2
evidence for READY. Same-HEAD retest must not destroy current evidence.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

import review_bus as rb  # noqa: E402


H1 = "a" * 40
H2 = "b" * 40


def _bus(tmp_path):
    return rb.ReviewBus(tmp_path / "review-bus", phase="P8")


def _publish(bus, sha=H1):
    return bus.publish(
        head_sha=sha, executor="glm-executor",
        required_tests=["python -m pytest tests/ -q"],
    )


def _cycle(bus):
    docs = sorted(bus.dir.glob("P8-c*.json"))
    return docs[-1].stem


# 1. CHANGES_REQUIRED@H1 -> H2 -> verdict invalidated
def test_q18_1_changes_required_rollover_drops_verdict(tmp_path):
    bus = _bus(tmp_path)
    _publish(bus, H1)
    bus.set_verdict(reviewer="r1", verdict="CHANGES_REQUIRED")
    bus.record_retest(sha=H2, ok=True)
    doc = bus.load(_cycle(bus))
    assert doc["head_sha"] == H2
    assert doc["status"] == "REVIEW_REQUESTED"
    assert "verdict" not in doc
    assert doc.get("next_action") == "FIX_AND_REREVIEW"


# 2. fresh PASS@H2 accepted after CHANGES rollover
def test_q18_2_fresh_pass_accepted_after_rollover(tmp_path):
    bus = _bus(tmp_path)
    _publish(bus, H1)
    bus.set_verdict(reviewer="r1", verdict="CHANGES_REQUIRED")
    bus.record_retest(sha=H2, ok=True)          # rollover clears verdict
    doc = bus.set_verdict(reviewer="r1", verdict="PASS")  # fresh PASS@H2
    assert doc["status"] == "APPROVED"


# 3. PASS+CI@H1 -> H2 -> no fresh CI => not READY
def test_q18_3_stale_ci_cannot_satisfy_new_head(tmp_path):
    bus = _bus(tmp_path)
    _publish(bus, H1)
    bus.set_verdict(reviewer="r1", verdict="PASS")
    bus.record_retest(sha=H1, ok=True)
    bus.record_ci(ok=True)                       # CI green at H1
    assert bus.readiness(_cycle(bus))["ready"] is True  # control

    bus.record_retest(sha=H2, ok=True)           # rollover
    bus.set_verdict(reviewer="r1", verdict="PASS")  # fresh PASS@H2
    result = bus.readiness(_cycle(bus))
    assert result["ready"] is False
    assert any("ci" in reason for reason in result["reasons"])


# 4. fresh CI@H2 => normal readiness may succeed
def test_q18_4_fresh_ci_restores_readiness(tmp_path):
    bus = _bus(tmp_path)
    _publish(bus, H1)
    bus.set_verdict(reviewer="r1", verdict="PASS")
    bus.record_retest(sha=H1, ok=True)
    bus.record_ci(ok=True)
    bus.record_retest(sha=H2, ok=True)
    bus.set_verdict(reviewer="r1", verdict="PASS")
    bus.record_ci(ok=True)                       # fresh CI at H2
    assert bus.readiness(_cycle(bus))["ready"] is True


# 5. findings survive rollover
def test_q18_5_findings_survive_rollover(tmp_path):
    bus = _bus(tmp_path)
    _publish(bus, H1)
    bus.add_finding(severity="blocker", area="core", summary="needs fix")
    bus.set_verdict(reviewer="r1", verdict="CHANGES_REQUIRED")
    findings = bus.load(_cycle(bus))["findings"]
    assert findings, "control: seeded findings exist"
    bus.record_retest(sha=H2, ok=True)
    after = bus.load(_cycle(bus))["findings"]
    assert [f["id"] for f in after] == [f["id"] for f in findings]


# 6. task/cycle identity stable (same cycle file, no new cycle)
def test_q18_6_task_cycle_identity_stable(tmp_path):
    bus = _bus(tmp_path)
    _publish(bus, H1)
    before = sorted(p.name for p in bus.dir.glob("P8-c*.json"))
    bus.record_retest(sha=H2, ok=True)
    after = sorted(p.name for p in bus.dir.glob("P8-c*.json"))
    assert before == after


# 7. retry/halt semantics unchanged
def test_q18_7_retry_halt_semantics_unchanged(tmp_path):
    bus = _bus(tmp_path)
    _publish(bus, H1)
    for _ in range(3):
        bus.record_retest(sha=H1, ok=False)     # same-HEAD failures count
    doc = bus.load(_cycle(bus))
    assert doc.get("halt_reason") == "retries-exceeded"
    assert doc["retries"] == 3


# 8. same-HEAD retest preserves current evidence
def test_q18_8_same_head_retest_preserves_evidence(tmp_path):
    bus = _bus(tmp_path)
    _publish(bus, H1)
    bus.set_verdict(reviewer="r1", verdict="PASS")
    bus.record_retest(sha=H1, ok=True)
    bus.record_ci(ok=True)
    bus.record_retest(sha=H1, ok=True)           # rerun at SAME head
    doc = bus.load(_cycle(bus))
    assert doc["status"] == "READY" or doc.get("verdict") == "PASS"
    assert doc["ci"]["ok"] is True               # CI not destroyed
    assert doc["head_sha"] == H1


# 9. reload/restart durable
def test_q18_9_reload_preserves_corrected_state(tmp_path):
    bus = _bus(tmp_path)
    _publish(bus, H1)
    bus.set_verdict(reviewer="r1", verdict="PASS")
    bus.record_ci(ok=True)
    bus.record_retest(sha=H2, ok=True)
    fresh = rb.ReviewBus(tmp_path / "review-bus", phase="P8")
    doc = fresh.load(_cycle(fresh))
    assert "verdict" not in doc and "ci" not in doc
    assert doc["status"] == "REVIEW_REQUESTED" and doc["head_sha"] == H2


# 10. BLOCK verdict also invalidated on rollover
def test_q18_10_block_verdict_rollover(tmp_path):
    bus = _bus(tmp_path)
    _publish(bus, H1)
    bus.set_verdict(reviewer="r1", verdict="BLOCK")
    bus.record_retest(sha=H2, ok=True)
    doc = bus.load(_cycle(bus))
    assert "verdict" not in doc and doc["status"] == "REVIEW_REQUESTED"


# 11. duplicate identical H2 result remains idempotent (bridge digest logic
#     depends on verdict-clear behavior; bus side keeps retest rebind stable)
def test_q18_11_double_rollover_rebind_stable(tmp_path):
    bus = _bus(tmp_path)
    _publish(bus, H1)
    bus.set_verdict(reviewer="r1", verdict="PASS")
    bus.record_retest(sha=H2, ok=True)
    bus.record_retest(sha=H2, ok=True)           # same H2 again: no further loss
    doc = bus.load(_cycle(bus))
    assert doc["head_sha"] == H2
    assert doc["retest"]["sha"] == H2 and doc["retest"]["ok"] is True


# 12. failing retest at rollover still counts a retry
def test_q18_12_failing_rollover_counts_retry(tmp_path):
    bus = _bus(tmp_path)
    _publish(bus, H1)
    bus.set_verdict(reviewer="r1", verdict="PASS")
    bus.record_retest(sha=H2, ok=False)
    doc = bus.load(_cycle(bus))
    assert doc["retries"] == 1
    assert doc["retest"]["ok"] is False
