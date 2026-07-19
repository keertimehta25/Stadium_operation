"""Unit tests for the translator module.

All GenAI API calls are mocked — tests run fully offline.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.translator import (
    _translate_text,
    format_multilingual_output,
    translate_recommendation,
)

SAMPLE_RECOMMENDATION: str = "Please redirect fans from Gate A to Gate D."


# ---------------------------------------------------------------------------
# translate_recommendation
# ---------------------------------------------------------------------------


class TestTranslateRecommendation:
    """Tests for multi-language translation."""

    @patch("src.translator._translate_text")
    def test_always_includes_english(self, mock_translate: MagicMock) -> None:
        """English should always be present, even without API calls."""
        mock_translate.return_value = "Traducción de ejemplo."
        result: dict[str, str] = translate_recommendation(SAMPLE_RECOMMENDATION)
        assert "English" in result
        assert result["English"] == SAMPLE_RECOMMENDATION

    @patch("src.translator._translate_text")
    def test_includes_secondary_languages(self, mock_translate: MagicMock) -> None:
        """Should attempt Spanish and French translations."""
        mock_translate.return_value = "Translated text."
        result: dict[str, str] = translate_recommendation(SAMPLE_RECOMMENDATION)
        assert "Spanish" in result
        assert "French" in result

    @patch(
        "src.translator._translate_text",
        side_effect=RuntimeError("API error"),
    )
    def test_graceful_on_translation_failure(self, mock_translate: MagicMock) -> None:
        """If translation fails, English must still be returned."""
        result: dict[str, str] = translate_recommendation(SAMPLE_RECOMMENDATION)
        assert "English" in result
        assert len(result) >= 1

    @patch("src.translator._translate_text")
    def test_does_not_translate_english_to_english(self, mock_translate: MagicMock) -> None:
        """Should not call the API to translate English → English."""
        mock_translate.return_value = "Dummy."
        translate_recommendation(SAMPLE_RECOMMENDATION)
        for call_args in mock_translate.call_args_list:
            assert call_args[0][1] != "English"


# ---------------------------------------------------------------------------
# format_multilingual_output
# ---------------------------------------------------------------------------


class TestFormatMultilingualOutput:
    """Tests for terminal formatting."""

    def test_contains_language_headers(self) -> None:
        """Each language should appear as a section header."""
        translations: dict[str, str] = {
            "English": "Go to Gate D.",
            "Spanish": "Ve a la Puerta D.",
        }
        output: str = format_multilingual_output(translations)
        assert "English" in output
        assert "Spanish" in output

    def test_contains_all_texts(self) -> None:
        """All translated texts should appear in the output."""
        translations: dict[str, str] = {
            "English": "Go to Gate D.",
            "French": "Allez à la Porte D.",
        }
        output: str = format_multilingual_output(translations)
        assert "Go to Gate D." in output
        assert "Allez à la Porte D." in output

    def test_empty_translations(self) -> None:
        """Empty dict should produce empty string."""
        output: str = format_multilingual_output({})
        assert output == ""


class TestTranslateTextDelegation:
    """_translate_text builds the prompt then delegates to genai_client.generate."""

    @patch("src.translator.generate")
    def test_delegates_to_shared_generate(self, mock_generate) -> None:
        mock_generate.return_value = "Ve a la Puerta D."

        result = _translate_text("Go to Gate D.", "Spanish")
        assert result == "Ve a la Puerta D."
        (prompt,), _ = mock_generate.call_args
        assert "Go to Gate D." in prompt
        assert "Spanish" in prompt

    @patch("src.translator.generate", side_effect=RuntimeError("empty"))
    def test_raises_with_language_in_message(self, _mock_generate) -> None:
        try:
            _translate_text("Go to Gate D.", "Spanish")
            assert False, "expected RuntimeError"
        except RuntimeError as exc:
            assert "Spanish" in str(exc)
