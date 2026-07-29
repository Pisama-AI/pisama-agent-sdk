# Changelog

## [0.3.2] - 2026-07-29

### Fixed

- The README linked the Claude Agent SDK at
  `github.com/anthropics/claude-code/tree/main/packages/claude-agent-sdk`, which
  returns 404. Upstream moved the Python SDK to its own repository. The link now
  points at `github.com/anthropics/claude-agent-sdk-python`, which is also the
  `Homepage` in the `claude-agent-sdk` PyPI metadata. PyPI renders the README from
  the published artifact, so this needs a release to reach the people who read it.

### Changed

- Declare the licence as the PEP 639 SPDX expression `license = "MIT"` with
  `license-files = ["LICENSE"]`, replacing the deprecated `{text = "MIT"}` table.
  The wheel now carries `License-Expression: MIT` and `License-File: LICENSE`
  instead of the free-text `License` field.
- Drop the `License :: OSI Approved :: MIT License` trove classifier. The
  `pyproject.toml` specification deprecates `License ::` classifiers and permits
  build tools to reject a project that sets both them and an SPDX expression;
  setuptools already errors on that combination. The licence is not lost, it moves
  into `License-Expression`.
- Require `hatchling>=1.27` to build, the first release line that emits core
  metadata 2.4 and reads `license-files` as a list of glob patterns.

## [0.3.1] - 2026-07-29

### Security

- `PisamaEvaluator` defaulted `base_url` to `https://mao-api.fly.dev`, a pre-rebrand
  Fly.io hostname that is no longer a deployed app. Fly app names are globally unique
  and become claimable once released, so any third party could have created an app of
  that name and received the `api_key` this client sets as a default header on every
  request. The default is now `https://api.pisama.ai`.

### Fixed

- Authenticate with `Authorization: Bearer` instead of the legacy `X-MAO-API-Key`
  header. That header is not read anywhere in the current backend, and
  `POST /api/v1/evaluate` declares `HTTPBearer`, so requests could not have succeeded
  against the live API regardless of host.

## Unreleased

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
