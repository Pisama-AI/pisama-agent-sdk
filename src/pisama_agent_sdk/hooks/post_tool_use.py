"""PostToolUse hook implementation."""

import logging
from typing import TYPE_CHECKING, Any, Optional

from ..bridge import DetectionBridge, get_bridge
from ..types import HookContext, HookInput

if TYPE_CHECKING:
    from .matchers import HookMatcher

logger = logging.getLogger(__name__)


def _recovery_output(message: str) -> dict[str, Any]:
    """Send recovery context to the model and mirror it for the user."""
    return {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": message,
        },
        "systemMessage": message,
    }


async def post_tool_use_hook(
    input_data: HookInput,
    tool_use_id: Optional[str],
    context: HookContext,
) -> dict[str, Any]:
    """PostToolUse hook for failure capture and recovery.

    This hook is called after each tool execution and can:
    - Capture trace data for analysis
    - Inject recovery guidance into model context
    - Mirror recovery guidance to the user via systemMessage

    Args:
        input_data: Contains tool_name, tool_input, tool_response, session_id
        tool_use_id: Unique identifier for this tool invocation
        context: Hook context with signal

    Returns:
        Hook output dict with recovery message if needed

    Register this callback through ``create_claude_hooks()`` or directly in
    ``ClaudeAgentOptions.hooks``.
    """
    if not tool_use_id:
        logger.debug("PostToolUse called without tool_use_id, skipping")
        return {}

    bridge = get_bridge()

    try:
        result = await bridge.analyze_post_tool(input_data, tool_use_id)

        return (
            _recovery_output(result.system_message)
            if result.system_message
            else {}
        )

    except Exception as e:
        logger.error(f"PostToolUse hook error: {e}", exc_info=True)
        return {}


class PostToolUseHook:
    """Class-based PostToolUse hook with configuration.

    Use this when you need more control over the hook behavior,
    such as custom bridge configuration or disabling recovery messages.

    Example:
        from pisama_agent_sdk.hooks import PostToolUseHook
        from pisama_agent_sdk import DetectionBridge

        # Create hook with custom bridge
        hook = PostToolUseHook(bridge=my_bridge, inject_recovery=True)

        # Register through create_claude_hooks() or ClaudeAgentOptions.hooks.
    """

    def __init__(
        self,
        bridge: Optional[DetectionBridge] = None,
        inject_recovery: bool = True,
        matcher: Optional["HookMatcher"] = None,
    ) -> None:
        """Initialize the hook.

        Args:
            bridge: Custom detection bridge (defaults to global)
            inject_recovery: If True, inject recovery messages on issues
            matcher: Optional tool and input matcher. Unmatched calls pass
                through without running detection.
        """
        self.bridge = bridge or get_bridge()
        self.inject_recovery = inject_recovery
        self.matcher = matcher

    async def __call__(
        self,
        input_data: HookInput,
        tool_use_id: Optional[str],
        context: HookContext,
    ) -> dict[str, Any]:
        """Handle PostToolUse event.

        Args:
            input_data: Hook input data
            tool_use_id: Tool use identifier
            context: Hook context

        Returns:
            Hook output dict
        """
        if not tool_use_id:
            return {}
        if self.matcher and not self.matcher.matches(
            input_data.get("tool_name", ""),
            input_data.get("tool_input"),
        ):
            return {}

        try:
            result = await self.bridge.analyze_post_tool(input_data, tool_use_id)

            return (
                _recovery_output(result.system_message)
                if self.inject_recovery and result.system_message
                else {}
            )
        except Exception as e:
            logger.error(f"PostToolUse error: {e}")
            return {}
