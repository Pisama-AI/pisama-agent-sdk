"""Sync in-loop healing for the Pisama Agent SDK. Thin forwarder.

The real implementation lives in :mod:`pisama.agents.heal`. Usage is
unchanged:

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
