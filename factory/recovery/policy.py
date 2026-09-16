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

    def decision(self, attempt: int, retryable: bool, *, category: str | None = None, owner_lane: str | None = None) -> str:
        if attempt >= self.max_attempts:
            return "ESCALATE"
        if not retryable:
            return "ESCALATE"
        # Unsafe scope and credential failures never retry
        if owner_lane in ("ESCALATE", "CREDENTIAL_OR_AUTH"):
            return "ESCALATE"
        # Provider pressure uses cooldown-based retry, not attempt budget
        if owner_lane == "PROVIDER_COOLDOWN":
            return "REQUEUE"
        # Environment recovery: bounded retry but not repair budget
        if owner_lane == "ENVIRONMENT_RECOVERY":
            return "REQUEUE"
        # Bounded repair and revalidation use attempt budget
        if owner_lane in ("BOUNDED_REPAIR", "REVALIDATE"):
            return "REQUEUE"
        # Default: retryable failures requeue within budget
        return "REQUEUE"
