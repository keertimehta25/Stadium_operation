"""Unit tests for the sustainability tracker — pure logic, no mocking."""

from __future__ import annotations

from src.sustainibility import BinStatus, simulate_bin_levels, sustainability_tip


class TestSimulateBinLevels:
    def test_same_seed_reproducible(self) -> None:
        a = simulate_bin_levels(seed=5)
        b = simulate_bin_levels(seed=5)
        assert a == b

    def test_covers_every_zone_and_type(self) -> None:
        statuses = simulate_bin_levels(seed=1)
        zones = {s.zone for s in statuses}
        types = {s.bin_type for s in statuses}
        assert len(zones) == 4
        assert len(types) == 3


class TestSustainabilityTip:
    def test_no_full_bins_says_ok(self) -> None:
        statuses = [BinStatus(zone="Z", bin_type="Recycling", fill_pct=30.0)]
        assert "no action needed" in sustainability_tip(statuses).lower()

    def test_full_bin_flagged(self) -> None:
        statuses = [BinStatus(zone="East Concourse", bin_type="Compost", fill_pct=92.0)]
        tip = sustainability_tip(statuses)
        assert "East Concourse" in tip
        assert "Compost" in tip