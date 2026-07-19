"""GenAI-powered gate-redirection recommender.

Builds a structured prompt from live gate densities, sends it to the
Google Gemini API, and returns a plain-language recommendation with
reasoning.  Gracefully falls back to a rule-based suggestion on any
API failure.
"""

from __future__ import annotations

import hashlib
import json

from src.config import DENSITY_LOW, DENSITY_MODERATE, STADIUM_NAME
from src.crowd_simulator import GateStatus
from src.genai_client import generate

# ---------------------------------------------------------------------------
# Prompt construction (pure, testable)
# ---------------------------------------------------------------------------


def build_prompt(gate_statuses: list[GateStatus]) -> str:
    """Create a structured prompt describing current gate conditions.

    The prompt asks the model to act as a crowd-management expert and
    return a recommendation with explicit reasoning.

    Args:
        gate_statuses: Current density snapshot for every gate.

    Returns:
        A fully formatted prompt string ready for the GenAI API.
    """
    lines: list[str] = [
        f"You are a crowd-management expert helping a volunteer at {STADIUM_NAME}.",
        "Below are the current gate density readings (0-100 %).\n",
    ]
    for status in gate_statuses:
        lines.append(
            f"  • {status.gate.name} ({status.gate.zone}): "
            f"{status.density_pct:.1f} % — {status.label}"
        )

    lines.append(
        "\nProvide a short, plain-language recommendation for the volunteer. "
        "Include:\n"
        "1. Which gate(s) fans should be redirected FROM (and why).\n"
        "2. Which gate(s) fans should be redirected TO (and why).\n"
        "3. Any additional crowd-safety advice.\n"
        "Keep the language simple — the volunteer may not be a native English speaker."
    )
    return "\n".join(lines)


def _state_fingerprint(gate_statuses: list[GateStatus]) -> str:
    """Return a short hash uniquely identifying a set of gate densities.

    Used for caching: if densities haven't changed we skip the API call.

    Args:
        gate_statuses: Current density snapshot.

    Returns:
        A hex-digest string.
    """
    data: str = json.dumps(
        [(s.gate.name, s.density_pct) for s in gate_statuses],
        sort_keys=True,
    )
    return hashlib.sha256(data.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Rule-based fallback (no API needed)
# ---------------------------------------------------------------------------


def fallback_recommendation(gate_statuses: list[GateStatus]) -> str:
    """Generate a simple rule-based recommendation without calling GenAI.

    This is used when the API is unavailable or returns an error.

    Args:
        gate_statuses: Current density snapshot.

    Returns:
        A plain-language fallback recommendation string.
    """
    congested: list[GateStatus] = [s for s in gate_statuses if s.density_pct > DENSITY_MODERATE]
    available: list[GateStatus] = [s for s in gate_statuses if s.density_pct <= DENSITY_LOW]

    if not congested:
        return (
            "All gates are operating within comfortable levels. "
            "No redirection is needed right now."
        )

    parts: list[str] = ["⚠️  Some gates are congested:\n"]
    for status in congested:
        parts.append(
            f"  • {status.gate.name} is at {status.density_pct:.0f} % "
            f"(zone: {status.gate.zone})."
        )

    if available:
        names: str = ", ".join(s.gate.name for s in available)
        parts.append(f"\n→ Please redirect fans to: {names}.")
    else:
        parts.append(
            "\n→ No gates are at low density. Ask your coordinator for additional guidance."
        )

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# GenAI API call (cached per gate-state fingerprint)
# ---------------------------------------------------------------------------

# Module-level cache: maps state fingerprint → recommendation text.
# Bounded so a long-running server process (gate densities change on
# every simulation tick) can't grow this dict without limit.
_CACHE_MAX_SIZE = 500
_recommendation_cache: dict[str, str] = {}


def _call_genai(prompt: str) -> str:
    """Send *prompt* to the Gemini API and return the response text.

    Thin per-module wrapper around ``src.genai_client.generate`` — kept
    here (rather than calling the shared helper directly from
    ``get_recommendation``) so this module's own fallback logic can
    mock/patch at its own boundary, same as before.

    Args:
        prompt: The fully formatted prompt.

    Returns:
        The model's text response.

    Raises:
        RuntimeError: If the API returns an empty or unusable response.
    """
    return generate(prompt)


def get_recommendation(gate_statuses: list[GateStatus]) -> str:
    """Return a GenAI-generated crowd-redirection recommendation.

    Results are cached per gate-state fingerprint so repeated calls with
    identical densities do not trigger extra API requests.

    On any failure (network, auth, quota), a rule-based fallback is
    returned instead — the function never raises.

    Args:
        gate_statuses: Current density snapshot for every gate.

    Returns:
        A plain-language recommendation string.
    """
    fingerprint: str = _state_fingerprint(gate_statuses)

    # Return cached result if gate state is unchanged
    if fingerprint in _recommendation_cache:
        return _recommendation_cache[fingerprint]

    prompt: str = build_prompt(gate_statuses)

    try:
        recommendation: str = _call_genai(prompt)
    except Exception:  # pylint: disable=broad-exception-caught
        # Graceful degradation — never crash on API issues. Broad on
        # purpose: any GenAI failure mode should fall back, not surface.
        recommendation = (
            "[AI unavailable — using rule-based fallback]\n\n"
            + fallback_recommendation(gate_statuses)
        )

    if len(_recommendation_cache) >= _CACHE_MAX_SIZE:
        _recommendation_cache.pop(next(iter(_recommendation_cache)))
    _recommendation_cache[fingerprint] = recommendation
    return recommendation


def clear_cache() -> None:
    """Clear the recommendation cache (useful between simulation ticks)."""
    _recommendation_cache.clear()
