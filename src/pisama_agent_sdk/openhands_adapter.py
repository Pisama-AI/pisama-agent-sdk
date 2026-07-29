"""OpenHands event-stream → Pisama bridge. Thin forwarder.

The real implementation lives in
:mod:`pisama.agents.openhands_adapter`. Usage is unchanged::

    from pathlib import Path
    from pisama_agent_sdk import OpenHandsEventStreamAdapter

    adapter = OpenHandsEventStreamAdapter()  # batch mode
    # ... wire adapter.on_action / on_observation into the OpenHands
    #     EventStream subscriber ...
    result = adapter.on_session_complete(Path("/path/to/session"))
    if result.has_failures:
        for d in result.failures:
            print(d.detector, d.severity, d.title)
"""

from pisama.agents.openhands_adapter import (
    OpenHandsEventStreamAdapter,
    StreamingCallback,
    StreamingDetection,
)

__all__ = [
    "OpenHandsEventStreamAdapter",
    "StreamingDetection",
    "StreamingCallback",
]
