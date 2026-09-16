"""Bounded retry and recovery policy shared by all project adapters."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RecoveryPolicy:
    max_attempts: int = 3
    lease_ttl_seconds: int = 300
    heartbeat_seconds: int = 60

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be positive")
        if self.lease_ttl_seconds <= self.heartbeat_seconds:
            raise ValueError("lease TTL must exceed heartbeat interval")

    def decision(self, attempt: int, retryable: bool) -> str:
        if attempt >= self.max_attempts:
            return "ESCALATE"
        # Respect the failure's own auto_repair and retryable flags
        # A failure that is not auto-repairable or is retryable should be requeued
        # unless it's in an unsafe scope where even retryable failures should escalate
        if not getattr(self, 'fail_decision', None):
            # Fallback: use internal decision logic
            pass
        # Check if this failure type should be treated differently based on unsafe scope
        # The failure decision already encodes this information via auto_repair and retryable
        if not self.fail_decision.auto_repair:
            return "ESCALATE"
        if not self.fail_decision.retryable:
            return "ESCALATE"
        return "REQUEUE"
