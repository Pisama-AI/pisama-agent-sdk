"""Detection Bridge - connects Agent SDK hooks to Pisama detection.

Thin forwarder to :mod:`pisama.agents.bridge`, which now holds the real
``DetectionBridge`` implementation. See that module for the actual
detection/blocking/recovery logic.
"""

from pisama.agents.bridge import (
    DetectionBridge,
    configure_bridge,
    create_bridge,
    get_bridge,
)

__all__ = [
    "DetectionBridge",
    "get_bridge",
    "configure_bridge",
    "create_bridge",
]
