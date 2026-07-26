"""Pisama Evaluator — drop-in evaluator for multi-agent harnesses.

Usage:
    from pisama_agent_sdk import PisamaEvaluator

    evaluator = PisamaEvaluator(api_key="pisama_...")

    result = evaluator.evaluate(
        specification={"text": "Build a login page with OAuth"},
        output={"text": generator_output},
    )
    if not result.passed:
        for failure in result.failures:
            print(f"{failure.detector}: {failure.description}")
"""

import asyncio
import base64
import json
import logging
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)
DEFAULT_API_URL = "https://api.pisama.ai"
_TOKEN_REFRESH_SKEW_SECONDS = 30.0
_TOKEN_FALLBACK_TTL_SECONDS = 300.0

try:
    import httpx

    _HTTPX_AVAILABLE = True
except ImportError:
    _HTTPX_AVAILABLE = False


def _parse_access_token(payload: Any) -> str:
    token = payload.get("access_token") if isinstance(payload, dict) else None
    if not isinstance(token, str) or not token.strip():
        raise ValueError(
            "Pisama authentication response did not include a valid access_token"
        )
    return token.strip()


def _access_token_expiry(payload: Any, token: str) -> float:
    """Return a conservative Unix expiry for a token response.

    The Pisama token endpoint returns a JWT whose ``exp`` claim is the
    authoritative expiry. ``expires_in`` is also accepted for compatible
    deployments. Opaque tokens get a short fallback TTL and are still
    refreshed immediately when the API returns 401.
    """
    try:
        encoded_payload = token.split(".")[1]
        padding = "=" * (-len(encoded_payload) % 4)
        claims = json.loads(
            base64.urlsafe_b64decode(encoded_payload + padding).decode("utf-8")
        )
        expires_at = claims.get("exp") if isinstance(claims, dict) else None
        if (
            isinstance(expires_at, (int, float))
            and not isinstance(expires_at, bool)
            and expires_at > 0
        ):
            return float(expires_at)
    except (IndexError, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        pass

    expires_in = payload.get("expires_in") if isinstance(payload, dict) else None
    if (
        isinstance(expires_in, (int, float))
        and not isinstance(expires_in, bool)
        and expires_in > 0
    ):
        return time.time() + float(expires_in)
    return time.time() + _TOKEN_FALLBACK_TTL_SECONDS


@dataclass
class EvalFailure:
    detector: str
    confidence: float
    severity: str
    title: str
    description: str
    suggested_fix: Optional[str] = None


@dataclass
class EvalResult:
    passed: bool
    score: float
    failures: List[EvalFailure]
    suggestions: List[str]
    detectors_run: List[str]
    evaluation_time_ms: int


def _build_evaluation_payload(
    specification: Dict[str, Any],
    output: Dict[str, Any],
    agent_role: str,
    detectors: Optional[List[str]],
    context_limit: Optional[int],
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "specification": specification,
        "output": output,
        "agent_role": agent_role,
    }
    if detectors:
        payload["detectors"] = detectors
    if context_limit:
        payload["context_limit"] = context_limit
    return payload


def _parse_evaluation_result(data: Dict[str, Any]) -> EvalResult:
    failures = [
        EvalFailure(
            detector=failure["detector"],
            confidence=failure["confidence"],
            severity=failure["severity"],
            title=failure["title"],
            description=failure["description"],
            suggested_fix=failure.get("suggested_fix"),
        )
        for failure in data.get("failures", [])
    ]
    return EvalResult(
        passed=data["passed"],
        score=data["score"],
        failures=failures,
        suggestions=data.get("suggestions", []),
        detectors_run=data.get("detectors_run", []),
        evaluation_time_ms=data.get("evaluation_time_ms", 0),
    )


class PisamaEvaluator:
    """Client for the Pisama evaluation API.

    Args:
        api_key: Pisama API key (pisama_...)
        base_url: Backend URL (default: https://api.pisama.ai)
        timeout: Request timeout in seconds
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = DEFAULT_API_URL,
        timeout: float = 30.0,
    ):
        if not _HTTPX_AVAILABLE:
            raise ImportError(
                "httpx is required for PisamaEvaluator: "
                'pip install "pisama-agent-sdk[evaluator]"'
            )
        if not api_key.strip():
            raise ValueError("api_key must be a non-empty Pisama API key")

        self.api_key = api_key.strip()
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={"Content-Type": "application/json"},
            timeout=timeout,
        )
        self._access_token: Optional[str] = None
        self._access_token_expires_at = 0.0
        self._token_state_lock = threading.Lock()
        self._authentication_lock = threading.Lock()

    def _cached_access_token(self) -> Optional[str]:
        with self._token_state_lock:
            if (
                self._access_token
                and self._access_token_expires_at
                > time.time() + _TOKEN_REFRESH_SKEW_SECONDS
            ):
                return self._access_token
        return None

    def _cache_access_token(self, payload: Any) -> str:
        token = _parse_access_token(payload)
        expires_at = _access_token_expiry(payload, token)
        with self._token_state_lock:
            self._access_token = token
            self._access_token_expires_at = expires_at
        return token

    def _invalidate_access_token(self, token: Optional[str] = None) -> None:
        """Discard ``token`` without clearing a concurrent newer credential."""
        with self._token_state_lock:
            if token is None or token == self._access_token:
                self._access_token = None
                self._access_token_expires_at = 0.0

    def _authorization_headers(self) -> Dict[str, str]:
        token = self._cached_access_token()
        if token is None:
            with self._authentication_lock:
                token = self._cached_access_token()
                if token is None:
                    response = self._client.post(
                        "/api/v1/auth/token",
                        json={"api_key": self.api_key, "scope": "full"},
                    )
                    response.raise_for_status()
                    token = self._cache_access_token(response.json())
        return {"Authorization": f"Bearer {token}"}

    @staticmethod
    def _header_token(headers: Dict[str, str]) -> str:
        return headers["Authorization"].removeprefix("Bearer ")

    def evaluate(
        self,
        specification: Dict[str, Any],
        output: Dict[str, Any],
        agent_role: str = "generator",
        detectors: Optional[List[str]] = None,
        context_limit: Optional[int] = None,
    ) -> EvalResult:
        """Evaluate generator output against a specification.

        Args:
            specification: Sprint contract or task spec.
            output: Generator output to evaluate.
            agent_role: Role of the producing agent (generator/evaluator/planner).
            detectors: Specific detectors to run (default: auto-select).
            context_limit: Model context window for pressure detection.

        Returns:
            EvalResult with pass/fail verdict and failure details.
        """
        payload = _build_evaluation_payload(
            specification,
            output,
            agent_role,
            detectors,
            context_limit,
        )

        headers = self._authorization_headers()
        response = self._client.post(
            "/api/v1/evaluate",
            json=payload,
            headers=headers,
        )
        if response.status_code == 401:
            self._invalidate_access_token(self._header_token(headers))
            response = self._client.post(
                "/api/v1/evaluate",
                json=payload,
                headers=self._authorization_headers(),
            )
        response.raise_for_status()
        return _parse_evaluation_result(response.json())

    async def evaluate_async(
        self,
        specification: Dict[str, Any],
        output: Dict[str, Any],
        agent_role: str = "generator",
        detectors: Optional[List[str]] = None,
        context_limit: Optional[int] = None,
    ) -> EvalResult:
        """Async version of evaluate()."""
        payload = _build_evaluation_payload(
            specification,
            output,
            agent_role,
            detectors,
            context_limit,
        )

        async with httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Content-Type": "application/json"},
            timeout=self.timeout,
        ) as client:
            headers = await asyncio.to_thread(self._authorization_headers)
            response = await client.post(
                "/api/v1/evaluate",
                json=payload,
                headers=headers,
            )
            if response.status_code == 401:
                self._invalidate_access_token(self._header_token(headers))
                headers = await asyncio.to_thread(self._authorization_headers)
                response = await client.post(
                    "/api/v1/evaluate",
                    json=payload,
                    headers=headers,
                )
            response.raise_for_status()
            return _parse_evaluation_result(response.json())

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def __enter__(self) -> "PisamaEvaluator":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
