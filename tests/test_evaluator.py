"""Evaluator authentication regressions over a real local HTTP boundary."""

from __future__ import annotations

import base64
import json
import logging
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Iterator

import pytest

from pisama_agent_sdk import PisamaEvaluator

_API_KEY = "pisama_evaluator_contract"
_EVALUATION_RESULT = {
    "passed": True,
    "score": 1.0,
    "failures": [],
    "suggestions": [],
    "detectors_run": ["contract"],
    "evaluation_time_ms": 1,
}


def _encode_segment(value: dict[str, object]) -> str:
    encoded = base64.urlsafe_b64encode(
        json.dumps(value, separators=(",", ":")).encode("utf-8")
    )
    return encoded.rstrip(b"=").decode("ascii")


def _token(expiry: float, sequence: int) -> str:
    return ".".join(
        (
            _encode_segment({"alg": "HS256", "typ": "JWT"}),
            _encode_segment({"exp": expiry, "sequence": sequence}),
            f"contract-signature-{sequence}",
        )
    )


@dataclass
class _ServerState:
    first_token_ttl: float = 3600.0
    reject_first_evaluation: bool = False
    authentication_count: int = 0
    evaluation_count: int = 0
    issued_tokens: list[str] = field(default_factory=list)


@contextmanager
def _evaluator_server(
    *,
    first_token_ttl: float = 3600.0,
    reject_first_evaluation: bool = False,
) -> Iterator[tuple[str, _ServerState]]:
    state = _ServerState(
        first_token_ttl=first_token_ttl,
        reject_first_evaluation=reject_first_evaluation,
    )

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length) or b"{}")

            if self.path == "/api/v1/auth/token":
                assert body == {"api_key": _API_KEY, "scope": "full"}
                state.authentication_count += 1
                ttl = (
                    state.first_token_ttl
                    if state.authentication_count == 1
                    else 3600.0
                )
                access_token = _token(
                    time.time() + ttl,
                    state.authentication_count,
                )
                state.issued_tokens.append(access_token)
                self._json_response(200, {"access_token": access_token})
                return

            if self.path == "/api/v1/evaluate":
                state.evaluation_count += 1
                expected = (
                    f"Bearer {state.issued_tokens[-1]}"
                    if state.issued_tokens
                    else ""
                )
                if self.headers.get("Authorization") != expected:
                    self._json_response(401, {"detail": "Invalid token"})
                    return
                if (
                    state.reject_first_evaluation
                    and state.evaluation_count == 1
                ):
                    self._json_response(401, {"detail": "Token has expired"})
                    return
                self._json_response(200, _EVALUATION_RESULT)
                return

            self._json_response(404, {"detail": "Not found"})

        def _json_response(
            self,
            status: int,
            body: dict[str, object],
        ) -> None:
            payload = json.dumps(body).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, format: str, *args: object) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}", state
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def _evaluate(evaluator: PisamaEvaluator) -> None:
    result = evaluator.evaluate(
        specification={"text": "Return the requested result."},
        output={"text": "Requested result."},
    )
    assert result.passed is True


async def _evaluate_async(evaluator: PisamaEvaluator) -> None:
    result = await evaluator.evaluate_async(
        specification={"text": "Return the requested result."},
        output={"text": "Requested result."},
    )
    assert result.passed is True


def test_sync_evaluator_reuses_one_token_for_twelve_evaluations() -> None:
    with _evaluator_server() as (base_url, state):
        with PisamaEvaluator(api_key=_API_KEY, base_url=base_url) as evaluator:
            for _ in range(12):
                _evaluate(evaluator)

    assert state.authentication_count == 1
    assert state.evaluation_count == 12


@pytest.mark.asyncio
async def test_async_evaluator_reuses_one_token_for_twelve_evaluations() -> None:
    with _evaluator_server() as (base_url, state):
        with PisamaEvaluator(api_key=_API_KEY, base_url=base_url) as evaluator:
            for _ in range(12):
                await _evaluate_async(evaluator)

    assert state.authentication_count == 1
    assert state.evaluation_count == 12


def test_evaluator_refreshes_a_token_near_expiry() -> None:
    with _evaluator_server(first_token_ttl=1.0) as (base_url, state):
        with PisamaEvaluator(api_key=_API_KEY, base_url=base_url) as evaluator:
            _evaluate(evaluator)
            _evaluate(evaluator)

    assert state.authentication_count == 2
    assert state.evaluation_count == 2


@pytest.mark.parametrize("use_async", [False, True])
@pytest.mark.asyncio
async def test_evaluator_refreshes_once_after_401_without_logging_token(
    use_async: bool,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG, logger="pisama_agent_sdk.evaluator")
    with _evaluator_server(reject_first_evaluation=True) as (base_url, state):
        with PisamaEvaluator(api_key=_API_KEY, base_url=base_url) as evaluator:
            if use_async:
                await _evaluate_async(evaluator)
            else:
                _evaluate(evaluator)

    assert state.authentication_count == 2
    assert state.evaluation_count == 2
    assert all(token not in caplog.text for token in state.issued_tokens)
