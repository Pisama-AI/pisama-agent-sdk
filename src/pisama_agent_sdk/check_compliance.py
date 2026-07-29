"""Specification-compliance check (beta, feature-flagged). Thin forwarder.

The real implementation lives in :mod:`pisama.agents.check_compliance`.
Usage is unchanged; see that module's docstring for the full contract
(``PISAMA_ENABLE_CHECK_COMPLIANCE`` gating, request/response shape).
"""

from pisama.agents.check_compliance import (
    BehavioralRule,
    ComplianceResult,
    PisamaFeatureNotEnabledError,
    Violation,
    check_compliance,
)

__all__ = [
    "PisamaFeatureNotEnabledError",
    "BehavioralRule",
    "Violation",
    "ComplianceResult",
    "check_compliance",
]
