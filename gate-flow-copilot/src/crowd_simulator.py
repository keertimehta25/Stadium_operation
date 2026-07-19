"""Crowd-density simulator for MetLife Stadium gates.

Generates realistic gate-level occupancy percentages (0-100 %) influenced by
time-to-kickoff and a randomised inflow rate.  Fully deterministic when a
seed is provided, making the output reproducible for testing.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

from src.config import DENSITY_LOW, DENSITY_MODERATE, GATES, GateInfo

# ---------------------------------------------------------------------------
# Simulation tuning constants
# ---------------------------------------------------------------------------
# These were previously inline magic numbers; each is named here so the
# model's behavior can be tuned in one place and the intent of each value
# is explicit at the call site rather than only in a comment.
MIN_CROWD_MULTIPLIER = 0.2  # trickle-in rate far before kickoff
MAX_CROWD_MULTIPLIER = 1.0  # peak surge rate right before kickoff
KICKOFF_CURVE_MIDPOINT_MINUTES = 45  # logistic curve center
KICKOFF_CURVE_STEEPNESS = 0.08  # logistic curve steepness
INFLOW_NOISE_SIGMA = 5.0  # std-dev of per-gate random perturbation
MIN_DENSITY_PCT = 0.0
MAX_DENSITY_PCT = 100.0
CAPACITY_BUFFER_FACTOR = 1.2  # headroom applied when scaling by gate capacity
BASE_DENSITY_SCALE = 50.0  # max base density attributable to capacity alone


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class GateStatus:
    """Snapshot of a single gate's current crowd density."""

    gate: GateInfo
    density_pct: float  # 0.0 – 100.0

    @property
    def label(self) -> str:
        """Return a human-readable congestion label."""
        if self.density_pct <= DENSITY_LOW:
            return "Low"
        if self.density_pct <= DENSITY_MODERATE:
            return "Moderate"
        return "High"


# ---------------------------------------------------------------------------
# Core simulation helpers (pure functions, O(1) per gate)
# ---------------------------------------------------------------------------


def _kickoff_multiplier(minutes_to_kickoff: int) -> float:
    """Return a crowd-surge multiplier based on time remaining.

    Fans arrive in a logistic-curve pattern:
      * > 90 min before kickoff → trickle (×0.2)
      * 30-90 min → steady build-up
      * < 30 min → peak surge (×1.0)

    Args:
        minutes_to_kickoff: Minutes remaining before the match starts.
                            Must be non-negative.

    Returns:
        A multiplier in [0.2, 1.0].
    """
    if minutes_to_kickoff <= 0:
        return MAX_CROWD_MULTIPLIER
    # Logistic curve centred at KICKOFF_CURVE_MIDPOINT_MINUTES minutes,
    # steepness factor KICKOFF_CURVE_STEEPNESS
    raw: float = 1.0 / (
        1.0
        + math.exp(KICKOFF_CURVE_STEEPNESS * (minutes_to_kickoff - KICKOFF_CURVE_MIDPOINT_MINUTES))
    )
    return max(MIN_CROWD_MULTIPLIER, min(raw, MAX_CROWD_MULTIPLIER))


def _random_inflow(rng: random.Random, base_density: float) -> float:
    """Add a bounded random perturbation to a base density.

    Args:
        rng: A seeded Random instance for reproducibility.
        base_density: The deterministic baseline density (0-100).

    Returns:
        Perturbed density clamped to [0.0, 100.0].
    """
    noise: float = rng.gauss(mu=0.0, sigma=INFLOW_NOISE_SIGMA)
    return max(MIN_DENSITY_PCT, min(MAX_DENSITY_PCT, base_density + noise))


def _base_density_for_gate(gate: GateInfo) -> float:
    """Derive a gate-specific base density from its capacity.

    Higher-capacity gates tend to run at lower density because they
    process fans faster, while smaller gates congest sooner.

    Args:
        gate: The gate metadata.

    Returns:
        A base density percentage in [0, 100].
    """
    max_capacity: int = max(g.capacity for g in GATES)
    # Inverse relationship: smaller capacity → higher base density
    return BASE_DENSITY_SCALE * (1.0 - gate.capacity / (max_capacity * CAPACITY_BUFFER_FACTOR))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def simulate_gate_densities(
    minutes_to_kickoff: int,
    seed: int | None = None,
) -> list[GateStatus]:
    """Generate a snapshot of crowd density for every stadium gate.

    The simulation combines three factors:
      1. A per-gate base density derived from gate capacity.
      2. A time-based multiplier that models the arrival curve.
      3. A seeded random perturbation for realistic variation.

    Args:
        minutes_to_kickoff: Minutes remaining until kickoff (≥ 0).
        seed: Optional RNG seed for deterministic output.

    Returns:
        A list of ``GateStatus`` objects, one per configured gate.

    Raises:
        ValueError: If ``minutes_to_kickoff`` is negative.
    """
    if minutes_to_kickoff < 0:
        raise ValueError("minutes_to_kickoff must be non-negative")

    rng = random.Random(seed)
    multiplier: float = _kickoff_multiplier(minutes_to_kickoff)

    statuses: list[GateStatus] = []
    for gate in GATES:
        base: float = _base_density_for_gate(gate)
        scaled: float = base + (MAX_DENSITY_PCT - base) * multiplier
        density: float = _random_inflow(rng, scaled)
        statuses.append(GateStatus(gate=gate, density_pct=round(density, 1)))

    return statuses
