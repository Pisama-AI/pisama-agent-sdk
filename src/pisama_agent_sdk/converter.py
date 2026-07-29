"""Converts Claude Agent SDK HookInput to pisama-core Span format. Thin forwarder.

The real implementation lives in :mod:`pisama.agents.converter`.
"""

from pisama.agents.converter import HookInputConverter

__all__ = [
    "HookInputConverter",
]
