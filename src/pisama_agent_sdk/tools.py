"""Custom tools for Claude Agent SDK integration. Thin forwarder.

The real implementation lives in :mod:`pisama.agents.tools`. Usage is
unchanged:

    from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
    from pisama_agent_sdk import create_check_tool

    options = ClaudeAgentOptions(
        custom_tools=[create_check_tool()],
    )

    async with ClaudeSDKClient(options=options) as client:
        await client.query("Analyze the auth service incident")
        async for message in client.receive_response():
            print(message)
"""

from pisama.agents.tools import (
    PISAMA_CHECK_DESCRIPTION,
    PISAMA_CHECK_TOOL_SCHEMA,
    create_check_tool,
    pisama_check_handler,
)

__all__ = [
    "PISAMA_CHECK_TOOL_SCHEMA",
    "PISAMA_CHECK_DESCRIPTION",
    "pisama_check_handler",
    "create_check_tool",
]
