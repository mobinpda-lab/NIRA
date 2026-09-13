import json
from pathlib import Path

from factory.runtime.global_reconcile import (
    GlobalReconciler,
    ReconcileDecision,
    ReconcileSnapshot,
    WorkCategory,
)


ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def read_json(path: str):
    return json.loads(read(path))


def test_waits_when_exact_main_is_missing_or_execution_is_active():
    reconciler = GlobalReconciler()
    assert reconciler.reconcile(ReconcileSnapshot(main_sha="")).decision is ReconcileDecision.WAIT
    for kwargs in (
        {"active_workers": 1},
        {"active_leases": 1},
        {"active_canonical_runs": 1},
    ):
        result = reconciler.reconcile(ReconcileSnapshot(main_sha="abc", **kwargs))
        assert result.decision is ReconcileDecision.WAIT


def test_unrelated_open_prs_do_not_stall_selected_safe_work():
    result = GlobalReconciler().reconcile(
        ReconcileSnapshot(main_sha="abc", open_candidate_prs=3, product_tasks=(40,))
    )
    assert result.decision is ReconcileDecision.CONTINUE
    assert result.issue_number == 40


def test_human_and_security_holds_fail_closed():
    reconciler = GlobalReconciler()
    security = reconciler.reconcile(
        ReconcileSnapshot(main_sha="abc", product_tasks=(10,), security_holds=("#10",))
    )
    human = reconciler.reconcile(
        ReconcileSnapshot(main_sha="abc", product_tasks=(10,), human_holds=("#11",))
    )
    assert security.decision is ReconcileDecision.WAIT
    assert human.decision is ReconcileDecision.WAIT


def test_priority_is_product_then_release_blocker_then_recovery_then_factory():
    reconciler = GlobalReconciler()
    base = dict(
        main_sha="abc",
        product_tasks=(40,),
        release_blockers=(30,),
        retryable_failures=("issue-20:provider-pressure",),
        recovery_issue=20,
        factory_improvements=(10,),
    )
    product = reconciler.reconcile(ReconcileSnapshot(**base))
    assert product.decision is ReconcileDecision.CONTINUE
    assert product.category is WorkCategory.PRODUCT
    assert product.issue_number == 40

    base["product_tasks"] = ()
    release = reconciler.reconcile(ReconcileSnapshot(**base))
    assert release.category is WorkCategory.RELEASE_BLOCKER
    assert release.issue_number == 30

    base["release_blockers"] = ()
    recovery = reconciler.reconcile(ReconcileSnapshot(**base))
    assert recovery.decision is ReconcileDecision.RECOVER
    assert recovery.category is WorkCategory.RECOVERY
    assert recovery.issue_number == 20

    base["retryable_failures"] = ()
    base["recovery_issue"] = None
    factory = reconciler.reconcile(ReconcileSnapshot(**base))
    assert factory.category is WorkCategory.FACTORY_IMPROVEMENT
    assert factory.issue_number == 10


def test_recovery_budget_exhaustion_escalates_instead_of_retry_loop():
    result = GlobalReconciler().reconcile(
        ReconcileSnapshot(
            main_sha="abc",
            retryable_failures=("issue-160:provider-pressure",),
            recovery_issue=160,
            recovery_attempts=2,
            recovery_budget=2,
        )
    )
    assert result.decision is ReconcileDecision.WAIT
    assert result.escalate is True
    assert result.category is WorkCategory.RECOVERY


def test_global_reconcile_workflow_is_five_minute_fail_closed_and_queue_only():
    workflow = read(".github/workflows/nira-global-reconcile.yml")
    assert "cron: '*/5 * * * *'" in workflow
    assert "contents: read" in workflow
    assert "contents: write" not in workflow
    assert "pull-requests: read" in workflow
    assert "actions: write" in workflow
    assert "nira-intake-queue.yml" in workflow
    assert "nira-queue-scheduler.yml" in workflow
    assert "nira-provider-capacity-probe.yml" in workflow
    assert "nira-cross-repo-worker.yml" not in workflow
    assert "currentRef.data.object.sha !== snapshot.main_sha" in workflow
    assert "related-pr-open" in workflow
    assert "race-active-canonical-run" in workflow
    assert "github.rest.pulls.merge" not in workflow


def test_global_reconcile_policy_registers_protected_controller():
    policy = read_json("factory/registry/autonomous-mutation-policy.json")
    controller = policy["global_reconcile_controller"]
    assert controller["workflow"] == ".github/workflows/nira-global-reconcile.yml"
    assert controller["cadence"] == "*/5 * * * *"
    assert controller["queue_is_single_dispatch_authority"] is True
    assert controller["may_dispatch_workers_directly"] is False
    assert controller["may_write_repository_contents"] is False
    assert controller["may_merge_pull_requests"] is False
    assert policy["safety"]["automatic_merge_enabled"] is False
    assert ".github/workflows/nira-global-reconcile.yml" in policy["protected_paths"]


def test_promotion_requires_human_merge_by_default():
    promotion = read_json("factory/registry/promotion-policy.json")["promotion"]
    orchestrator = read(".github/workflows/production-orchestrator.yml")
    assert promotion["automatic_merge_enabled"] is False
    assert "automatic_merge_enabled" in orchestrator
    assert 'if [[ "$auto_merge" != "true" ]]' in orchestrator
    assert "NIRA_PROMOTION=READY_FOR_HUMAN_MERGE" in orchestrator
    assert "AUTOMATIC_MERGE=false" in orchestrator
