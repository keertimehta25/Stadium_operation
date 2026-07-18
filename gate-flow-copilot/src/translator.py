"""Multi-language translation for gate-flow recommendations.

Translates the English recommendation into Spanish and French using the
Gemini API, falling back to English-only output on any failure.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any

from google import genai

from src.config import SUPPORTED_LANGUAGES, get_api_key

# Cache of (source_text, target_language) -> translated text. The same
# recommendation string is often requested repeatedly within a short
# window (e.g. the frontend polling /api/status every few seconds while
# gate density hasn't changed enough to alter the recommendation), so
# caching avoids paying for and waiting on a duplicate Gemini call.
_translation_cache: dict[tuple[str, str], str] = {}


# ---------------------------------------------------------------------------
# Translation helpers
# ---------------------------------------------------------------------------

def _translate_text(text: str, target_language: str) -> str:
    """Translate *text* into *target_language* via the Gemini API.

    Args:
        text: The English source text.
        target_language: The language name (e.g. ``"Spanish"``).

    Returns:
        The translated text.

    Raises:
        RuntimeError: If the API returns an empty response.
    """
    client: Any = genai.Client(api_key=get_api_key())

    prompt: str = (
        f"Translate the following crowd-management recommendation into "
        f"{target_language}. Keep the meaning exact and the language simple "
        f"so a stadium volunteer can understand it easily.\n\n"
        f"---\n{text}\n---"
    )
    response: Any = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )

    if not response or not response.text:
        raise RuntimeError(
            f"Gemini API returned an empty response for {target_language}."
        )

    return response.text.strip()


def translate_recommendation(
    recommendation: str,
) -> dict[str, str]:
    """Return the recommendation in all supported languages.

    Always includes the original English text.  If translation to a
    secondary language fails, that language is omitted silently rather
    than crashing the entire output.

    Args:
        recommendation: The English recommendation string.

    Returns:
        A dict mapping language name → translated text.
        At minimum contains ``{"English": recommendation}``.
    """
    translations: dict[str, str] = {"English": recommendation}
    languages = [lang for lang in SUPPORTED_LANGUAGES if lang != "English"]

    def _get(language: str) -> tuple[str, str | None]:
        cache_key = (recommendation, language)
        if cache_key in _translation_cache:
            return language, _translation_cache[cache_key]
        try:
            text = _translate_text(recommendation, language)
            _translation_cache[cache_key] = text
            return language, text
        except Exception:
            # Graceful degradation: skip this language on failure
            return language, None

    # Run the (uncached) API calls concurrently instead of sequentially —
    # this roughly halves latency when translating into 2+ languages.
    if languages:
        with ThreadPoolExecutor(max_workers=len(languages)) as executor:
            for language, text in executor.map(_get, languages):
                if text is not None:
                    translations[language] = text

    return translations


def format_multilingual_output(translations: dict[str, str]) -> str:
    """Format translated recommendations for terminal display.

    Each language block is preceded by a header and separated by a
    horizontal rule for readability.

    Args:
        translations: Mapping of language name → translated text.

    Returns:
        A single formatted string ready for printing.
    """
    sections: list[str] = []
    for language, text in translations.items():
        sections.append(f"── {language} {'─' * (40 - len(language))}\n{text}")
    return "\n\n".join(sections)
