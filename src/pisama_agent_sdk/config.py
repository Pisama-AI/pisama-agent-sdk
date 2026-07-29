"""Configuration management for Agent SDK integration. Thin forwarder.

The real implementation lives in :mod:`pisama.agents.config`.
"""

from pisama.agents.config import BridgeConfig, load_config

__all__ = [
    "BridgeConfig",
    "load_config",
]
