"""Deterministic failure intelligence for NIRA.

Classification is evidence-driven and provider-neutral. It decides routing only;
it never mutates repositories or grants promotion authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re


class FailureClass(str, Enum):
    CODE = "CODE"
    TEST_REGRESSION = "TEST_REGRESSION"
    DEPENDENCY = "DEPENDENCY"
    ENVIRONMENT = "ENVIRONMENT"
    PERMISSION = "PERMISSION"
    PROVIDER_PRESSURE = "PROVIDER_PRESSURE"
    FLAKY = "FLAKY"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class FailureDecision:
    category: FailureClass
    confidence: str
    auto_repair: bool
    owner_lane: str
    retryable: bool
    reason: str


_PATTERNS: tuple[tuple[FailureClass, tuple[str, ...]], ...] = (
    (FailureClass.PERMISSION, (
        r"permission denied", r"http 40[13]", r"forbidden", r"bad credentials",
        r"resource not accessible", r"missing.*secret", r"private key",
    )),
    (FailureClass.PROVIDER_PRESSURE, (
        r"http 429", r"rate limit", r"too many requests", r"http 50[234]",
        r"upstream unavailable", r"provider pressure",
    )),
    (FailureClass.DEPENDENCY, (
        r"dependency", r"lockfile", r"could not resolve", r"package .* not found",
        r"version solving failed", r"npm err", r"pub get",
    )),
    (FailureClass.ENVIRONMENT, (
        r"runner", r"android sdk", r"java_home", r"no space left", r"network is unreachable",
        r"temporary failure", r"service unavailable",
    )),
    (FailureClass.TEST_REGRESSION, (
        r"assertionerror", r"expected .* actual", r"tests? failed", r"test .* failure",
        r"golden.*mismatch", r"snapshot.*failed",
    )),
    (FailureClass.CODE, (
        r"syntaxerror", r"compile", r"undefined", r"unresolved reference",
        r"cannot find symbol", r"importerror", r"typeerror",
    )),
    (FailureClass.FLAKY, (
        r"flaky", r"intermittent", r"timed out", r"timeout",
    )),
)


def classify_failure(text: str, *, changed_files: tuple[str, ...] = (), repeated: bool = False) -> FailureDecision:
    normalized = (text or "").lower()
    matched = FailureClass.UNKNOWN
    for category, patterns in _PATTERNS:
        if any(re.search(pattern, normalized, re.IGNORECASE) for pattern in patterns):
            matched = category
            break

    # Determine if this failure falls under an unsafe scope (e.g., involves secrets, credentials, or protected control surfaces)
    unsafe_scope = any(
        p.startswith(".github/workflows/")
        or p == "factory/registry/promotion-policy.json"
        or re.search(r"(secret|credential|token)", p, re.IGNORECASE)
        for p in changed_files
    )

    if matched is FailureClass.PERMISSION:
        return FailureDecision(matched, "HIGH", False, "CREDENTIAL_OR_AUTH", False, "permission/auth failures require configuration evidence")
    if matched is FailureClass.PROVIDER_PRESSURE:
        return FailureDecision(matched, "HIGH", False, "PROVIDER_COOLDOWN", True, "provider pressure must not consume repair attempts")
    if matched is FailureClass.ENVIRONMENT:
        return FailureDecision(matched, "MEDIUM", False, "ENVIRONMENT_RECOVERY", True, "environment failures should not spend AI repair budget")
    if matched is FailureClass.DEPENDENCY:
        # Dependency failures can be repaired outside protected surfaces, but not inside them
        repair_allowed = not unsafe_scope
        owner_lane = "BOUNDED_REPAIR" if repair_allowed else "ESCALATE"
        return FailureDecision(matched, "MEDIUM", repair_allowed, owner_lane, True, "dependency repair allowed only outside protected control surfaces")
    if matched in {FailureClass.CODE, FailureClass.TEST_REGRESSION}:
        # Code and test regression failures can be repaired outside protected surfaces
        repair_allowed = not unsafe_scope
        owner_lane = "BOUNDED_REPAIR" if repair_allowed else "ESCALATE"
        return FailureDecision(matched, "MEDIUM", repair_allowed, owner_lane, True, "source/test failures may enter bounded repair")
    if matched is FailureClass.FLAKY:
        # Flaky failures should be revalidated before considering code repair
        return FailureDecision(matched, "LOW" if not repeated else "MEDIUM", False, "REVALIDATE", True, "flaky evidence should be revalidated before code repair")
    return FailureDecision(FailureClass.UNKNOWN, "NONE", False, "ESCALATE", False, "unknown failure fails closed")
