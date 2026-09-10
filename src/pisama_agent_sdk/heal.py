"""Sync in-loop healing for the Pisama Agent SDK. Thin forwarder.

The real implementation lives in :mod:`pisama.agents.heal`. Usage is
unchanged. If both applied and escalated are false, remain observe-only.
A fix or derived prompt_patch may still be present for human inspection;
its presence is not permission to apply it. The forwarded Python parser
retains recognized flags and message but does not expose unknown response
fields such as application_blocked_reason. This is not certification of
autonomous safety if detector evidence is restored later.

Usage:

    from pisama_agent_sdk.heal import heal_now

    result = heal_now(
        detection_type="loop",
        details={"states": [...]},
        framework="claude_sdk",
    )
    if result.applied and result.prompt_patch:
        # Re-issue the agent's next step with the patch.
        ...
    elif result.escalated:
        # Block and route to human.
        ...
"""

from pisama.agents.heal import HealingResult, heal_now

__all__ = [
    "HealingResult",
    "heal_now",
]
