"""Pisama Evaluator — drop-in evaluator for multi-agent harnesses. Thin forwarder.

The real implementation lives in :mod:`pisama.agents.evaluator`. Usage is
unchanged:

    from pisama_agent_sdk import PisamaEvaluator

    evaluator = PisamaEvaluator(api_key="psk_...", base_url="https://api.pisama.ai")

    result = evaluator.evaluate(
        specification={"text": "Build a login page with OAuth"},
        output={"text": generator_output},
    )
    if not result.passed:
        for failure in result.failures:
            print(f"{failure.detector}: {failure.description}")
"""

from pisama.agents.evaluator import EvalFailure, EvalResult, PisamaEvaluator

__all__ = [
    "EvalFailure",
    "EvalResult",
    "PisamaEvaluator",
]
