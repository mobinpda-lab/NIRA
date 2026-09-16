"""Minimal executable NIRA control-plane path.

The implementation is intentionally small and deterministic. It provides the
control-plane boundaries needed to exercise a client task without giving the
client adapter any queue, worker, or promotion authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256

from factory.adapters.arvin import ArvinClientAdapter
from factory.contracts.schema import Evidence, Task, TaskState
from factory.gates.engine import Gate, GateDecision, evaluate, exact_base_gate, exact_head_gate
from factory.recovery.policy import RecoveryPolicy
from factory.runtime.state_machine import Lease, expiry_from, transition


@dataclass(frozen=True)
class QueuedTask:
    task: Task
    enqueued_at: str


class NIRAQueue:
    """Idempotent FIFO queue owned by NIRA."""

    def __init__(self) -> None:
        self._items: dict[str, QueuedTask] = {}

    def enqueue(self, task: Task) -> QueuedTask:
        if task.idempotency_key in self._items:
            return self._items[task.idempotency_key]
        item = QueuedTask(task, datetime.now(timezone.utc).isoformat())
        self._items[task.idempotency_key] = item
        return item

    def next(self) -> QueuedTask:
        if not self._items:
            raise LookupError("NIRA queue is empty")
        return next(iter(self._items.values()))


class NIRAControlPlane:
    """Owns intake, queue, lease/fencing, worker handoff, gates and evidence."""

    def __init__(self, adapter: ArvinClientAdapter) -> None:
        adapter.validate()
        self.adapter = adapter
        self.queue = NIRAQueue()
        self.recovery = RecoveryPolicy()
        self._leases: dict[str, Lease] = {}
        self._evidence: dict[str, Evidence] = {}

    def intake(self, task: Task) -> QueuedTask:
        if task.project_id != self.adapter.project_id:
            raise ValueError("task project does not match registered client")
        if task.state != TaskState.READY:
            raise ValueError("intake accepts READY tasks only")
        return self.queue.enqueue(task)

    def lease(self, task: Task, worker_id: str, now: datetime | None = None) -> Lease:
        if task.idempotency_key not in self.queue._items:
            raise ValueError("task must be queued before lease")
        now = now or datetime.now(timezone.utc)
        lease_id = sha256(f"{task.task_id}:{worker_id}:{task.attempt}".encode()).hexdigest()[:16]
        lease = Lease(
            lease_id,
            task.task_id,
            worker_id,
            task.attempt + 1,
            now,
            expiry_from(now, self.recovery.lease_ttl_seconds),
        )
        self._leases[lease_id] = lease
        return lease

    def authorize_worker(
        self,
        task: Task,
        lease: Lease,
        worker_id: str,
        fence_token: int,
        now: datetime | None = None,
    ) -> TaskState:
        from factory.runtime.state_machine import validate_lease

        decision = validate_lease(lease, worker_id, fence_token, now)
        if decision.value != "ACCEPT":
            raise PermissionError(f"worker rejected by lease fencing: {decision.value}")
        return transition(task.state, TaskState.RUNNING)

    def gates(
        self,
        base_sha: str,
        observed_base: str,
        head_sha: str,
        observed_head: str,
        ci_passed: bool,
    ) -> GateDecision:
        return evaluate(
            [
                Gate("exact_base", lambda _: exact_base_gate(base_sha, observed_base)),
                Gate("exact_head", lambda _: exact_head_gate(head_sha, observed_head)),
                Gate("ci", lambda _: ci_passed),
            ],
            object(),
        )

    def record_evidence(self, evidence: Evidence) -> Evidence:
        """Persist independently collected evidence; workers cannot self-verify."""
        evidence.validate()
        if evidence.project_id != self.adapter.project_id:
            raise ValueError("evidence project does not match registered client")
        if evidence.repo != self.adapter.repository:
            raise ValueError("evidence repository does not match registered client")
        self._evidence[evidence.evidence_id] = evidence
        return evidence

    def promotion_gate(self, evidence_id: str) -> bool:
        """Return authorization only; NIRA promotion authority executes elsewhere."""
        evidence = self._evidence[evidence_id]
        return evidence.observation_state.value == "VERIFIED" and evidence.confidence != "NONE"

    def health_status(self) -> str:
        """
        Returns the health status of the NIRA control plane.
        
        Determined by:
        - Active lease existence (at least one lease is currently active)
        - Verified evidence presence (at least one evidence with VERIFIED state and non-NONE confidence)
        
        Returns:
        - "healthy": all conditions met
        - "degraded": missing one of the above conditions
        """
        now = datetime.now(timezone.utc)
        
        # Check for active lease
        has_active_lease = any(lease.active(now) for lease in self._leases.values())
        
        # Check for verified evidence
        has_verified_evidence = any(
            ev.observation_state.value == "VERIFIED" and ev.confidence != "NONE"
            for ev in self._evidence.values()
        )
        
        if has_active_lease and has_verified_evidence:
            return "healthy"
        else:
            return "degraded"
