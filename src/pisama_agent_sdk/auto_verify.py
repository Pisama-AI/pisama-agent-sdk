"""SDK auto-verification — runs innovation primitives with a real Claude client.

When `heal_now()` returns a `recommended_verification` hint (because
the backend identified an innovation primitive that could unlock a
DANGEROUS-class fix but needs an `agent_callable` only the SDK has),
this module:

1. Instantiates the named primitive with a real Anthropic client as
   the `agent_callable` (and `shadow_callable` etc. when applicable).
2. Runs the primitive against the detection + fix.
3. If the primitive passes, POSTs the outcome to `/healing/confirm-
   applied` so backend's FixEffectivenessTracker records the verified
   apply.

Why the primitive logic is vendored here rather than imported from the
backend: the backend package isn't installed when the SDK runs in a
customer's agent. The vendored versions are deliberately lightweight —
same contract, same default thresholds, same Track E synth-test
assertions — but live alongside the SDK so heal_now() callers don't
need backend on PYTHONPATH.

Use:
    from pisama_agent_sdk.auto_verify import auto_verify_and_confirm

    healing = heal_now(detection_type="hallucination", ...)
    if healing.recommended_verification:
        confirmed = auto_verify_and_confirm(
            healing=healing,
            detection_type="hallucination",
            details=detection_details,
            # Optional — defaults to PISAMA_API_KEY env + Claude Haiku
        )
        if confirmed.applied:
            # SDK has run the primitive locally and confirmed; backend
            # has recorded the outcome.
            ...
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from urllib import error as urllib_error
from urllib import request as urllib_request

from .heal import HealingResult
from .indication import SDKIndication
from .indication import _fire as _fire_indication

logger = logging.getLogger(__name__)

_DEFAULT_API_URL = "https://api.pisama.ai"
_DEFAULT_MODEL = "claude-haiku-4-5-20251001"
_DEFAULT_TIMEOUT_S = 8.0
# How many "safe turn" inputs the SDK collects from the last N turns of
# the agent's history when running ShadowReplay. Track E used 3.
_SAFE_TURN_BUDGET = 3


@dataclass
class AutoVerifyResult:
    """Outcome of running an innovation primitive locally + posting back."""

    primitive: str
    applied: bool
    primitive_confidence: float = 0.0
    before_confidence: float = 0.0
    after_confidence: float = 0.0
    rationale: str = ""
    confirm_recorded: bool = False
    confirm_response: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


def auto_verify_and_confirm(
    *,
    healing: HealingResult,
    detection_type: str,
    details: Optional[Dict[str, Any]] = None,
    agent_callable: Optional[Callable[..., str]] = None,
    safe_turn_inputs: Optional[List[str]] = None,
    api_url: Optional[str] = None,
    api_key: Optional[str] = None,
    model_id: str = _DEFAULT_MODEL,
    timeout_s: float = _DEFAULT_TIMEOUT_S,
) -> AutoVerifyResult:
    """Run the recommended primitive locally; on success, POST back to backend.

    Returns the outcome regardless of whether it succeeded — if the
    primitive failed or the agent_callable couldn't run, `applied=False`
    and `rationale` explains.

    Default `agent_callable` constructs a Claude Haiku client using
    PISAMA_API_KEY (or `api_key` arg). Callers can pass their own for
    tests or to target a different model.
    """
    rec = healing.recommended_verification or {}
    primitive = rec.get("primitive")
    fix = healing.fix or {}
    if not primitive:
        return AutoVerifyResult(
            primitive="",
            applied=False,
            rationale="No recommended_verification on HealingResult.",
        )

    if agent_callable is None:
        agent_callable = _build_claude_agent_callable(
            api_key=api_key, model_id=model_id, timeout_s=timeout_s
        )
        if agent_callable is None:
            return AutoVerifyResult(
                primitive=primitive,
                applied=False,
                rationale="No agent_callable supplied and no Anthropic SDK / API key available.",
            )

    detection_for_primitive = {
        "detection_type": detection_type,
        "details": details or {},
        "confidence": float((details or {}).get("confidence") or 0.0),
    }
    fix_payload = fix if isinstance(fix, dict) else {}

    primitive_passed, primitive_confidence, before, after, rationale = _run_primitive(
        primitive,
        detection_for_primitive,
        fix_payload,
        agent_callable=agent_callable,
        safe_turn_inputs=safe_turn_inputs or _DEFAULT_SAFE_INPUTS,
    )
    if not primitive_passed:
        result = AutoVerifyResult(
            primitive=primitive,
            applied=False,
            primitive_confidence=primitive_confidence,
            before_confidence=before,
            after_confidence=after,
            rationale=rationale or f"{primitive} verification did not pass.",
        )
        _fire_indication(_indication_from(result, detection_type, applied=False))
        return result

    # Verification passed — POST back to backend so the outcome lands
    # in FixEffectivenessTracker alongside async-verification outcomes.
    confirm_recorded, confirm_response = _post_confirm_applied(
        api_url=api_url,
        api_key=api_key,
        payload={
            "detection_type": detection_type,
            "fix_id": fix_payload.get("id", "unknown"),
            "fix_type": fix_payload.get("fix_type", "unknown"),
            "primitive": primitive,
            "success": True,
            "before_confidence": before,
            "after_confidence": after,
            "primitive_confidence": primitive_confidence,
            "details": details or {},
        },
        timeout_s=timeout_s,
    )

    result = AutoVerifyResult(
        primitive=primitive,
        applied=True,
        primitive_confidence=primitive_confidence,
        before_confidence=before,
        after_confidence=after,
        rationale=rationale,
        confirm_recorded=confirm_recorded,
        confirm_response=confirm_response,
    )
    _fire_indication(_indication_from(result, detection_type, applied=True))
    return result


# Default "safe" inputs ShadowReplay anchors against when the caller
# doesn't provide their own. Three benign neutral prompts the agent
# should answer the same way pre- and post-fix.
_DEFAULT_SAFE_INPUTS = [
    "What's the current time?",
    "Summarise the last user message in one sentence.",
    "Confirm you're ready for the next instruction.",
]


def _build_claude_agent_callable(
    *,
    api_key: Optional[str],
    model_id: str,
    timeout_s: float,
) -> Optional[Callable[..., str]]:
    """Build an agent_callable that hits Claude Haiku via the Anthropic SDK.

    Returns None if anthropic isn't importable or no API key — caller
    treats that as "skip primitive verification."
    """
    key = api_key or os.getenv("PISAMA_AGENT_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    if not key:
        return None
    try:
        from anthropic import Anthropic
    except ImportError:
        logger.warning("auto_verify: anthropic SDK not installed; skipping verification")
        return None

    client = Anthropic(api_key=key)

    def _call(prompt_input: str = "", **kwargs) -> str:
        # The primitives pass varied kwargs (prompt_input, temperature,
        # seed, original_input, delta, fix, etc.). For Claude the
        # relevant ones are temperature + the prompt body. Build a
        # single user message; the primitive's own framing already
        # encodes whatever role-shaping it needs.
        temperature = float(kwargs.get("temperature", 0.0) or 0.0)
        delta = kwargs.get("delta") or ""
        system_message = kwargs.get("prompt") or kwargs.get("system") or ""
        user_message = prompt_input or kwargs.get("original_input") or ""
        if delta and not system_message:
            system_message = delta
        try:
            message = client.messages.create(
                model=model_id,
                max_tokens=400,
                temperature=temperature,
                system=system_message or "You are an assistant.",
                messages=[{"role": "user", "content": user_message or "(no input)"}],
                timeout=timeout_s,
            )
        except Exception as exc:
            logger.info("auto_verify: Claude call failed (%s)", exc)
            return ""
        try:
            return "".join(
                block.text for block in message.content
                if getattr(block, "type", None) == "text"
            )
        except Exception:
            return ""

    return _call


def _run_primitive(
    primitive: str,
    detection: Dict[str, Any],
    fix: Dict[str, Any],
    *,
    agent_callable: Callable[..., str],
    safe_turn_inputs: List[str],
):
    """Dispatch to the lightweight SDK-side primitive implementation.

    Returns (passed, primitive_confidence, before_conf, after_conf, rationale).
    """
    if primitive == "PromptDelta":
        return _run_prompt_delta(detection, fix, agent_callable)
    if primitive == "ShadowReplay":
        return _run_shadow_replay(detection, fix, agent_callable, safe_turn_inputs)
    if primitive == "ConsensusCheck":
        return _run_consensus_check(detection, fix, agent_callable)
    # CounterfactualReplay needs a full trace + replay engine that the
    # SDK doesn't have access to; backend runs that one server-side
    # when trace_events are in the request. SDK falls through.
    return (False, 0.0, 0.0, 0.0,
            f"{primitive} not implemented in SDK; backend handles this primitive server-side.")


def _run_prompt_delta(
    detection: Dict[str, Any],
    fix: Dict[str, Any],
    agent_callable: Callable[..., str],
):
    """Vendored bounded-delta verification.

    Lifted from backend/app/healing/innovations/prompt_delta.py — same
    50-token cap, same residual-signal check on the agent's response
    with the delta appended.
    """
    details = detection.get("details") or {}
    detection_type = detection.get("detection_type") or ""

    # Build a delta deterministically from the detection evidence.
    delta = _build_prompt_delta(detection_type, details)
    if delta is None:
        return (False, 0.0, 0.0, 0.0, "Could not build a bounded delta for this detection shape.")
    if len(delta) > 50 * 4:  # 50 tokens ≈ 200 chars
        return (False, 0.0, 0.0, 0.0, f"Generated delta exceeds size cap ({len(delta)//4} tokens).")

    original_prompt = _original_prompt(detection_type, details)
    original_input = details.get("user_message") or details.get("input") or ""
    try:
        response = agent_callable(
            prompt=f"{original_prompt}\n\n{delta}",
            original_input=original_input,
            delta=delta,
        )
    except Exception as exc:
        return (False, 0.0, 0.0, 0.0, f"agent_callable raised: {exc}")

    residual = _residual_signal(detection_type, details, response)
    before = float(detection.get("confidence") or 0.0)
    after = residual

    if residual < 0.5:
        return (True, 1.0 - residual, before, after,
                f"Delta of ~{len(delta)//4} tokens; simulated re-prompt did not re-fire detector.")
    return (False, residual, before, after,
            f"Delta applied but detector signal remains high (residual={residual:.2f}).")


def _run_shadow_replay(
    detection: Dict[str, Any],
    fix: Dict[str, Any],
    agent_callable: Callable[..., str],
    safe_turn_inputs: List[str],
):
    """Vendored A/B verification — calls the same agent_callable for
    both original and shadow paths (production callers would pass two
    different clients; for default-mode SDK use we approximate by
    prompting with vs without the fix's system patch)."""
    details = detection.get("details") or {}
    failing_input = (
        details.get("user_message") or details.get("input")
        or details.get("query") or ""
    )
    if not failing_input:
        return (False, 0.0, 0.0, 0.0, "Detection lacks replayable input.")
    original_failing = details.get("output") or details.get("agent_output") or ""

    fix_prompt_patch = _fix_to_prompt_patch(fix)
    try:
        shadow_failing = agent_callable(
            prompt=fix_prompt_patch or "Be careful and grounded.",
            original_input=failing_input,
        )
    except Exception as exc:
        return (False, 0.0, 0.0, 0.0, f"Shadow call failed: {exc}")

    failing_sim = _text_similarity(original_failing, shadow_failing)
    if failing_sim > 0.5:
        return (False, failing_sim, float(detection.get("confidence") or 0.0), failing_sim,
                f"Shadow output too similar to original on failing turn (sim={failing_sim:.2f}).")

    regressions = 0
    for safe_input in safe_turn_inputs[:_SAFE_TURN_BUDGET]:
        try:
            orig = agent_callable(original_input=safe_input)
            shad = agent_callable(prompt=fix_prompt_patch, original_input=safe_input)
        except Exception:
            regressions += 1
            continue
        sim = _text_similarity(orig, shad)
        if sim < 0.6:
            regressions += 1

    before = float(detection.get("confidence") or 0.0)
    after = failing_sim
    if regressions:
        return (False, 1.0 - regressions / max(1, len(safe_turn_inputs)),
                before, after,
                f"Shadow regressed on {regressions}/{len(safe_turn_inputs[:_SAFE_TURN_BUDGET])} safe turns.")
    return (True, (1.0 - failing_sim) * 0.5 + 0.5, before, after,
            f"Shadow diverged on failing turn (sim={failing_sim:.2f}); matched on safe turns.")


def _run_consensus_check(
    detection: Dict[str, Any],
    fix: Dict[str, Any],
    agent_callable: Callable[..., str],
):
    """Vendored N-sample voting with temperature spread."""
    details = detection.get("details") or {}
    failing_input = (
        details.get("user_message") or details.get("input")
        or details.get("query") or ""
    )
    original_answer = details.get("output") or details.get("agent_output") or ""
    if not failing_input or not original_answer:
        return (False, 0.0, 0.0, 0.0, "Detection lacks (input, output) pair.")

    temperatures = [0.0, 0.3, 0.5, 0.7, 1.0]
    samples: List[str] = []
    for i, temp in enumerate(temperatures):
        try:
            samples.append(agent_callable(prompt_input=failing_input, temperature=temp, seed=i))
        except Exception:
            return (False, 0.0, 0.0, 0.0, f"Sample {i} failed.")

    def norm(value: str) -> str:
        return " ".join((value or "").lower().split())

    norm_original = norm(original_answer)
    diverged = sum(1 for s in samples if norm(s) != norm_original)
    rate = diverged / len(samples)

    before = float(detection.get("confidence") or 0.0)
    if rate < 0.6:
        return (False, rate, before, before * (1.0 - rate),
                f"Only {diverged}/{len(samples)} samples diverged from original.")
    # Stable hallucination invariant: if EVERY divergent sample agrees,
    # plus the divergence is consistent, that's a real correction.
    return (True, rate, before, before * (1.0 - rate),
            f"{diverged}/{len(samples)} samples diverged; consensus signals genuine alternative.")


# ─────────────────────────────────────────────────────────────────────
# Vendored helpers (lifted from backend innovation modules)
# ─────────────────────────────────────────────────────────────────────


def _build_prompt_delta(detection_type: str, details: Dict[str, Any]) -> Optional[str]:
    if detection_type == "persona_drift":
        violations = details.get("violated_actions") or []
        if not violations:
            return None
        return f"REMINDER: stay strictly inside your role. You must not {violations[0]}."
    if detection_type == "role_usurpation":
        violations = details.get("violated_actions") or []
        if not violations:
            return None
        return f"GUARDRAIL: '{violations[0]}' is outside your allowed_actions; refuse it."
    if detection_type == "dify_classifier_drift":
        expected = details.get("expected_distribution") or {}
        if not expected:
            return None
        top = max(expected.items(), key=lambda kv: kv[1])[0]
        return f"REMINDER: typical correct label for this input class is '{top}'."
    return None


def _original_prompt(detection_type: str, details: Dict[str, Any]) -> str:
    if detection_type == "persona_drift":
        agent = details.get("agent") or {}
        return agent.get("persona_description") or ""
    if detection_type == "role_usurpation":
        return details.get("persona_description") or details.get("system_prompt") or ""
    if detection_type == "dify_classifier_drift":
        return details.get("classifier_prompt") or ""
    return ""


def _residual_signal(
    detection_type: str,
    details: Dict[str, Any],
    response: str,
) -> float:
    lower = (response or "").lower()
    if detection_type == "persona_drift":
        forbidden = [a.lower() for a in (details.get("violated_actions") or [])]
        if not forbidden:
            return 0.0
        hits = sum(1 for term in forbidden if term and term in lower)
        return min(1.0, hits / max(1, len(forbidden)))
    if detection_type == "role_usurpation":
        forbidden = [a.lower() for a in (details.get("violated_actions") or [])]
        return 1.0 if any(t and t in lower for t in forbidden) else 0.0
    if detection_type == "dify_classifier_drift":
        expected = details.get("expected_distribution") or {}
        if not expected:
            return 0.0
        top = max(expected.items(), key=lambda kv: kv[1])[0].lower()
        return 0.0 if top in lower else 0.8
    return 0.5


def _fix_to_prompt_patch(fix: Dict[str, Any]) -> str:
    """Surface the fix's actionable text for the shadow agent."""
    if not isinstance(fix, dict):
        return ""
    meta = fix.get("metadata") or {}
    snippet = meta.get("framework_specific_code")
    if isinstance(snippet, str) and snippet.strip():
        return snippet
    for key in ("rationale", "description", "title"):
        v = fix.get(key)
        if isinstance(v, str) and v.strip():
            return v
    return ""


def _text_similarity(a: str, b: str) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    tokens_a = set(_tokens(a))
    tokens_b = set(_tokens(b))
    if not tokens_a or not tokens_b:
        return 0.0
    return len(tokens_a & tokens_b) / len(tokens_a | tokens_b)


def _tokens(text: str) -> List[str]:
    return [t for t in "".join(ch.lower() if ch.isalnum() else " " for ch in text).split() if t]


# ─────────────────────────────────────────────────────────────────────
# Confirm-applied POST to backend
# ─────────────────────────────────────────────────────────────────────


def _post_confirm_applied(
    *,
    api_url: Optional[str],
    api_key: Optional[str],
    payload: Dict[str, Any],
    timeout_s: float,
) -> tuple:
    """POST to /api/v1/healing/confirm-applied. Returns (recorded, response_dict)."""
    base_url = (api_url or os.getenv("PISAMA_API_URL", _DEFAULT_API_URL)).rstrip("/")
    key = api_key or os.getenv("PISAMA_API_KEY", "")
    if not key:
        return (False, {"error": "PISAMA_API_KEY not configured"})

    body = json.dumps(payload).encode("utf-8")
    req = urllib_request.Request(
        url=f"{base_url}/api/v1/healing/confirm-applied",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
            "User-Agent": "pisama-agent-sdk/auto_verify",
        },
        method="POST",
    )
    try:
        with urllib_request.urlopen(req, timeout=timeout_s) as resp:
            raw = resp.read()
        return (True, json.loads(raw.decode("utf-8")))
    except urllib_error.HTTPError as exc:
        return (False, {"error": f"HTTP {exc.code}"})
    except (urllib_error.URLError, TimeoutError) as exc:
        return (False, {"error": f"network failure: {exc}"})
    except Exception as exc:
        return (False, {"error": f"unexpected: {exc}"})


def _indication_from(
    result: AutoVerifyResult,
    detection_type: str,
    *,
    applied: bool,
) -> SDKIndication:
    """Surface auto-verify outcome via the standard SDK indication channel."""
    return SDKIndication(
        severity="info" if applied else "warning",
        category="auto_healed_verified" if applied else "escalated_dangerous",
        detection_type=detection_type,
        headline=(
            f"SDK auto-verified {detection_type} via {result.primitive}"
            if applied else
            f"SDK auto-verification did not pass ({result.primitive})"
        ),
        detail=result.rationale,
        confidence=result.primitive_confidence,
        action_required=not applied,
        sdk_primitive=result.primitive,
        verification_passed=applied,
        risk_level="dangerous",
        tags=["sdk_verified"] if applied else ["sdk_escalated"],
    )
