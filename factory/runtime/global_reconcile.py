"""Deterministic decision policy for NIRA Autonomous Global Reconcile."""
from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class ReconcileDecision(str, Enum):
    WAIT = "WAIT"
    RECOVER = "RECOVER"
    CONTINUE = "CONTINUE"


class WorkCategory(str, Enum):
    PRODUCT = "PRODUCT"
    RELEASE_BLOCKER = "RELEASE_BLOCKER"
    RECOVERY = "RECOVERY"
    FACTORY_IMPROVEMENT = "FACTORY_IMPROVEMENT"
    NONE = "NONE"


@dataclass(frozen=True)
class ReconcileSnapshot:
    main_sha: str
    active_workers: int = 0
    active_leases: int = 0
    active_canonical_runs: int = 0
    worker_execution_started: bool = False
    worker_execution_evidence: bool = False
    stale_leases: bool = False
    open_candidate_prs: int = 0
    product_tasks: tuple[int, ...] = field(default_factory=tuple)
    release_blockers: tuple[int, ...] = field(default_factory=tuple)
    factory_improvements: tuple[int, ...] = field(default_factory=tuple)
    retryable_failures: tuple[str, ...] = field(default_factory=tuple)
    recovery_issue: int | None = None
    recovery_attempts: int = 0
    recovery_budget: int = 2
    security_holds: tuple[str, ...] = field(default_factory=tuple)
    human_holds: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ReconcileResult:
    decision: ReconcileDecision
    reason: str
    category: WorkCategory = WorkCategory.NONE
    issue_number: int | None = None
    escalate: bool = False


class GlobalReconciler:
    def reconcile(self, state: ReconcileSnapshot) -> ReconcileResult:
        if not state.main_sha:
            return ReconcileResult(ReconcileDecision.WAIT, "missing exact main SHA")

        if state.security_holds or state.human_holds:
            return ReconcileResult(ReconcileDecision.WAIT, "human/security gate required")

        if state.stale_leases and state.active_leases and not state.worker_execution_evidence:
            return ReconcileResult(
                ReconcileDecision.RECOVER,
                "stale lease without worker execution evidence",
                WorkCategory.RECOVERY,
                state.recovery_issue,
            )

        if self._has_active_execution(state):
            return ReconcileResult(ReconcileDecision.WAIT, "existing canonical execution is active")

        if state.product_tasks:
            return ReconcileResult(ReconcileDecision.CONTINUE, "product work available", WorkCategory.PRODUCT, min(state.product_tasks))

        if state.release_blockers:
            return ReconcileResult(ReconcileDecision.CONTINUE, "release blocker remediation available", WorkCategory.RELEASE_BLOCKER, min(state.release_blockers))

        if state.retryable_failures and state.recovery_issue is not None:
            if state.recovery_attempts >= state.recovery_budget:
                return ReconcileResult(ReconcileDecision.WAIT, "recovery budget exhausted", WorkCategory.RECOVERY, state.recovery_issue, True)
            return ReconcileResult(ReconcileDecision.RECOVER, "bounded recovery required", WorkCategory.RECOVERY, state.recovery_issue)

        if state.factory_improvements:
            return ReconcileResult(ReconcileDecision.CONTINUE, "factory improvement available", WorkCategory.FACTORY_IMPROVEMENT, min(state.factory_improvements))

        return ReconcileResult(ReconcileDecision.WAIT, "no safe action available")

    @staticmethod
    def _has_active_execution(state: ReconcileSnapshot) -> bool:
        return any((state.active_workers, state.active_leases, state.active_canonical_runs)) and (state.worker_execution_started or state.worker_execution_evidence)


def snapshot_from_dict(raw: dict[str, Any]) -> ReconcileSnapshot:
    normalized = dict(raw)
    for name in {"product_tasks", "release_blockers", "factory_improvements", "retryable_failures", "security_holds", "human_holds"}:
        normalized[name] = tuple(normalized.get(name) or ())
    return ReconcileSnapshot(**normalized)


def result_dict(result: ReconcileResult) -> dict[str, Any]:
    data = asdict(result)
    data["decision"] = result.decision.value
    data["category"] = result.category.value
    return data


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    raw = json.loads(Path(args[0]).read_text(encoding="utf-8")) if args else json.load(sys.stdin)
    json.dump(result_dict(GlobalReconciler().reconcile(snapshot_from_dict(raw))), sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
