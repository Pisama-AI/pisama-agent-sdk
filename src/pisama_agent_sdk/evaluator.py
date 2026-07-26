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

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)
DEFAULT_API_URL = "https://api.pisama.ai"

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

    def _authorization_headers(self) -> Dict[str, str]:
        response = self._client.post(
            "/api/v1/auth/token",
            json={"api_key": self.api_key, "scope": "full"},
        )
        response.raise_for_status()
        return {"Authorization": f"Bearer {_parse_access_token(response.json())}"}

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
            token_response = await client.post(
                "/api/v1/auth/token",
                json={"api_key": self.api_key, "scope": "full"},
            )
            token_response.raise_for_status()
            headers = {
                "Authorization": (
                    f"Bearer {_parse_access_token(token_response.json())}"
                )
            }
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
