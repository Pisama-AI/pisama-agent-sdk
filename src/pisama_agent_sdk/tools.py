"""Self-check tool adapters.

``create_check_tool`` returns a framework-neutral descriptor.
``create_claude_check_tool`` and ``create_claude_check_server`` return the
native objects expected by the current Claude Agent SDK.

Usage with Claude Agent SDK:
    from claude_agent_sdk import ClaudeAgentOptions
    from pisama_agent_sdk import create_claude_check_server

    server = create_claude_check_server()
    options = ClaudeAgentOptions(
        mcp_servers={"pisama": server},
        allowed_tools=["mcp__pisama__pisama_check"],
    )
"""

import json
import logging
from typing import Any, Dict, Optional

from .check import check

logger = logging.getLogger(__name__)

# Tool definition for Claude Agent SDK
PISAMA_CHECK_TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "output": {
            "type": "string",
            "description": "The output text you want to verify for issues",
        },
        "context": {
            "type": "object",
            "description": "Context about the task: query, sources, task description",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The original query or question being answered",
                },
                "sources": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Source documents the output should be grounded in",
                },
                "task": {
                    "type": "string",
                    "description": "The task description or specification",
                },
            },
        },
        "detectors": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Specific detectors to run (optional). Available: hallucination, derailment, specification, completion, corruption, persona_drift",
        },
    },
    "required": ["output"],
}

PISAMA_CHECK_DESCRIPTION = (
    "Check your output for potential issues before returning it to the user. "
    "Use this when you're uncertain about accuracy, when making claims "
    "based on retrieved data, or when the task is high-stakes. "
    "Returns a confidence score (0-1, higher is better) and any detected "
    "issues with suggested fixes. If score > 0.8, the output is likely fine. "
    "If score < 0.5, consider revising based on the suggested fixes."
)


async def pisama_check_handler(
    input_data: Dict[str, Any],
    tool_use_id: Optional[str] = None,
    context: Any = None,
) -> Dict[str, Any]:
    """Handler for the pisama_check custom tool.

    Called by Claude Agent SDK when the agent invokes pisama_check.

    Args:
        input_data: Tool input with "output", optional "context" and "detectors"
        tool_use_id: Unique tool invocation ID
        context: SDK context (signal, etc.)

    Returns:
        Check result dict with passed, score, issues, detectors_run
    """
    output_text = input_data.get("output", "")
    check_context = input_data.get("context")
    detectors = input_data.get("detectors")

    if not output_text:
        return {
            "passed": True,
            "score": 1.0,
            "issues": [],
            "detectors_run": [],
            "check_time_ms": 0,
            "error": "No output provided to check",
        }

    result = await check(
        output=output_text,
        context=check_context,
        detectors=detectors,
    )

    logger.info(
        "pisama_check: passed=%s score=%.2f issues=%d time=%dms",
        result.get("passed"),
        result.get("score", 0),
        len(result.get("issues", [])),
        result.get("check_time_ms", 0),
    )

    return result


def create_check_tool() -> Dict[str, Any]:
    """Create a framework-neutral ``pisama_check`` tool descriptor.

    The current Claude Agent SDK does not accept dictionary descriptors on
    ``ClaudeAgentOptions``. Use :func:`create_claude_check_server` for that
    integration.

    Returns:
        Tool definition dict with name, description, input_schema, and handler.

    """
    return {
        "name": "pisama_check",
        "description": PISAMA_CHECK_DESCRIPTION,
        "input_schema": PISAMA_CHECK_TOOL_SCHEMA,
        "handler": pisama_check_handler,
    }


def _require_claude_agent_sdk() -> tuple[Any, Any]:
    try:
        from claude_agent_sdk import create_sdk_mcp_server, tool
    except ImportError as exc:
        raise ImportError(
            "Claude Agent SDK integration requires: "
            'pip install "pisama-agent-sdk[claude]"'
        ) from exc
    return tool, create_sdk_mcp_server


def create_claude_check_tool() -> Any:
    """Create a native Claude Agent SDK ``SdkMcpTool``."""
    tool, _ = _require_claude_agent_sdk()

    @tool(
        "pisama_check",
        PISAMA_CHECK_DESCRIPTION,
        PISAMA_CHECK_TOOL_SCHEMA,
    )
    async def _claude_check(input_data: Dict[str, Any]) -> Dict[str, Any]:
        result = await pisama_check_handler(input_data)
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result, sort_keys=True),
                }
            ],
        }

    return _claude_check


def create_claude_check_server(
    *,
    name: str = "pisama",
    version: str = "1.0.0",
) -> Any:
    """Create an in-process MCP server containing ``pisama_check``."""
    _, create_sdk_mcp_server = _require_claude_agent_sdk()
    return create_sdk_mcp_server(
        name=name,
        version=version,
        tools=[create_claude_check_tool()],
    )
