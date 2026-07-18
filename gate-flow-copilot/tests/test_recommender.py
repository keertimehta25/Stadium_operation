"""Unit tests for the recommender module.

All GenAI API calls are mocked — tests run fully offline.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.config import GATES
from src.crowd_simulator import GateStatus
from src.recommender import (
    _call_genai,
    _state_fingerprint,
    build_prompt,
    clear_cache,
    fallback_recommendation,
    get_recommendation,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def low_density_statuses() -> list[GateStatus]:
    """All gates at comfortable (low) density."""
    return [GateStatus(gate=g, density_pct=25.0) for g in GATES]


@pytest.fixture()
def mixed_density_statuses() -> list[GateStatus]:
    """Mix of congested and low-density gates."""
    densities = [85.0, 30.0, 75.0, 20.0, 90.0, 15.0]
    return [GateStatus(gate=g, density_pct=d) for g, d in zip(GATES, densities)]


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    """Ensure a fresh cache for every test."""
    clear_cache()


# ---------------------------------------------------------------------------
# build_prompt
# ---------------------------------------------------------------------------


class TestBuildPrompt:
    """Tests for prompt construction."""

    def test_contains_stadium_name(self, low_density_statuses: list[GateStatus]) -> None:
        """Prompt should mention the stadium."""
        prompt: str = build_prompt(low_density_statuses)
        assert "MetLife Stadium" in prompt

    def test_contains_all_gates(self, low_density_statuses: list[GateStatus]) -> None:
        """Every configured gate should appear in the prompt."""
        prompt: str = build_prompt(low_density_statuses)
        for gate in GATES:
            assert gate.name in prompt

    def test_contains_density_values(self, mixed_density_statuses: list[GateStatus]) -> None:
        """Prompt should include numeric density percentages."""
        prompt: str = build_prompt(mixed_density_statuses)
        assert "85.0" in prompt
        assert "30.0" in prompt

    def test_asks_for_reasoning(self, low_density_statuses: list[GateStatus]) -> None:
        """Prompt should request reasoning in the recommendation."""
        prompt: str = build_prompt(low_density_statuses)
        assert "why" in prompt.lower()


# ---------------------------------------------------------------------------
# _state_fingerprint
# ---------------------------------------------------------------------------


class TestStateFingerprint:
    """Tests for caching fingerprint."""

    def test_same_input_same_hash(self, low_density_statuses: list[GateStatus]) -> None:
        """Identical statuses should produce identical fingerprints."""
        fp_a = _state_fingerprint(low_density_statuses)
        fp_b = _state_fingerprint(low_density_statuses)
        assert fp_a == fp_b

    def test_different_input_different_hash(
        self,
        low_density_statuses: list[GateStatus],
        mixed_density_statuses: list[GateStatus],
    ) -> None:
        """Different statuses should produce different fingerprints."""
        fp_a = _state_fingerprint(low_density_statuses)
        fp_b = _state_fingerprint(mixed_density_statuses)
        assert fp_a != fp_b


# ---------------------------------------------------------------------------
# fallback_recommendation
# ---------------------------------------------------------------------------


class TestFallbackRecommendation:
    """Tests for the rule-based fallback."""

    def test_no_congestion_says_ok(self, low_density_statuses: list[GateStatus]) -> None:
        """When nothing is congested, say so."""
        result: str = fallback_recommendation(low_density_statuses)
        assert "no redirection" in result.lower()

    def test_congested_lists_gates(self, mixed_density_statuses: list[GateStatus]) -> None:
        """Congested gates should be named in the fallback."""
        result: str = fallback_recommendation(mixed_density_statuses)
        assert "Gate A" in result  # 85 % → congested

    def test_suggests_redirect_target(self, mixed_density_statuses: list[GateStatus]) -> None:
        """Low-density gates should be suggested as redirect targets."""
        result: str = fallback_recommendation(mixed_density_statuses)
        assert "redirect" in result.lower()


# ---------------------------------------------------------------------------
# get_recommendation (with mocked API)
# ---------------------------------------------------------------------------


class TestGetRecommendation:
    """Tests for the main recommendation function (API mocked)."""

    @patch("src.recommender._call_genai")
    def test_returns_api_response(
        self,
        mock_genai: MagicMock,
        low_density_statuses: list[GateStatus],
    ) -> None:
        """Should return the GenAI response when the API succeeds."""
        mock_genai.return_value = "Redirect fans from Gate A to Gate D."
        result: str = get_recommendation(low_density_statuses)
        assert "Gate A" in result or "Gate D" in result
        mock_genai.assert_called_once()

    @patch("src.recommender._call_genai")
    def test_caches_result(
        self,
        mock_genai: MagicMock,
        low_density_statuses: list[GateStatus],
    ) -> None:
        """Second call with same state should hit cache, not API."""
        mock_genai.return_value = "Use Gate B."
        get_recommendation(low_density_statuses)
        get_recommendation(low_density_statuses)
        mock_genai.assert_called_once()

    @patch("src.recommender._call_genai", side_effect=RuntimeError("API down"))
    def test_fallback_on_api_failure(
        self,
        mock_genai: MagicMock,
        mixed_density_statuses: list[GateStatus],
    ) -> None:
        """Should return fallback text when the API raises."""
        result: str = get_recommendation(mixed_density_statuses)
        assert "rule-based fallback" in result.lower()

    @patch("src.recommender._call_genai", side_effect=Exception("Unexpected"))
    def test_never_crashes(
        self,
        mock_genai: MagicMock,
        low_density_statuses: list[GateStatus],
    ) -> None:
        """Function must never raise, regardless of error type."""
        result: str = get_recommendation(low_density_statuses)
        assert isinstance(result, str)
        assert len(result) > 0


class TestCallGenaiClient:
    """Tests for _call_genai's direct genai.Client interaction."""

    @patch("src.recommender.genai.Client")
    def test_returns_stripped_text_on_success(self, mock_client_cls, monkeypatch) -> None:
        monkeypatch.setenv("GENAI_API_KEY", "test-key")
        mock_response = MagicMock()
        mock_response.text = "  Redirect fans to Gate D.  "
        mock_client_cls.return_value.models.generate_content.return_value = mock_response

        assert _call_genai("some prompt") == "Redirect fans to Gate D."

    @patch("src.recommender.genai.Client")
    def test_raises_on_empty_response(self, mock_client_cls, monkeypatch) -> None:
        monkeypatch.setenv("GENAI_API_KEY", "test-key")
        mock_response = MagicMock()
        mock_response.text = ""
        mock_client_cls.return_value.models.generate_content.return_value = mock_response

        with pytest.raises(RuntimeError):
            _call_genai("some prompt")
