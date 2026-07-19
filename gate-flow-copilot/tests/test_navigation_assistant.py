"""Unit tests for the navigation assistant module.

All GenAI API calls are mocked — tests run fully offline.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src.crowd_simulator import simulate_gate_densities
from src.navigation_assistant import (
    _call_genai,
    _congestion_note,
    build_prompt,
    fallback_navigation,
    find_pois,
    get_directions,
)


class TestFindPois:
    """Tests for point-of-interest lookup."""

    def test_returns_all_by_default(self) -> None:
        assert len(find_pois()) > 0

    def test_filters_by_category(self) -> None:
        results = find_pois("medical")
        assert results
        assert all(p.category == "medical" for p in results)

    def test_unknown_category_returns_empty(self) -> None:
        assert find_pois("teleporter") == []


class TestCongestionNote:
    """Tests for the live-congestion note used by navigation guidance."""

    def test_no_gate_statuses_returns_empty(self) -> None:
        assert _congestion_note("near Gate A, East", None) == ""

    def test_matching_gate_returns_note(self) -> None:
        statuses = simulate_gate_densities(minutes_to_kickoff=30, seed=1)
        gate_name = statuses[0].gate.name
        note = _congestion_note(f"near {gate_name}, East", statuses)
        assert gate_name in note
        assert "%" in note

    def test_no_matching_gate_returns_empty(self) -> None:
        statuses = simulate_gate_densities(minutes_to_kickoff=30, seed=1)
        assert _congestion_note("near Gate Z, Nowhere", statuses) == ""


class TestBuildPromptWithLiveData:
    """Tests confirming live gate density flows into the navigation prompt."""

    def test_prompt_includes_congestion_when_provided(self) -> None:
        statuses = simulate_gate_densities(minutes_to_kickoff=30, seed=1)
        gate_name = statuses[0].gate.name
        prompt = build_prompt("Gate A", "Dest", f"near {gate_name}, East", statuses)
        assert "Live crowd data" in prompt

    def test_prompt_omits_congestion_clause_when_absent(self) -> None:
        prompt = build_prompt("Gate A", "Dest", "near Gate Z, Nowhere", None)
        assert "Live crowd data" not in prompt


class TestFallbackNavigation:
    """Tests for the rule-based wayfinding fallback."""

    def test_unresolved_destination_asks_to_check_spelling(self) -> None:
        result = fallback_navigation("Gate A", "Narnia", None)
        assert "not a recognized" in result.lower() or "Narnia" in result

    def test_resolved_destination_mentions_zone(self) -> None:
        result = fallback_navigation("Gate A", "First Aid Station – East", "near Gate A")
        assert "Gate A" in result

    def test_includes_congestion_when_gate_statuses_provided(self) -> None:
        statuses = simulate_gate_densities(minutes_to_kickoff=30, seed=1)
        gate_name = statuses[0].gate.name
        result = fallback_navigation("Gate A", "Dest", f"near {gate_name}", statuses)
        assert gate_name in result
        assert "%" in result


class TestGetDirections:
    """Tests for the main entry point (API mocked)."""

    @patch("src.navigation_assistant._call_genai")
    def test_returns_api_directions_for_valid_destination(self, mock_genai: MagicMock) -> None:
        mock_genai.return_value = "1. Head toward Gate C. 2. Follow signs north."
        result = get_directions("Gate A", "Guest Services Desk")
        assert result["resolved"] is True
        assert "Gate C" in result["directions"] or "north" in result["directions"].lower()
        mock_genai.assert_called_once()

    def test_unresolved_destination_skips_api_call(self) -> None:
        with patch("src.navigation_assistant._call_genai") as mock_genai:
            result = get_directions("Gate A", "Nonexistent Place")
            assert result["resolved"] is False
            mock_genai.assert_not_called()

    @patch("src.navigation_assistant._call_genai", side_effect=RuntimeError("API down"))
    def test_falls_back_on_api_failure(self, mock_genai: MagicMock) -> None:
        result = get_directions("Gate A", "Guest Services Desk")
        assert result["resolved"] is True
        assert isinstance(result["directions"], str)
        assert len(result["directions"]) > 0

    @patch("src.navigation_assistant._call_genai", side_effect=Exception("boom"))
    def test_never_crashes(self, mock_genai: MagicMock) -> None:
        result = get_directions("Gate A", "Guest Services Desk")
        assert isinstance(result, dict)


class TestCallGenaiDelegation:
    """_call_genai should simply delegate to the shared genai_client.generate."""

    @patch("src.navigation_assistant.generate")
    def test_delegates_to_shared_generate(self, mock_generate) -> None:
        mock_generate.return_value = "Head toward Gate C."

        assert _call_genai("some prompt") == "Head toward Gate C."
        mock_generate.assert_called_once_with("some prompt")

    @patch("src.navigation_assistant.generate", side_effect=RuntimeError("empty"))
    def test_propagates_errors(self, _mock_generate) -> None:
        with pytest.raises(RuntimeError):
            _call_genai("some prompt")
