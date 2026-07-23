"""Pisama Agent SDK Integration.

Provides hooks and tools for Claude Agent SDK that connect to
Pisama's detection infrastructure for real-time failure prevention.

Quick Start (passive monitoring):
    from pisama_agent_sdk import pre_tool_use_hook, post_tool_use_hook

    agent.hooks.pre_tool_use = pre_tool_use_hook
    agent.hooks.post_tool_use = post_tool_use_hook

Agent Self-Check (active verification):
    from pisama_agent_sdk import check

    result = await check(
        output="The server is healthy based on the metrics.",
        context={"query": "Is auth-service down?", "sources": [...]}
    )
    if not result["passed"]:
        # Revise output based on result["issues"]

Claude Agent SDK Custom Tool:
    from pisama_agent_sdk import create_check_tool
    from claude_agent_sdk import ClaudeAgentOptions

    options = ClaudeAgentOptions(
        custom_tools=[create_check_tool()],
    )
"""

__version__ = "0.2.0"

# Hook functions (primary API)
from .hooks.pre_tool_use import pre_tool_use_hook, PreToolUseHook
from .hooks.post_tool_use import post_tool_use_hook, PostToolUseHook

# In-loop healing (Track B)
from .heal import heal_now, HealingResult

# Clarification primitive (Track F) — pause/ask/resume for entity_confusion etc.
from .clarification import (
    ClarificationPrimitive,
    ClarificationRequest,
    Resolution as ClarificationResolution,
    register_clarification_builder,
)

# Indication channel (Track G) — out-of-band signal for the developer
# running the agent. Wire on_indication(callable) to receive structured
# notifications on every healing outcome.
from .indication import (
    SDKIndication,
    on_indication,
    clear_indication_callbacks,
)

# Auto-verify (Track H3) — runs an innovation primitive locally with a
# real Claude client when the backend surfaces a recommended_verification
# hint, then POSTs the outcome back to /healing/confirm-applied so
# FixEffectivenessTracker accumulates real efficacy data alongside the
# async-verification scheduler.
from .auto_verify import auto_verify_and_confirm, AutoVerifyResult

# Configuration
from .bridge import configure_bridge, create_bridge, get_bridge
from .config import BridgeConfig, load_config

# Bridge (for advanced use)
from .bridge import DetectionBridge

# Types
from .types import BridgeResult, HookInput, HookContext, HookJSONOutput

# Matchers
from .hooks.matchers import (
    HookMatcher,
    ALL_TOOLS,
    FILE_TOOLS,
    SHELL_TOOLS,
    DANGEROUS_COMMANDS,
    AGENT_TOOLS,
    create_matcher,
)

# Session management
from .session import SessionManager, session_manager

# Agent self-check
from .check import check, configure_check

# Specification compliance (beta, gated by PISAMA_ENABLE_CHECK_COMPLIANCE)
from .check_compliance import (
    BehavioralRule,
    ComplianceResult,
    PisamaFeatureNotEnabledError,
    Violation,
    check_compliance,
)

# Custom tools for Claude Agent SDK
from .tools import create_check_tool, pisama_check_handler

# Evaluator client (Pisama-as-evaluator for multi-agent harnesses)
from .evaluator import PisamaEvaluator, EvalResult, EvalFailure

# ATIF (Harbor) trajectory analysis
from .atif import (
    analyze_atif,
    analyze_atif_batch,
    AtifAnalyzeResult,
    AtifDetection,
)

# OpenHands event-stream adapter (Phase C of plan-to-all-5-unified-glade)
from .openhands_adapter import (
    OpenHandsEventStreamAdapter,
    StreamingDetection,
    StreamingCallback,
)

# Chaos engineering (SDK-level failure injection)
from .chaos import (
    ChaosConfig,
    ToolFailure,
    LatencyInjection,
    ErrorInjection,
    OutputCorruption,
    ContextTruncation,
)

__all__ = [
    # Version
    "__version__",
    # Hook functions
    "pre_tool_use_hook",
    "post_tool_use_hook",
    # Hook classes
    "PreToolUseHook",
    "PostToolUseHook",
    # Configuration
    "configure_bridge",
    "create_bridge",
    "get_bridge",
    "BridgeConfig",
    "load_config",
    # Bridge
    "DetectionBridge",
    # Types
    "BridgeResult",
    "HookInput",
    "HookContext",
    "HookJSONOutput",
    # Matchers
    "HookMatcher",
    "ALL_TOOLS",
    "FILE_TOOLS",
    "SHELL_TOOLS",
    "DANGEROUS_COMMANDS",
    "AGENT_TOOLS",
    "create_matcher",
    # Session
    "SessionManager",
    "session_manager",
    # Agent self-check
    "check",
    "configure_check",
    # In-loop healing
    "heal_now",
    "HealingResult",
    # Clarification primitive
    "ClarificationPrimitive",
    "ClarificationRequest",
    "ClarificationResolution",
    "register_clarification_builder",
    # Specification compliance (beta)
    "check_compliance",
    "ComplianceResult",
    "BehavioralRule",
    "Violation",
    "PisamaFeatureNotEnabledError",
    # Indication channel (Track G)
    "SDKIndication",
    "on_indication",
    "clear_indication_callbacks",
    # Auto-verify (Track H3)
    "auto_verify_and_confirm",
    "AutoVerifyResult",
    # Custom tools
    "create_check_tool",
    "pisama_check_handler",
    # Evaluator
    "PisamaEvaluator",
    "EvalResult",
    "EvalFailure",
    # ATIF (Harbor) trajectory analysis
    "analyze_atif",
    "analyze_atif_batch",
    "AtifAnalyzeResult",
    "AtifDetection",
    # OpenHands event-stream adapter (Phase C)
    "OpenHandsEventStreamAdapter",
    "StreamingDetection",
    "StreamingCallback",
    # Chaos engineering
    "ChaosConfig",
    "ToolFailure",
    "LatencyInjection",
    "ErrorInjection",
    "OutputCorruption",
    "ContextTruncation",
]
