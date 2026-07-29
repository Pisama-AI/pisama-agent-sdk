"""Agent-initiated self-check — pisama.check(). Thin forwarder.

The real implementation lives in :mod:`pisama.agents.check`. Usage is
unchanged:

    from pisama_agent_sdk import check

    result = await check(
        output="The server is healthy based on the metrics I found.",
        context={"query": "Is auth-service down?", "sources": ["..."]}
    )
    if not result["passed"]:
        # Agent can retry, adjust, or escalate
        print(result["issues"])
"""

from pisama.agents.check import check, configure_check

__all__ = [
    "check",
    "configure_check",
]
