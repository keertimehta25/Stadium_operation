"""Single shared entry point for calling the Gemini API.

Every GenAI-backed assistant (recommender, navigation, accessibility,
translator) used to carry its own copy of "build a client, call
generate_content, validate the response, strip it" — four modules,
one boilerplate block. That logic now lives in exactly one place.

Each assistant module still defines its own thin `_call_genai` (or
`_translate_text`) wrapper around `generate()`. That's deliberate, not
leftover duplication: it keeps each module's own fallback/error-handling
logic — which genuinely does differ per module — easy to read in
context, and keeps each module mockable at its own boundary in tests
without reaching into a shared module. Only the part that was truly
identical (the actual API call) has been de-duplicated.
"""

from __future__ import annotations

from typing import Any

from google import genai

from src.config import GENAI_MODEL, get_api_key


def generate(prompt: str) -> str:
    """Send *prompt* to the Gemini API and return the response text.

    Args:
        prompt: The fully formatted prompt.

    Returns:
        The model's text response, stripped of leading/trailing whitespace.

    Raises:
        RuntimeError: If the API returns an empty or unusable response.
    """
    client: Any = genai.Client(api_key=get_api_key())
    response: Any = client.models.generate_content(
        model=GENAI_MODEL,
        contents=prompt,
    )

    if not response or not response.text:
        raise RuntimeError("Gemini API returned an empty response.")

    return response.text.strip()
