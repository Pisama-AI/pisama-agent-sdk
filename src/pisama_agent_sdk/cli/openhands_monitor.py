"""``pisama-openhands-monitor`` CLI. Thin forwarder.

The real implementation lives in
:mod:`pisama.agents.cli.openhands_monitor`. Wraps
:class:`pisama.agents.OpenHandsEventStreamAdapter` for batch analysis of
a completed session directory.

Usage::

    pisama-openhands-monitor <session-dir>
    pisama-openhands-monitor <session-dir> --api-url https://api.pisama.ai
    pisama-openhands-monitor <session-dir> --json   # full diagnosis as JSON

Exit codes:
  0 — analysis succeeded, no failures detected
  1 — analysis succeeded, at least one failure detected
  2 — usage / runtime error (e.g., session_dir missing trajectory.json)
"""

import sys

from pisama.agents.cli.openhands_monitor import main

__all__ = ["main"]

if __name__ == "__main__":
    sys.exit(main())
