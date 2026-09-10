# Healing result documentation

**Status:** In review
**As of:** 2026-09-10
**Owner:** engineering
**Supersedes:** none
**Evidence scope:** branch-only documentation

## Goal and boundaries

Starting from canonical main d987a1d, clarify that both application and
escalation flags being false does not imply an absent suggestion. Callers must
remain observe-only; a retained fix or derived patch is for human inspection,
not permission to apply it. Document the current parser's omission of unknown
response fields without implying loss of its recognized flags and message.

Only README, Python docstrings, and this plan may change. No behavior,
dependencies, versions, generated packages, publication, provider calls, or
production writes. This is not certification of autonomous safety if evidence
is restored later. No repository AGENTS.md or CLAUDE.md exists at this base;
CONTRIBUTING.md was read.

## Verification / DONE

- Inspect src/pisama_agent_sdk/heal.py and the canonical Python parser.
- Compare Python AST with base after removing docstrings: executable code must
  be identical; confirm dependency/version manifests unchanged.
- Run the existing real-object, network-free tests/test_heal.py controls.
- Check documentation wording and git diff --check.
- Independent root review is required before any push. No documentation build
  configuration exists in this repository; package builds are separate checks.

## State

Plan recorded before documentation edits. README and Python docstrings now
clarify observe-only behavior, inspection-only suggestions, and the parser's
recognized-field boundary. Executable AST comparison against the starting
commit (after removing docstrings) passed; pyproject.toml is unchanged.

Actual focused command:

```bash
PYTHONPATH=src:/tmp/pisama-python-healing-result-docs/src /Users/tuomonikulainen/pisama/backend/.venv/bin/python -m pytest --noconftest tests/test_heal.py -q
git diff --check
```

Four real-object tests passed in 0.15s, zero skips. These exercise existing
accessors, not live hosted endpoint behavior or published artifact delivery.
The Agent SDK is a thin forwarder: its current canonical source has no
independent result parser or duplicated HealingResult class. The Python
canonical parser contains the obsolete both-false wording; the shim README
and module now explain the forwarded semantics.

Full contributor checks on Python 3.11.13 with public pisama 0.7.0 and
pisama-core 1.11.0: 122 tests passed in 1.03s, zero skips. Ruff passed; mypy
passed all 24 source files. Fresh local wheel and sdist builds and twine checks
passed. A separate clean wheel environment installed public dependencies and
imported the actual forwarding objects successfully. Outputs are local
verification artifacts only, not a new 0.4.1 release or permission to overwrite
public packages. No multi-Python CI matrix run is claimed.

Full tests ran with an empty inherited credential environment and an audit
hook rejecting non-loopback socket connections in the pytest process.
Existing suite internals were not rewritten and are not being presented as
live-provider workflow proof.

Root approved the documentation-only diff; the requested grammar correction
was applied. No runtime code, version, dependency, push, package publication,
or production change. Commits remain isolated for root release review.
