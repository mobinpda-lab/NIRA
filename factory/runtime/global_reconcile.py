"""Deterministic decision policy for NIRA Autonomous Global Reconcile.

The reconciler is deliberately side-effect free. GitHub state is collected by
an Actions workflow, reduced to :class:`ReconcileSnapshot`, and then evaluated
here. Queue wake-up, bounded recovery and escalation are performed by the
workflow only after an exact-main race check.

This module never dispatches a worker, writes ``main``, merges a pull request,
or bypasses a human/security gate.
"""
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
    """Choose the next safe action from a reconstructable GitHub snapshot."""

    def reconcile(self, state: ReconcileSnapshot) -> ReconcileResult:
        if not state.main_sha:
            return ReconcileResult(
                ReconcileDecision.WAIT,
                "snapshot is missing exact main SHA",
            )

        if state.security_holds or state.human_holds:
            return ReconcileResult(
                ReconcileDecision.WAIT,
                "human/security gate required",
            )

        if self._has_active_execution(state):
            return ReconcileResult(
                ReconcileDecision.WAIT,
                "existing canonical execution is active",
            )

        # Product work outranks release blockers, bounded recovery and finally
        # factory improvement. Related open PRs are filtered by the collector
        # per issue; an unrelated PR must not stall the entire factory.
        if state.product_tasks:
            return ReconcileResult(
                ReconcileDecision.CONTINUE,
                "product work available",
                WorkCategory.PRODUCT,
                min(state.product_tasks),
            )

        if state.release_blockers:
            return ReconcileResult(
                ReconcileDecision.CONTINUE,
                "release blocker remediation available",
                WorkCategory.RELEASE_BLOCKER,
                min(state.release_blockers),
            )

        if state.retryable_failures and state.recovery_issue is not None:
            if state.recovery_attempts >= state.recovery_budget:
                return ReconcileResult(
                    ReconcileDecision.WAIT,
                    "bounded recovery budget exhausted; human escalation required",
                    WorkCategory.RECOVERY,
                    state.recovery_issue,
                    escalate=True,
                )
            return ReconcileResult(
                ReconcileDecision.RECOVER,
                "bounded recovery required",
                WorkCategory.RECOVERY,
                state.recovery_issue,
            )

        if state.factory_improvements:
            return ReconcileResult(
                ReconcileDecision.CONTINUE,
                "factory improvement available after higher priorities are clear",
                WorkCategory.FACTORY_IMPROVEMENT,
                min(state.factory_improvements),
            )

        return ReconcileResult(
            ReconcileDecision.WAIT,
            "no safe action available",
        )

    @staticmethod
    def _has_active_execution(state: ReconcileSnapshot) -> bool:
        return any(
            value > 0
            for value in (
                state.active_workers,
                state.active_leases,
                state.active_canonical_runs,
            )
        )


def snapshot_from_dict(raw: dict[str, Any]) -> ReconcileSnapshot:
    """Normalize workflow JSON into an immutable policy input."""

    tuple_fields = {
        "product_tasks",
        "release_blockers",
        "factory_improvements",
        "retryable_failures",
        "security_holds",
        "human_holds",
    }
    normalized = dict(raw)
    for name in tuple_fields:
        normalized[name] = tuple(normalized.get(name) or ())
    return ReconcileSnapshot(**normalized)


def result_dict(result: ReconcileResult) -> dict[str, Any]:
    data = asdict(result)
    data["decision"] = result.decision.value
    data["category"] = result.category.value
    return data


def main(argv: list[str] | None = None) -> int:
    """CLI used by the GitHub workflow; reads snapshot JSON and prints decision."""

    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) > 1:
        raise SystemExit("usage: python -m factory.runtime.global_reconcile [snapshot.json]")
    if args:
        raw = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    else:
        raw = json.load(sys.stdin)
    result = GlobalReconciler().reconcile(snapshot_from_dict(raw))
    json.dump(result_dict(result), sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
