"""PostToolUse hook implementation. Thin forwarder.

The real implementation lives in
:mod:`pisama.agents.hooks.post_tool_use`. Usage is unchanged::

    from pisama_agent_sdk.hooks import post_tool_use_hook

    # Register with Claude Agent SDK
    agent.hooks.post_tool_use = post_tool_use_hook
"""

from pisama.agents.hooks.post_tool_use import PostToolUseHook, post_tool_use_hook

__all__ = [
    "post_tool_use_hook",
    "PostToolUseHook",
]
