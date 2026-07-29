"""ClarificationPrimitive — pause, ask, resume. Thin forwarder.

The real implementation lives in :mod:`pisama.agents.clarification`. See
that module's docstring for the full pause/ask/resume design rationale.
"""

from pisama.agents.clarification import (
    AnswerProvider,
    AnswerProviderValue,
    AnswerResult,
    ClarificationPrimitive,
    ClarificationRequest,
    Resolution,
    build_entity_confusion_request,
    register_clarification_builder,
)

__all__ = [
    "ClarificationRequest",
    "Resolution",
    "AnswerResult",
    "AnswerProviderValue",
    "AnswerProvider",
    "build_entity_confusion_request",
    "ClarificationPrimitive",
    "register_clarification_builder",
]
