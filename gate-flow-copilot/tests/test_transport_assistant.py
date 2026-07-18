"""Unit tests for the transportation assistant — pure logic, no mocking."""

from __future__ import annotations

from src.transport_assistant import recommend_transport


class TestRecommendTransport:
    def test_post_match_recommends_rail(self) -> None:
        result = recommend_transport(minutes_to_kickoff=0, post_match=True)
        assert result["mode"] == "Rail / Transit"

    def test_far_from_kickoff_recommends_drive(self) -> None:
        result = recommend_transport(minutes_to_kickoff=120)
        assert result["mode"] == "Rideshare / Drive"

    def test_close_to_kickoff_recommends_shuttle(self) -> None:
        result = recommend_transport(minutes_to_kickoff=15)
        assert "Shuttle" in result["mode"]

    def test_always_includes_note(self) -> None:
        result = recommend_transport(minutes_to_kickoff=60)
        assert isinstance(result["note"], str) and len(result["note"]) > 0
