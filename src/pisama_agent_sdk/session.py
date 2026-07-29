"""Session state management for detection context. Thin forwarder.

The real implementation lives in :mod:`pisama.agents.session`.
``session_manager`` is the exact same module-level singleton instance
that :mod:`pisama.agents.session` constructs at import time -- sessions
tracked through this package and through ``pisama.agents`` directly are
the same sessions, not two independent caches.
"""

from pisama.agents.session import SessionManager, SessionState, session_manager

__all__ = [
    "SessionState",
    "SessionManager",
    "session_manager",
]
