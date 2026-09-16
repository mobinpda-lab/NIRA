from factory.feedback.failure_feedback import Failure, FailureFeedback


def failure(*, attempt: int = 0, retryable: bool = True, owner_lane: str = "BOUNDED_REPAIR") -> Failure:
    return Failure("task-1", attempt, "VALIDATION", retryable, "evidence-1", owner_lane)


def test_retryable_failure_enters_bounded_auto_fix():
    decision = FailureFeedback(max_auto_fix_attempts=2).decide(failure())
    assert decision.action == "AUTO_FIX"
    assert decision.reason == "BOUNDED_RETRYABLE_FAILURE"


def test_non_retryable_failure_escalates():
    decision = FailureFeedback().decide(failure(retryable=False))
    assert decision.action == "ESCALATE"
    assert decision.reason == "NON_RETRYABLE"


def test_budget_exhaustion_escalates():
    decision = FailureFeedback(max_auto_fix_attempts=2).decide(failure(attempt=2))
    assert decision.action == "ESCALATE"
    assert decision.reason == "AUTO_FIX_BUDGET_EXHAUSTED"


def test_duplicate_failure_is_suppressed():
    feedback = FailureFeedback()
    first = feedback.decide(failure())
    second = feedback.decide(failure())
    assert first.action == "AUTO_FIX"
    assert second.action == "SUPPRESS"
    assert second.reason == "DUPLICATE_FAILURE"


def test_unsafe_scope_escalates_immediately():
    decision = FailureFeedback().decide(failure(owner_lane="ESCALATE"))
    assert decision.action == "ESCALATE"
    assert decision.reason == "UNSAFE_SCOPE"


def test_credential_failure_escalates_immediately():
    decision = FailureFeedback().decide(failure(owner_lane="CREDENTIAL_OR_AUTH"))
    assert decision.action == "ESCALATE"
    assert decision.reason == "UNSAFE_SCOPE"


def test_provider_cooldown_escalates_cooldown_handled():
    decision = FailureFeedback().decide(failure(owner_lane="PROVIDER_COOLDOWN"))
    assert decision.action == "ESCALATE"
    assert decision.reason == "COOLDOWN_HANDLED"


def test_environment_recovery_escalates_cooldown_handled():
    decision = FailureFeedback().decide(failure(owner_lane="ENVIRONMENT_RECOVERY"))
    assert decision.action == "ESCALATE"
    assert decision.reason == "COOLDOWN_HANDLED"


def test_revalidate_limited_budget():
    feedback = FailureFeedback()
    first = feedback.decide(failure(owner_lane="REVALIDATE", attempt=0))
    assert first.action == "AUTO_FIX"
    assert first.reason == "BOUNDED_REVALIDATE"
    second = feedback.decide(failure(owner_lane="REVALIDATE", attempt=1))
    assert second.action == "ESCALATE"
    assert second.reason == "REVALIDATE_BUDGET_EXHAUSTED"}]}<tool_call>SIGNAL:END_OF_RESPONSE:{
