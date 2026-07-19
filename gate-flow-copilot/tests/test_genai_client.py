"""Unit tests for the shared genai_client.generate helper.

All GenAI API calls are mocked — tests run fully offline. This replaces
four near-identical "direct genai.Client interaction" test classes that
used to be duplicated across test_recommender.py, test_navigation_assistant.py,
test_accessibility_assistant.py, and test_translator.py, one per module
that used to have its own copy of the same API-call logic.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.genai_client import generate


class TestGenerate:
    """Tests for generate's direct genai.Client interaction."""

    @patch("src.genai_client.genai.Client")
    def test_returns_stripped_text_on_success(self, mock_client_cls, monkeypatch) -> None:
        monkeypatch.setenv("GENAI_API_KEY", "test-key")
        mock_response = MagicMock()
        mock_response.text = "  Redirect fans to Gate D.  "
        mock_client_cls.return_value.models.generate_content.return_value = mock_response

        assert generate("some prompt") == "Redirect fans to Gate D."

    @patch("src.genai_client.genai.Client")
    def test_raises_on_empty_response(self, mock_client_cls, monkeypatch) -> None:
        monkeypatch.setenv("GENAI_API_KEY", "test-key")
        mock_response = MagicMock()
        mock_response.text = ""
        mock_client_cls.return_value.models.generate_content.return_value = mock_response

        with pytest.raises(RuntimeError):
            generate("some prompt")

    @patch("src.genai_client.genai.Client")
    def test_raises_on_none_response(self, mock_client_cls, monkeypatch) -> None:
        monkeypatch.setenv("GENAI_API_KEY", "test-key")
        mock_client_cls.return_value.models.generate_content.return_value = None

        with pytest.raises(RuntimeError):
            generate("some prompt")

    @patch("src.genai_client.genai.Client")
    def test_passes_prompt_and_model_through(self, mock_client_cls, monkeypatch) -> None:
        monkeypatch.setenv("GENAI_API_KEY", "test-key")
        mock_response = MagicMock()
        mock_response.text = "ok"
        mock_client_cls.return_value.models.generate_content.return_value = mock_response

        generate("a specific prompt")

        _, kwargs = mock_client_cls.return_value.models.generate_content.call_args
        assert kwargs["contents"] == "a specific prompt"
        assert kwargs["model"]
