# Changelog

## Unreleased

## 0.2.2

- Add native Claude Agent SDK hook and MCP tool factories, with real contract
  tests against the supported Claude SDK range.
- Emit the Claude Agent SDK `deny` decision for blocked tool calls.
- Deliver SAFE auto-heal patches and post-tool recovery guidance through the
  Claude Agent SDK model-context contract.
- Cache evaluator bearer tokens, refresh them near expiry or after a 401, and
  avoid repeated authentication during evaluation sequences.
- Apply Pisama tool matchers consistently to pre-tool and post-tool processing.
- Document JSON text as the current Claude MCP result contract and exercise the
  complete in-process MCP server boundary.
- Point the evaluator client at `api.pisama.ai` and exchange API keys for the
  bearer tokens required by the current evaluator endpoint.
- Replace non-functional public examples, legacy repository links, and the
  broken Discussions support link.
- Add bounded optional dependencies, minimum `pisama-core` compatibility
  coverage, and stronger wheel and sdist smoke tests.
- Derive the runtime version from installed distribution metadata to prevent
  package and module version drift.
- Add dependency vulnerability auditing, explicit code ownership, and a
  working support-question path.

## 0.2.1

- Add a full-package coverage regression gate and security scanning.
- Declare the MIT license classifier in package metadata.
- Document ATIF, OpenHands, and Harbor-compatible evaluation use cases.
- Add typed-package metadata, mypy checks, dependency automation, distribution
  inspection, and clean-wheel smoke testing.
- Correct nullable endpoint handling and the clarification provider type
  contract.
- Refresh build, lint, publishing, and GitHub Actions tooling while preserving
  broad compatibility for optional runtime dependencies.
- Raise full-package coverage from 61.53% to more than 70% with real
  pisama-core detector runs and captured Harbor tool calls.
- Fix `check()` local detection against the current pisama-core Span contract;
  it previously failed silently and fell through to the network API.
- Make `BridgeConfig.save()` output loadable by `BridgeConfig.from_file()`.
- Support the documented `configure_bridge(BridgeConfig(...))` call and
  matcher filtering on `PreToolUseHook`.
- Constrain pisama-core to its compatible major version.
- Add Python 3.13 support metadata and release coverage.
- Pin release actions and stabilize lint configuration.

## 0.2.0

- Add ATIF v1.7 analysis support.
- Add the OpenHands session monitor command.
- Test package installation and public APIs on Python 3.10 through 3.13.

## 0.1.1

- Improve package metadata and release automation.
