"""Unit tests for the fan-facing gate lookup assistant.

This module is fully rule-based (no GenAI calls), so no mocking is
required — tests exercise the real logic directly.
"""

from __future__ import annotations

import pytest

from src.config import GATES
from src.crowd_simulator import GateStatus
from src.fan_assistant import find_section, recommend_gate_for_section


@pytest.fixture()
def all_low_statuses() -> list[GateStatus]:
    """Every gate comfortably low density."""
    return [GateStatus(gate=g, density_pct=20.0) for g in GATES]


@pytest.fixture()
def gate_a_congested_statuses() -> list[GateStatus]:
    """Gate A (nearest gate for the East Lower section) is congested."""
    statuses = []
    for gate in GATES:
        density = 90.0 if gate.name == "Gate A" else 25.0
        statuses.append(GateStatus(gate=gate, density_pct=density))
    return statuses


class TestFindSection:
    """Tests for section lookup."""

    def test_known_section_found(self) -> None:
        """A configured section name should resolve to its info."""
        section = find_section("100-114 (East Lower)")
        assert section is not None
        assert section.primary_gate == "Gate A"

    def test_unknown_section_returns_none(self) -> None:
        """An unrecognized section name should return None."""
        assert find_section("Nonexistent Section") is None


class TestRecommendGateForSection:
    """Tests for the section-to-gate recommendation logic."""

    def test_unknown_section_returns_error(self, all_low_statuses: list[GateStatus]) -> None:
        """An unrecognized section should produce an error key."""
        result = recommend_gate_for_section("Nowhere", all_low_statuses)
        assert "error" in result

    def test_recommends_primary_gate_when_clear(self, all_low_statuses: list[GateStatus]) -> None:
        """When the nearest gate is clear, it should be recommended as-is."""
        result = recommend_gate_for_section("100-114 (East Lower)", all_low_statuses)
        assert result["gate"] == "Gate A"
        assert "error" not in result

    def test_falls_back_to_alternate_when_primary_congested(
        self, gate_a_congested_statuses: list[GateStatus]
    ) -> None:
        """When the nearest gate is congested, the alternate should be used."""
        result = recommend_gate_for_section("100-114 (East Lower)", gate_a_congested_statuses)
        assert result["gate"] == "Gate E"  # configured alternate for this section
        assert "Gate A" in result["reason"]

    def test_includes_wait_estimate(self, all_low_statuses: list[GateStatus]) -> None:
        """Result should always include a plain-language wait estimate."""
        result = recommend_gate_for_section("200s (Club Level)", all_low_statuses)
        assert "wait_estimate" in result
        assert isinstance(result["wait_estimate"], str)
