# pisama-agent-sdk

[![PyPI version](https://img.shields.io/pypi/v/pisama-agent-sdk.svg)](https://pypi.org/project/pisama-agent-sdk/)
[![Python versions](https://img.shields.io/pypi/pyversions/pisama-agent-sdk.svg)](https://pypi.org/project/pisama-agent-sdk/)
[![CI](https://github.com/Pisama-AI/pisama-agent-sdk/actions/workflows/ci.yml/badge.svg)](https://github.com/Pisama-AI/pisama-agent-sdk/actions/workflows/ci.yml)
[![Security](https://github.com/Pisama-AI/pisama-agent-sdk/actions/workflows/security.yml/badge.svg)](https://github.com/Pisama-AI/pisama-agent-sdk/actions/workflows/security.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/Pisama-AI/pisama-agent-sdk/blob/main/LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/pisama-agent-sdk)](https://pypistats.org/packages/pisama-agent-sdk)

Typed Python adapters for real-time agent failure detection, ATIF trajectory
analysis, OpenHands monitoring, and evaluator workflows.

Passive hooks use the open source
[`pisama-core`](https://github.com/Pisama-AI/pisama-core) detector engine
locally. Telemetry is disabled by default.

## Requirements

| Component | Supported range |
| --- | --- |
| Python | 3.10 through 3.13 |
| `pisama-core` | 1.7.3 or newer, below 2.0 |
| Claude Agent SDK integration | 0.2.128 or newer, below 0.3 |
| ATIF | v1.0 through v1.7 |

CI tests every supported Python version. The minimum `pisama-core` version has
a separate compatibility gate.

## Install

Install local hooks and the framework-neutral SDK:

```bash
python -m pip install pisama-agent-sdk
```

Install native Claude Agent SDK integration:

```bash
python -m pip install "pisama-agent-sdk[claude]"
```

Other optional features are explicit:

```bash
python -m pip install "pisama-agent-sdk[evaluator]"     # HTTP evaluator and ATIF clients
python -m pip install "pisama-agent-sdk[telemetry]"     # opt-in PostHog telemetry
python -m pip install "pisama-agent-sdk[verification]"  # Claude-backed verification
```

## Claude Agent SDK hooks

`create_claude_hooks()` returns the mapping accepted by
`ClaudeAgentOptions.hooks`:

```python
from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient
from pisama_agent_sdk import create_claude_hooks

options = ClaudeAgentOptions(
    hooks=create_claude_hooks(),
)

async with ClaudeSDKClient(options=options) as client:
    await client.query("Inspect the repository and summarize its test coverage.")
    async for message in client.receive_response():
        print(message)
```

Pisama checks each tool call before execution and records its result after
execution. When a severe failure pattern is detected, the pre-tool hook returns
the Claude Agent SDK `deny` decision with a reason. The agent can then adjust
its approach.

### Configure thresholds

```python
from pisama_agent_sdk import BridgeConfig, configure_bridge, create_claude_hooks

bridge = configure_bridge(
    BridgeConfig(
        warning_threshold=40,
        block_threshold=60,
        detection_timeout_ms=80,
        fail_open=True,
    )
)

hooks = create_claude_hooks(bridge=bridge)
```

`fail_open=True` lets the tool call proceed when the hook itself fails or times
out. Set it to `False` on a class-based `PreToolUseHook` when your host requires
strict failure behavior.

### Filter tools

Pisama's matcher controls which callbacks run detection. The Claude matcher
controls which callbacks the Claude SDK invokes.

```python
from pisama_agent_sdk import FILE_TOOLS, create_claude_hooks

hooks = create_claude_hooks(
    tool_matcher=FILE_TOOLS,
    sdk_matcher="Read|Write|Edit|Glob|Grep",
)
```

Built-in Pisama matchers are `ALL_TOOLS`, `FILE_TOOLS`, `SHELL_TOOLS`,
`DANGEROUS_COMMANDS`, and `AGENT_TOOLS`.

## Claude self-check tool

The current Claude Agent SDK exposes custom tools through an in-process MCP
server:

```python
from claude_agent_sdk import ClaudeAgentOptions
from pisama_agent_sdk import create_claude_check_server

pisama_server = create_claude_check_server()

options = ClaudeAgentOptions(
    mcp_servers={"pisama": pisama_server},
    allowed_tools=["mcp__pisama__pisama_check"],
)
```

The tool returns both text and structured content. `create_check_tool()` remains
available as a framework-neutral dictionary descriptor for hosts that accept
that shape.

## Direct self-check

`check()` runs the local detector bridge:

```python
from pisama_agent_sdk import check

result = await check(
    output="The server is healthy based on the metrics.",
    context={
        "query": "Is auth-service down?",
        "sources": ["health-check output", "service logs"],
    },
)

if not result["passed"]:
    print(result["issues"])
```

## ATIF and OpenHands

Analyze one ATIF trajectory through a Pisama deployment:

```python
from pisama_agent_sdk import analyze_atif

result = analyze_atif(
    "trajectory.json",
    api_key="pisama_...",
)

if not result.analysis_complete:
    raise RuntimeError(result.detectors_failed)
```

Analyze a completed OpenHands session:

```bash
export PISAMA_API_KEY="pisama_..."
pisama-openhands-monitor ./sessions/run-001 --json
```

Both clients default to `https://api.pisama.ai`. Pass `api_url` to use a
self-hosted deployment.

## Evaluator client

Evaluator mode requires the `evaluator` extra and a Pisama API key. Server-side
feature access is still enforced by the target Pisama deployment.

```python
from pisama_agent_sdk import PisamaEvaluator

with PisamaEvaluator(api_key="pisama_...") as evaluator:
    result = evaluator.evaluate(
        specification={"text": "Return the deployed health-check evidence."},
        output={"text": "Health check returned HTTP 200."},
    )

print(result.passed, result.failures)
```

The client exchanges the API key for a short-lived bearer token before calling
the evaluator endpoint.

## Network and data behavior

- Passive pre-tool and post-tool detection runs locally with `pisama-core`.
- Telemetry is off unless `enable_telemetry=True` and a telemetry key are set.
- `analyze_atif`, `PisamaEvaluator`, `heal_now`, and auto-verification call the
  configured Pisama API.
- `PISAMA_API_URL` overrides the hosted API where supported.
- `PISAMA_API_KEY` supplies credentials where supported.

Review the
[security policy](https://github.com/Pisama-AI/pisama-agent-sdk/security/policy)
before reporting a vulnerability.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
ruff check src tests
mypy src/pisama_agent_sdk
pytest -q --cov=pisama_agent_sdk --cov-fail-under=70
python -m build
python -m twine check dist/*
```

See the
[contribution guide](https://github.com/Pisama-AI/pisama-agent-sdk/blob/main/CONTRIBUTING.md)
and
[release notes](https://github.com/Pisama-AI/pisama-agent-sdk/blob/main/CHANGELOG.md).

## License

MIT
