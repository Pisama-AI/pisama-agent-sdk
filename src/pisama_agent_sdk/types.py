"""Type definitions for Claude Agent SDK integration. Thin forwarder.

The real definitions live in :mod:`pisama.agents.types`.
"""

from pisama.agents.types import (
    BridgeResult,
    HookContext,
    HookInput,
    HookJSONOutput,
    HookSpecificOutput,
    PermissionDecision,
)

__all__ = [
    "HookInput",
    "HookContext",
    "PermissionDecision",
    "HookSpecificOutput",
    "HookJSONOutput",
    "BridgeResult",
]
