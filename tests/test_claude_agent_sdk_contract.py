"""Compatibility tests against the installed Claude Agent SDK."""

from __future__ import annotations

import json
from importlib.metadata import version
from typing import Any, Literal, get_args, get_origin, get_type_hints

import pytest
from claude_agent_sdk import ClaudeAgentOptions, SdkMcpTool
from claude_agent_sdk import HookMatcher as ClaudeHookMatcher
from claude_agent_sdk.types import PreToolUseHookSpecificOutput

from pisama_agent_sdk import (
    BridgeConfig,
    BridgeResult,
    PisamaEvaluator,
    configure_bridge,
    create_claude_check_server,
    create_claude_check_tool,
    create_claude_hooks,
)
from pisama_agent_sdk.evaluator import DEFAULT_API_URL, _parse_access_token


def _literal_values(annotation: Any) -> set[str]:
    if get_origin(annotation) is Literal:
        return {value for value in get_args(annotation) if isinstance(value, str)}
    values: set[str] = set()
    for argument in get_args(annotation):
        values.update(_literal_values(argument))
    return values


def test_runtime_version_matches_distribution_metadata() -> None:
    import pisama_agent_sdk

    assert pisama_agent_sdk.__version__ == version("pisama-agent-sdk")


def test_block_output_uses_current_claude_permission_contract() -> None:
    allowed = _literal_values(
        get_type_hints(
            PreToolUseHookSpecificOutput,
            include_extras=True,
        )["permissionDecision"]
    )
    output = BridgeResult(
        should_block=True,
        block_reason="Repeated tool loop",
    ).to_hook_output()
    decision = output["hookSpecificOutput"]["permissionDecision"]

    assert decision == "deny"
    assert decision in allowed
    assert "block" not in allowed


def test_hook_factory_builds_real_claude_options() -> None:
    bridge = configure_bridge(
        BridgeConfig(
            detection_timeout_ms=1000,
            tool_patterns=[".*"],
            excluded_tools=[],
        )
    )
    hooks = create_claude_hooks(
        bridge=bridge,
        sdk_matcher="Read|Write|Edit|Bash",
    )
    options = ClaudeAgentOptions(hooks=hooks)

    assert set(options.hooks) == {"PreToolUse", "PostToolUse"}
    assert all(
        isinstance(matchers[0], ClaudeHookMatcher)
        for matchers in options.hooks.values()
    )
    assert options.hooks["PreToolUse"][0].hooks[0].bridge is bridge
    assert options.hooks["PostToolUse"][0].hooks[0].bridge is bridge


@pytest.mark.asyncio
async def test_native_claude_check_tool_runs_real_local_detection() -> None:
    configure_bridge(
        BridgeConfig(
            detection_timeout_ms=1000,
            tool_patterns=[".*"],
            excluded_tools=[],
        )
    )
    tool = create_claude_check_tool()
    response = await tool.handler(
        {
            "output": "Created the requested directory and file.",
            "context": {
                "query": "Create a directory and place one file inside it.",
                "sources": ["captured tool result"],
            },
        }
    )

    assert isinstance(tool, SdkMcpTool)
    assert tool.name == "pisama_check"
    assert response["structuredContent"]["detectors_run"] == ["realtime"]
    text_result = json.loads(response["content"][0]["text"])
    assert text_result == response["structuredContent"]


def test_native_check_server_is_accepted_by_claude_options() -> None:
    server = create_claude_check_server()
    options = ClaudeAgentOptions(
        mcp_servers={"pisama": server},
        allowed_tools=["mcp__pisama__pisama_check"],
    )

    assert options.mcp_servers["pisama"]["type"] == "sdk"
    assert options.mcp_servers["pisama"]["name"] == "pisama"
    assert options.allowed_tools == ["mcp__pisama__pisama_check"]


def test_evaluator_defaults_to_live_api_without_legacy_header() -> None:
    with PisamaEvaluator(api_key="pisama_contract_test") as evaluator:
        assert evaluator.base_url == DEFAULT_API_URL
        assert "x-mao-api-key" not in evaluator._client.headers
        assert "authorization" not in evaluator._client.headers


def test_auth_token_payload_requires_a_nonempty_token() -> None:
    assert _parse_access_token({"access_token": " signed-token "}) == "signed-token"
    with pytest.raises(ValueError, match="access_token"):
        _parse_access_token({})
