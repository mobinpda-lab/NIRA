from datetime import datetime, timezone

import pytest

from factory.contracts.schema import ProjectContract, TaskState, Evidence, ObservationState
from factory.gates.engine import Gate, GateResult, artifact_gate, evaluate, exact_head_gate
from factory.recovery.policy import RecoveryPolicy
from factory.runtime.state_machine import Lease, LeaseDecision, expiry_from, transition, validate_lease
from factory.runtime.global_reconcile import (
    GlobalReconciler,
    ReconcileDecision,
    ReconcileSnapshot,
)


def test_illegal_transition_is_fail_closed():
    with pytest.raises(ValueError):
        transition(TaskState.READY, TaskState.PROMOTED)


def test_stale_or_wrong_worker_is_rejected():
    now = datetime.now(timezone.utc)
    lease = Lease("l1", "t1", "w1", 7, now, expiry_from(now))
    assert validate_lease(lease, "w2", 7, now) == LeaseDecision.REJECT_OWNER
    assert validate_lease(lease, "w1", 8, now) == LeaseDecision.REJECT_FENCED


def test_expired_lease_is_rejected():
    now = datetime.now(timezone.utc)
    lease = Lease("l1", "t1", "w1", 7, now, now)
    assert validate_lease(lease, "w1", 7, now) == LeaseDecision.REJECT_EXPIRED


def test_gate_engine_never_promotes_on_missing_evidence():
    decision = evaluate([Gate("ci", lambda _: False)], object())
    assert decision.result == GateResult.BLOCKED
    assert decision.failed_gates == ("ci",)


def test_exact_head_and_artifact_are_explicit():
    assert exact_head_gate("a" * 40, "a" * 40)
    assert not exact_head_gate("a" * 40, "b" * 40)
    assert artifact_gate("tests", [{"name": "tests", "expired": False}])
    assert not artifact_gate("tests", [{"name": "tests", "expired": True}])


def test_evidence_requires_identity_and_confidence():
    evidence = Evidence("e1", "org/repo", "p", "t", 1, "a" * 40, "b" * 40, None, None, "ci")
    with pytest.raises(ValueError):
        evidence.validate()


def test_recovery_is_bounded():
    policy = RecoveryPolicy()
    assert policy.decision(0, True) == "REQUEUE"
    assert policy.decision(2, True) == "REQUEUE"
    assert policy.decision(3, True) == "ESCALATE"
    assert policy.decision(1, False) == "ESCALATE"


def test_stale_lease_without_execution_evidence_requires_recovery():
    snapshot = ReconcileSnapshot(
        main_sha="a" * 40,
        active_leases=1,
        stale_leases=1,
        worker_execution_evidence=False,
    )
    result = GlobalReconciler().reconcile(snapshot)
    assert result.decision == ReconcileDecision.RECOVER
