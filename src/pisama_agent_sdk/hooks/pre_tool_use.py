"""PreToolUse hook implementation. Thin forwarder.

The real implementation lives in :mod:`pisama.agents.hooks.pre_tool_use`.
Usage is unchanged::

    from pisama_agent_sdk.hooks import pre_tool_use_hook

    # Register with Claude Agent SDK
    agent.hooks.pre_tool_use = pre_tool_use_hook
"""

from pisama.agents.hooks.pre_tool_use import PreToolUseHook, pre_tool_use_hook

__all__ = [
    "pre_tool_use_hook",
    "PreToolUseHook",
]
