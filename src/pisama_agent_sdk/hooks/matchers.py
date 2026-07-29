"""Tool matching patterns for hook filtering. Thin forwarder.

The real implementation lives in :mod:`pisama.agents.hooks.matchers`.
"""

from pisama.agents.hooks.matchers import (
    AGENT_TOOLS,
    ALL_TOOLS,
    DANGEROUS_COMMANDS,
    FILE_TOOLS,
    SHELL_TOOLS,
    HookMatcher,
    create_matcher,
)

__all__ = [
    "HookMatcher",
    "ALL_TOOLS",
    "FILE_TOOLS",
    "SHELL_TOOLS",
    "DANGEROUS_COMMANDS",
    "AGENT_TOOLS",
    "create_matcher",
]
