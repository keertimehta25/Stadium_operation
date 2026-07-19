"""Multi-language translation for gate-flow recommendations.

Translates the English recommendation into Spanish and French using the
Gemini API, falling back to English-only output on any failure.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from src.config import SUPPORTED_LANGUAGES
from src.genai_client import generate

# Cache of (source_text, target_language) -> translated text. The same
# recommendation string is often requested repeatedly within a short
# window (e.g. the frontend polling /api/status every few seconds while
# gate density hasn't changed enough to alter the recommendation), so
# caching avoids paying for and waiting on a duplicate Gemini call.
# Bounded so a long-running server process can't grow this dict without
# limit as gate states drift over a matchday.
_CACHE_MAX_SIZE = 500
_translation_cache: dict[tuple[str, str], str] = {}


# ---------------------------------------------------------------------------
# Translation helpers
# ---------------------------------------------------------------------------


def _translate_text(text: str, target_language: str) -> str:
    """Translate *text* into *target_language* via the Gemini API.

    Thin per-module wrapper around ``src.genai_client.generate`` — kept
    here (rather than calling the shared helper directly from
    ``translate_recommendation``) so this module builds its own prompt
    and can attach the target language to the error message, while the
    actual API call is de-duplicated in one shared place.

    Args:
        text: The English source text.
        target_language: The language name (e.g. ``"Spanish"``).

    Returns:
        The translated text.

    Raises:
        RuntimeError: If the API returns an empty response.
    """
    prompt: str = (
        f"Translate the following crowd-management recommendation into "
        f"{target_language}. Keep the meaning exact and the language simple "
        f"so a stadium volunteer can understand it easily.\n\n"
        f"---\n{text}\n---"
    )
    try:
        return generate(prompt)
    except RuntimeError as exc:
        raise RuntimeError(f"Gemini API returned an empty response for {target_language}.") from exc


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
            if len(_translation_cache) >= _CACHE_MAX_SIZE:
                _translation_cache.pop(next(iter(_translation_cache)))
            _translation_cache[cache_key] = text
            return language, text
        except Exception:  # pylint: disable=broad-exception-caught
            # Graceful degradation: skip this language on failure. Broad
            # on purpose so one bad translation never blocks the others.
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
