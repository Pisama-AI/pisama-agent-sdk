# Contributing to pisama-agent-sdk

Thanks for your interest in improving `pisama-agent-sdk`. **As of
0.4.0, this repository is a thin compatibility shim** — every module
under `src/pisama_agent_sdk/` re-exports the equivalent object from
`pisama.agents` (part of the
[`pisama-python`](https://github.com/Pisama-AI/pisama-python) repo,
published as `pisama` on PyPI). There is no detection logic, hook
implementation, or ATIF client code living in this repository anymore.

**If you want to add a hook point, a framework adapter, fix detection
behavior, or change anything a hook actually *does*, that change
belongs in [`pisama-python`](https://github.com/Pisama-AI/pisama-python)'s
`src/pisama/agents/` — open your PR there.** Core detection engine
lives in [`pisama-core`](https://github.com/tn-pisama/pisama-core);
advanced detectors and calibrated thresholds live in
[Pisama](https://pisama.ai) Cloud.

## What we're looking for (in *this* repo)

- **Forwarder bugs**: a symbol that used to be importable from
  `pisama_agent_sdk` (or a deep path like
  `pisama_agent_sdk.hooks.pre_tool_use`) but no longer is, or that
  forwards to the wrong `pisama.agents` object.
  `tests/test_real_public_workflows.py` and the per-module tests are
  the regression net for this.
- **Version/dependency drift**: `pyproject.toml`'s `pisama>=X.Y.Z`
  floor falling behind what `pisama.agents` actually needs, or the
  `[project.scripts]` entry point breaking.
- **Bug reports** with a minimal reproducer for anything specific to
  this package's forwarding layer (as opposed to detection behavior,
  which is a `pisama-python` issue).
- **Documentation fixes** on this README and this CONTRIBUTING guide.

## What we're not looking for

- New hooks, detectors, adapters, or any other implementation code —
  see above, that goes in `pisama-python`.
- Tuned detection thresholds. Those are Pisama Cloud features.
- Hook paths that auto-terminate agent runs without a documented opt-in.

## Development setup

```bash
git clone https://github.com/tn-pisama/pisama-agent-sdk.git
cd pisama-agent-sdk
python3 -m venv .venv && source .venv/bin/activate
pip install -e .[dev]
pytest tests/
```

## PR checklist

- [ ] Every module still forwards a real object from `pisama.agents` —
      no reimplementation, no logic living in this package.
- [ ] Clean-venv install succeeds with the declared dependencies
      (`pip install pisama-agent-sdk` alone, no extras, against the
      real `pisama` release on PyPI).
- [ ] Existing tests pass: `pytest tests/ -q`.

## Licensing and contributor grant

By submitting a PR you agree that your contribution is licensed under
MIT, the same license as this repo.

## Questions

Open a GitHub Discussion or visit [pisama.ai](https://pisama.ai).
