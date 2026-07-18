"""Unit tests for the Flask web dashboard.

All GenAI API calls are mocked — tests run fully offline, matching the
pattern used in test_recommender.py and test_translator.py.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from src.recommender import clear_cache
from src.web import _parse_minutes, app


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    """Ensure a fresh recommendation cache for every test."""
    clear_cache()


@pytest.fixture()
def client():
    """Flask test client with testing mode enabled."""
    app.config.update(TESTING=True)
    with app.test_client() as test_client:
        yield test_client


# ---------------------------------------------------------------------------
# _parse_minutes
# ---------------------------------------------------------------------------


class TestParseMinutes:
    """Tests for clamping the minutes-to-kickoff query parameter."""

    def test_within_range_unchanged(self) -> None:
        """A value already in range should pass through unchanged."""
        assert _parse_minutes(30) == 30

    def test_negative_clamped_to_zero(self) -> None:
        """Negative input should clamp to the minimum."""
        assert _parse_minutes(-15) == 0

    def test_too_large_clamped_to_max(self) -> None:
        """Very large input should clamp to the maximum."""
        assert _parse_minutes(9999) == 240


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


class TestIndexRoute:
    """Tests for the dashboard shell route."""

    def test_index_returns_200(self, client) -> None:
        """The dashboard page should load successfully."""
        response = client.get("/")
        assert response.status_code == 200

    def test_index_mentions_stadium(self, client) -> None:
        """The rendered page should include the stadium name."""
        response = client.get("/")
        assert b"MetLife Stadium" in response.data


class TestApiStatusRoute:
    """Tests for the JSON snapshot API (GenAI calls mocked)."""

    @patch("src.recommender._call_genai", return_value="Redirect to Gate D.")
    @patch("src.translator._translate_text", return_value="Texto traducido.")
    def test_returns_expected_shape(self, mock_translate, mock_genai, client) -> None:
        """Response JSON should include stadium, gates, and translations."""
        response = client.get("/api/status?minutes=15&seed=42")
        assert response.status_code == 200

        payload = response.get_json()
        assert payload["stadium"] == "MetLife Stadium, East Rutherford, New Jersey"
        assert payload["minutes_to_kickoff"] == 15
        assert len(payload["gates"]) == 6
        assert "English" in payload["translations"]

    @patch("src.recommender._call_genai", return_value="All clear.")
    @patch("src.translator._translate_text", return_value="Todo bien.")
    def test_clamps_out_of_range_minutes(self, mock_translate, mock_genai, client) -> None:
        """A minutes value above the max should be clamped, not rejected."""
        response = client.get("/api/status?minutes=99999")
        assert response.status_code == 200
        assert response.get_json()["minutes_to_kickoff"] == 240

    @patch("src.recommender._call_genai", return_value="All clear.")
    @patch("src.translator._translate_text", return_value="Todo bien.")
    def test_seed_gives_reproducible_output(self, mock_translate, mock_genai, client) -> None:
        """Same seed and minutes should yield identical gate densities."""
        first = client.get("/api/status?minutes=20&seed=7").get_json()
        second = client.get("/api/status?minutes=20&seed=7").get_json()
        assert first["gates"] == second["gates"]


class TestApiFanGateRoute:
    """Tests for the fan-facing gate lookup route (no GenAI involved)."""

    def test_valid_section_returns_200(self, client) -> None:
        """A recognized section should return a recommendation."""
        response = client.get("/api/fan-gate?section=100-114 (East Lower)&minutes=30&seed=1")
        assert response.status_code == 200
        payload = response.get_json()
        assert "gate" in payload
        assert "wait_estimate" in payload

    def test_unknown_section_returns_400(self, client) -> None:
        """An unrecognized section should return a 400 with an error key."""
        response = client.get("/api/fan-gate?section=Nowhere")
        assert response.status_code == 400
        assert "error" in response.get_json()


class TestApiSectionsRoute:
    """Tests for the seating-section listing route."""

    def test_returns_list(self, client) -> None:
        response = client.get("/api/sections")
        assert response.status_code == 200
        assert isinstance(response.get_json(), list)
        assert len(response.get_json()) > 0


class TestApiTransportRoute:
    """Tests for the transport recommendation route."""

    def test_returns_200(self, client) -> None:
        response = client.get("/api/transport?minutes=45")
        assert response.status_code == 200

    def test_post_match_flag(self, client) -> None:
        response = client.get("/api/transport?minutes=10&post_match=true")
        assert response.status_code == 200


class TestApiSustainabilityRoute:
    """Tests for the sustainability route."""

    def test_returns_bins_and_tip(self, client) -> None:
        response = client.get("/api/sustainability?seed=3")
        assert response.status_code == 200
        payload = response.get_json()
        assert "bins" in payload
        assert "tip" in payload


class TestApiPoisRoute:
    """Tests for the points-of-interest listing route."""

    def test_returns_all_by_default(self, client) -> None:
        response = client.get("/api/pois")
        assert response.status_code == 200
        assert len(response.get_json()) > 0

    def test_filters_by_category(self, client) -> None:
        response = client.get("/api/pois?category=medical")
        assert response.status_code == 200
        payload = response.get_json()
        assert all(p["category"] == "medical" for p in payload)


class TestApiNavigateRoute:
    """Tests for the navigation route, including live-density wiring."""

    @patch("src.navigation_assistant._call_genai", return_value="Head north.")
    def test_valid_request_returns_200(self, mock_genai, client) -> None:
        response = client.get(
            "/api/navigate?start=Gate A&destination=Guest Services Desk&minutes=30"
        )
        assert response.status_code == 200
        assert response.get_json()["resolved"] is True

    def test_missing_start_returns_400(self, client) -> None:
        response = client.get("/api/navigate?destination=Guest Services Desk")
        assert response.status_code == 400

    def test_missing_destination_returns_400(self, client) -> None:
        response = client.get("/api/navigate?start=Gate A")
        assert response.status_code == 400


class TestApiAccessibilityRoute:
    """Tests for the accessibility Q&A route."""

    @patch("src.accessibility_assistant._call_genai", return_value="Yes, ramp access.")
    def test_valid_question_returns_200(self, mock_genai, client) -> None:
        response = client.post("/api/accessibility", json={"question": "Wheelchair access?"})
        assert response.status_code == 200
        assert "answer" in response.get_json()

    def test_missing_question_returns_400(self, client) -> None:
        response = client.post("/api/accessibility", json={})
        assert response.status_code == 400

    def test_non_json_body_returns_400(self, client) -> None:
        response = client.post("/api/accessibility", data="not json")
        assert response.status_code == 400


class TestErrorHandlers:
    """Tests for clean JSON error responses."""

    def test_404_returns_json(self, client) -> None:
        response = client.get("/api/does-not-exist")
        assert response.status_code == 404
        assert response.get_json() == {"error": "Not found"}


class TestSecurityHeaders:
    """Tests confirming baseline security headers are attached."""

    def test_headers_present_on_response(self, client) -> None:
        response = client.get("/api/sections")
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
