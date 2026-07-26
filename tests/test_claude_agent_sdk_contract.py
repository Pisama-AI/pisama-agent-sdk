"""Compatibility tests against the installed Claude Agent SDK."""

from __future__ import annotations

import json
from importlib.metadata import version
from typing import Any, Literal, get_args, get_origin, get_type_hints

import pytest
from claude_agent_sdk import ClaudeAgentOptions, SdkMcpTool
from claude_agent_sdk import HookMatcher as ClaudeHookMatcher
from claude_agent_sdk.types import (
    PostToolUseHookSpecificOutput,
    PreToolUseHookSpecificOutput,
)
from mcp.shared.memory import create_connected_server_and_client_session

from pisama_agent_sdk import (
    BridgeConfig,
    BridgeResult,
    DetectionBridge,
    HealingResult,
    HookMatcher,
    PisamaEvaluator,
    SessionManager,
    configure_bridge,
    create_claude_check_server,
    create_claude_check_tool,
    create_claude_hooks,
)
from pisama_agent_sdk.evaluator import DEFAULT_API_URL, _parse_access_token
from pisama_agent_sdk.hooks.post_tool_use import _recovery_output
from pisama_agent_sdk.hooks.pre_tool_use import _heal_output


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


def test_safe_heal_patch_uses_the_exact_model_context_contract() -> None:
    patch = "Limit retries to three attempts before selecting another action."
    output = _heal_output(
        HealingResult(
            applied=True,
            escalated=False,
            risk_level="safe",
            fix={"metadata": {"framework_specific_code": patch}},
        )
    )

    assert output == {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "Pisama denied this invocation after applying a SAFE fix. "
                "Retry using the supplied additional context."
            ),
            "additionalContext": patch,
        },
        "systemMessage": patch,
    }
    assert "additionalContext" in get_type_hints(
        PreToolUseHookSpecificOutput,
        include_extras=True,
    )


def test_post_tool_recovery_uses_the_exact_model_context_contract() -> None:
    guidance = "Inspect the failed tool output before choosing a different action."
    output = _recovery_output(guidance)

    assert output == {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": guidance,
        },
        "systemMessage": guidance,
    }
    assert "additionalContext" in get_type_hints(
        PostToolUseHookSpecificOutput,
        include_extras=True,
    )


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
async def test_native_claude_check_tool_returns_canonical_json_text() -> None:
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
    assert set(response) == {"content"}
    text_result = json.loads(response["content"][0]["text"])
    assert text_result["detectors_run"] == ["realtime"]


@pytest.mark.asyncio
async def test_native_check_result_crosses_the_real_mcp_server_boundary() -> None:
    configure_bridge(
        BridgeConfig(
            detection_timeout_ms=1000,
            tool_patterns=[".*"],
            excluded_tools=[],
        )
    )
    server = create_claude_check_server()

    async with create_connected_server_and_client_session(
        server["instance"]
    ) as session:
        listed = await session.list_tools()
        response = await session.call_tool(
            "pisama_check",
            {
                "output": "Created the requested directory and file.",
                "context": {
                    "query": "Create a directory and place one file inside it.",
                    "sources": ["captured tool result"],
                },
            },
        )

    assert [tool.name for tool in listed.tools] == ["pisama_check"]
    assert response.isError is False
    assert response.structuredContent is None
    assert response.content[0].type == "text"
    wire_result = json.loads(response.content[0].text)
    assert wire_result["detectors_run"] == ["realtime"]


def test_native_check_server_is_accepted_by_claude_options() -> None:
    server = create_claude_check_server()
    options = ClaudeAgentOptions(
        mcp_servers={"pisama": server},
        allowed_tools=["mcp__pisama__pisama_check"],
    )

    assert options.mcp_servers["pisama"]["type"] == "sdk"
    assert options.mcp_servers["pisama"]["name"] == "pisama"
    assert options.allowed_tools == ["mcp__pisama__pisama_check"]


@pytest.mark.asyncio
async def test_factory_tool_matcher_excludes_pre_and_post_processing() -> None:
    bridge = DetectionBridge(
        BridgeConfig(
            detection_timeout_ms=1000,
            tool_patterns=[".*"],
            excluded_tools=[],
        ),
        session_mgr=SessionManager(),
    )
    matcher = HookMatcher(exclude_tools=["Read"])
    hooks = create_claude_hooks(bridge=bridge, tool_matcher=matcher)
    pre_hook = hooks["PreToolUse"][0].hooks[0]
    post_hook = hooks["PostToolUse"][0].hooks[0]
    excluded_input = {
        "tool_name": "Read",
        "tool_input": {"file_path": "README.md"},
        "tool_response": {"content": "package documentation"},
        "session_id": "excluded-tool",
    }

    assert pre_hook.matcher is matcher
    assert post_hook.matcher is matcher
    assert await pre_hook(excluded_input, "excluded-pre", {}) == {}
    assert await post_hook(excluded_input, "excluded-post", {}) == {}
    assert bridge.sessions.session_count == 0


def test_evaluator_defaults_to_live_api_without_legacy_header() -> None:
    with PisamaEvaluator(api_key="pisama_contract_test") as evaluator:
        assert evaluator.base_url == DEFAULT_API_URL
        assert "x-mao-api-key" not in evaluator._client.headers
        assert "authorization" not in evaluator._client.headers


def test_auth_token_payload_requires_a_nonempty_token() -> None:
    assert _parse_access_token({"access_token": " signed-token "}) == "signed-token"
    with pytest.raises(ValueError, match="access_token"):
        _parse_access_token({})
