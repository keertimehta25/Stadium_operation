"""Sustainability tracker for stadium waste and recycling.

Simulates bin fill-levels across concourse zones and surfaces a
plain-language tip — a lightweight example of the tournament's
sustainability vertical. Rule-based and deterministic when seeded.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

ZONES: tuple[str, ...] = (
    "East Concourse",
    "West Concourse",
    "North Upper",
    "South Upper",
)
BIN_TYPES: tuple[str, ...] = ("Recycling", "Compost", "Landfill")

MIN_SIMULATED_FILL_PCT = 10.0
MAX_SIMULATED_FILL_PCT = 95.0
OVERFLOW_RISK_THRESHOLD_PCT = 80.0


@dataclass(frozen=True)
class BinStatus:
    """Fill-level snapshot for one bin in one zone."""

    zone: str
    bin_type: str
    fill_pct: float


def simulate_bin_levels(seed: int | None = None) -> list[BinStatus]:
    """Simulate current fill levels for every bin type in every zone.

    Args:
        seed: Optional RNG seed for reproducible output.

    Returns:
        A list of BinStatus entries, one per (zone, bin_type) pair.
    """
    rng = random.Random(seed)
    return [
        BinStatus(
            zone=zone,
            bin_type=bin_type,
            fill_pct=round(rng.uniform(MIN_SIMULATED_FILL_PCT, MAX_SIMULATED_FILL_PCT), 1),
        )
        for zone in ZONES
        for bin_type in BIN_TYPES
    ]


def sustainability_tip(statuses: list[BinStatus]) -> str:
    """Generate a plain-language tip based on current bin levels.

    Args:
        statuses: Current bin fill levels.

    Returns:
        A short, actionable tip for venue staff.
    """
    full_bins = [s for s in statuses if s.fill_pct > OVERFLOW_RISK_THRESHOLD_PCT]
    if not full_bins:
        return "All bins are within normal capacity. No action needed."

    worst = max(full_bins, key=lambda s: s.fill_pct)
    return (
        f"{worst.bin_type} bins in {worst.zone} are at {worst.fill_pct:.0f}% "
        "capacity — schedule a pickup before the next rush to avoid overflow."
    )
