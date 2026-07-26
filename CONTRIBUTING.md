# Contributing to pisama-agent-sdk

Thanks for your interest in improving `pisama-agent-sdk`. This package
provides Claude Agent SDK hooks for real-time failure detection,
flagging loops, hallucinations, and other failures before they consume
tokens. Core detection engine lives in
[`pisama-core`](https://github.com/Pisama-AI/pisama-core);
advanced detectors and calibrated thresholds live in
[Pisama](https://pisama.ai) Cloud.

## What we're looking for

- **New hook points** for agent lifecycle events that Claude Agent SDK
  exposes (pre-tool-call, post-tool-call, message-stream, etc.).
- **Framework adapters** for related orchestrators that want the same
  detection surface.
- **Bug reports** with a minimal reproducer, especially cases where
  a hook fails to fire or misclassifies a legitimate retry.
- **Documentation fixes** on the hook matrix and configuration.

## What we're not looking for

- Tuned detection thresholds. Those are Pisama Cloud features.
- Hook paths that auto-terminate agent runs without a documented opt-in.

## Development setup

```bash
git clone https://github.com/Pisama-AI/pisama-agent-sdk.git
cd pisama-agent-sdk
python3 -m venv .venv && source .venv/bin/activate
python -m pip install -e ".[dev]"
ruff check src tests
mypy src/pisama_agent_sdk
pytest -q --cov=pisama_agent_sdk --cov-fail-under=70
```

## PR checklist

- [ ] New hook (if applicable) is registered via the documented hook
      API and disables cleanly when the user opts out.
- [ ] Detection calls go through `pisama_core`; no detection logic
      lives in this package.
- [ ] Clean-venv install succeeds with the declared dependencies.
- [ ] Supported public examples remain covered by a real compatibility test.
- [ ] Existing tests pass with the coverage gate.

## Compatibility and releases

- Supported Python and dependency ranges are published in the README and
  enforced in CI.
- Breaking changes require a changelog entry and a migration note. Before
  1.0, deprecate a public API for at least one minor release when practical.
- Releases come from version tags whose commits belong to the protected
  `main` branch.
- Wheel and sdist artifacts must pass clean-environment tests before trusted
  publishing can run.

## Licensing and contributor grant

By submitting a PR you agree that your contribution is licensed under
MIT, the same license as this repo.

## Questions

Open a
[question issue](https://github.com/Pisama-AI/pisama-agent-sdk/issues/new?template=question.yml)
or visit [pisama.ai](https://pisama.ai).
