"""Hook implementations for Claude Agent SDK integration.

Thin forwarder; every name below comes from a sibling module that
itself forwards to the equivalent :mod:`pisama.agents.hooks` path.
"""

from .matchers import (
    AGENT_TOOLS,
    ALL_TOOLS,
    DANGEROUS_COMMANDS,
    FILE_TOOLS,
    SHELL_TOOLS,
    HookMatcher,
)
from .post_tool_use import PostToolUseHook, post_tool_use_hook
from .pre_tool_use import PreToolUseHook, pre_tool_use_hook

__all__ = [
    # Hook functions
    "pre_tool_use_hook",
    "post_tool_use_hook",
    # Hook classes
    "PreToolUseHook",
    "PostToolUseHook",
    # Matchers
    "HookMatcher",
    "ALL_TOOLS",
    "FILE_TOOLS",
    "SHELL_TOOLS",
    "DANGEROUS_COMMANDS",
    "AGENT_TOOLS",
]
