"""SDK-side indication channel — out-of-band signal for the developer. Thin forwarder.

The real implementation lives in :mod:`pisama.agents.indication`. Usage
is unchanged:

    from pisama_agent_sdk import on_indication

    @on_indication
    def alert_me(indication):
        print(f"[Pisama] {indication.severity}: {indication.headline}")
        if indication.action_required:
            send_to_pagerduty(indication.to_dict())

    # Or pass a callable directly:
    on_indication(my_callback)
"""

from pisama.agents.indication import (
    SDKIndication,
    clear_indication_callbacks,
    on_indication,
)

__all__ = [
    "SDKIndication",
    "on_indication",
    "clear_indication_callbacks",
]
