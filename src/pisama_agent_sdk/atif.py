"""ATIF trajectory analysis client. Thin forwarder.

The real implementation now lives in :mod:`pisama.agents.atif` (the
``pisama`` base package, installed automatically as a dependency of this
distribution). This module re-exports its public API unchanged so
existing ``from pisama_agent_sdk import analyze_atif`` / ``from
pisama_agent_sdk.atif import ...`` call sites keep working without
modification.

Usage (unchanged)::

    from pisama_agent_sdk import analyze_atif

    result = analyze_atif("./trajectories/run-001.json")
    if not result.analysis_complete:
        raise RuntimeError("ATIF analysis was incomplete")
    elif result.has_failures:
        for d in result.failures:
            print(d.detector, d.severity, d.title)

For directories or many files::

    from pisama_agent_sdk import analyze_atif_batch

    results = analyze_atif_batch("./trajectories/")
    for r in results:
        print(r.trace_id, r.failure_count)
"""

# DEFAULT_TIMEOUT_SECONDS and the two underscore-prefixed helpers below
# are forwarded but not part of the documented public API (they were
# not in the original module's own __all__ either). Kept importable for
# backward compatibility with anything that reached into these names
# directly; the two underscore-prefixed helpers are also white-box
# tested by this repo's own test suite -- see tests/test_atif.py.
from pisama.agents.atif import (
    DEFAULT_API_URL,
    DEFAULT_TIMEOUT_SECONDS,  # noqa: F401
    SUPPORTED_SCHEMA_VERSIONS,
    AtifAnalyzeResult,
    AtifDetection,
    _discover_trajectory_files,  # noqa: F401
    _load_trajectory,  # noqa: F401
    analyze_atif,
    analyze_atif_batch,
)

__all__ = [
    "AtifAnalyzeResult",
    "AtifDetection",
    "DEFAULT_API_URL",
    "SUPPORTED_SCHEMA_VERSIONS",
    "analyze_atif",
    "analyze_atif_batch",
]
