"""Unit tests for the crowd_simulator module."""

import pytest

from src.config import GATES
from src.crowd_simulator import (
    GateStatus,
    _base_density_for_gate,
    _kickoff_multiplier,
    simulate_gate_densities,
)


class TestKickoffMultiplier:
    """Tests for the logistic arrival-curve multiplier."""

    def test_at_kickoff_returns_max(self) -> None:
        """At kickoff (0 min), multiplier should be 1.0."""
        assert _kickoff_multiplier(0) == 1.0

    def test_negative_treated_as_kickoff(self) -> None:
        """Negative minutes are clamped to 1.0 inside the function."""
        assert _kickoff_multiplier(-5) == 1.0

    def test_far_out_returns_low(self) -> None:
        """Well before kickoff (120 min), multiplier should be near minimum."""
        result: float = _kickoff_multiplier(120)
        assert result == pytest.approx(0.2, abs=0.05)

    def test_midpoint_reasonable(self) -> None:
        """At 45 min (curve centre), multiplier ≈ 0.5."""
        result: float = _kickoff_multiplier(45)
        assert 0.4 <= result <= 0.6

    def test_monotonically_decreasing(self) -> None:
        """Multiplier should decrease as time-to-kickoff increases."""
        values: list[float] = [_kickoff_multiplier(m) for m in range(0, 121, 10)]
        for i in range(len(values) - 1):
            assert values[i] >= values[i + 1]


class TestBaseDensity:
    """Tests for per-gate base density calculation."""

    def test_smaller_gate_higher_density(self) -> None:
        """A gate with lower capacity should have higher base density."""
        small_gate = min(GATES, key=lambda g: g.capacity)
        large_gate = max(GATES, key=lambda g: g.capacity)
        assert _base_density_for_gate(small_gate) > _base_density_for_gate(large_gate)

    def test_density_in_range(self) -> None:
        """Base densities should be within 0-100."""
        for gate in GATES:
            density: float = _base_density_for_gate(gate)
            assert 0.0 <= density <= 100.0


class TestSimulateGateDensities:
    """Tests for the main simulation function."""

    def test_returns_all_gates(self) -> None:
        """Should return one GateStatus per configured gate."""
        statuses: list[GateStatus] = simulate_gate_densities(30, seed=42)
        assert len(statuses) == len(GATES)

    def test_deterministic_with_seed(self) -> None:
        """Same seed + same inputs → identical output."""
        run_a = simulate_gate_densities(30, seed=123)
        run_b = simulate_gate_densities(30, seed=123)
        for a, b in zip(run_a, run_b):
            assert a.density_pct == b.density_pct

    def test_different_seeds_differ(self) -> None:
        """Different seeds should produce different densities."""
        run_a = simulate_gate_densities(30, seed=1)
        run_b = simulate_gate_densities(30, seed=2)
        densities_a = [s.density_pct for s in run_a]
        densities_b = [s.density_pct for s in run_b]
        assert densities_a != densities_b

    def test_densities_in_bounds(self) -> None:
        """All densities must be in [0, 100]."""
        for seed in range(10):
            statuses = simulate_gate_densities(30, seed=seed)
            for s in statuses:
                assert 0.0 <= s.density_pct <= 100.0

    def test_negative_minutes_raises(self) -> None:
        """Negative minutes_to_kickoff should raise ValueError."""
        with pytest.raises(ValueError, match="non-negative"):
            simulate_gate_densities(-1)

    def test_higher_density_near_kickoff(self) -> None:
        """Average density should be higher near kickoff than far from it."""
        near = simulate_gate_densities(5, seed=42)
        far = simulate_gate_densities(120, seed=42)
        avg_near: float = sum(s.density_pct for s in near) / len(near)
        avg_far: float = sum(s.density_pct for s in far) / len(far)
        assert avg_near > avg_far


class TestGateStatusLabel:
    """Tests for the human-readable congestion label."""

    @pytest.mark.parametrize(
        "density, expected_label",
        [
            (0.0, "Low"),
            (40.0, "Low"),
            (40.1, "Moderate"),
            (70.0, "Moderate"),
            (70.1, "High"),
            (100.0, "High"),
        ],
    )
    def test_label_thresholds(self, density: float, expected_label: str) -> None:
        """Verify label boundaries at exact threshold values."""
        status = GateStatus(gate=GATES[0], density_pct=density)
        assert status.label == expected_label
