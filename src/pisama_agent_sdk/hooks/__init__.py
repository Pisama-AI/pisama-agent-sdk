"""Hook implementations for Claude Agent SDK integration."""

from typing import TYPE_CHECKING, Any, Optional, cast

if TYPE_CHECKING:
    from ..bridge import DetectionBridge

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


def create_claude_hooks(
    *,
    bridge: Optional["DetectionBridge"] = None,
    tool_matcher: Optional[HookMatcher] = None,
    sdk_matcher: Optional[str] = None,
    timeout: Optional[float] = 60.0,
    fail_open: bool = True,
    auto_heal: Optional[bool] = None,
    inject_recovery: bool = True,
) -> dict[str, list[Any]]:
    """Build a hooks mapping accepted by ``ClaudeAgentOptions``.

    The Pisama ``HookMatcher`` filters calls inside the detector bridge.
    ``sdk_matcher`` is the Claude Agent SDK matcher expression used before
    the callback is invoked. Keeping the two explicit avoids confusing the
    similarly named matcher types from each package.

    Install the optional integration first:
    ``pip install "pisama-agent-sdk[claude]"``.
    """
    try:
        from claude_agent_sdk import HookMatcher as ClaudeHookMatcher
    except ImportError as exc:
        raise ImportError(
            "Claude Agent SDK integration requires: "
            'pip install "pisama-agent-sdk[claude]"'
        ) from exc

    pre_hook = PreToolUseHook(
        bridge=bridge,
        fail_open=fail_open,
        auto_heal=auto_heal,
        matcher=tool_matcher,
    )
    post_hook = PostToolUseHook(
        bridge=bridge or pre_hook.bridge,
        inject_recovery=inject_recovery,
    )
    return {
        "PreToolUse": [
            ClaudeHookMatcher(
                matcher=sdk_matcher,
                hooks=[cast(Any, pre_hook)],
                timeout=timeout,
            )
        ],
        "PostToolUse": [
            ClaudeHookMatcher(
                matcher=sdk_matcher,
                hooks=[cast(Any, post_hook)],
                timeout=timeout,
            )
        ],
    }


__all__ = [
    # Hook functions
    "pre_tool_use_hook",
    "post_tool_use_hook",
    # Hook classes
    "PreToolUseHook",
    "PostToolUseHook",
    "create_claude_hooks",
    # Matchers
    "HookMatcher",
    "ALL_TOOLS",
    "FILE_TOOLS",
    "SHELL_TOOLS",
    "DANGEROUS_COMMANDS",
    "AGENT_TOOLS",
]
