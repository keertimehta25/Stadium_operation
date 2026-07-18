"""Configuration constants for Gate-Flow Co-Pilot.

Stores stadium metadata, gate definitions, and capacity limits for
MetLife Stadium, New Jersey — a FIFA World Cup 2026 venue.
Loads the GenAI API key securely from environment variables via python-dotenv.
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
load_dotenv()  # reads .env in the project root


# GenAI model used by every assistant module. Centralised so an upgrade
# (e.g. to a newer Gemini version) is a one-line change instead of a
# four-file find-and-replace.
GENAI_MODEL: str = "gemini-2.0-flash"


def get_api_key() -> str:
    """Return the GenAI API key from the environment.

    Raises:
        EnvironmentError: If GENAI_API_KEY is not set or is empty.
    """
    key: str | None = os.getenv("GENAI_API_KEY")
    if not key:
        raise EnvironmentError(
            "GENAI_API_KEY is not set. Copy .env.example to .env and add your key."
        )
    return key


# ---------------------------------------------------------------------------
# Stadium metadata
# ---------------------------------------------------------------------------
STADIUM_NAME: str = "MetLife Stadium, East Rutherford, New Jersey"
STADIUM_CAPACITY: int = 82_500


@dataclass(frozen=True)
class GateInfo:
    """Immutable descriptor for a single stadium entry gate."""

    name: str
    zone: str
    capacity: int  # max fans/hour this gate can process


# MetLife Stadium gates (publicly documented gate zones A–D plus VIP/media).
# Capacities are realistic estimates based on typical NFL/FIFA venue throughput.
GATES: tuple[GateInfo, ...] = (
    GateInfo(name="Gate A", zone="East – Lower Level", capacity=3_000),
    GateInfo(name="Gate B", zone="West – Lower Level", capacity=3_200),
    GateInfo(name="Gate C", zone="North – Upper Level", capacity=2_800),
    GateInfo(name="Gate D", zone="South – Upper Level", capacity=2_800),
    GateInfo(name="Gate E", zone="Northeast – Club", capacity=1_500),
    GateInfo(name="VIP Gate", zone="West – VIP Entrance", capacity=800),
)

GATE_NAMES: tuple[str, ...] = tuple(g.name for g in GATES)

# ---------------------------------------------------------------------------
# Crowd-density thresholds (percentage, 0-100)
# ---------------------------------------------------------------------------
DENSITY_LOW: int = 40  # ≤ 40 % → comfortable
DENSITY_MODERATE: int = 70  # 41-70 % → busy
# > 70 % → congested / redirect fans

# ---------------------------------------------------------------------------
# Supported languages for translated recommendations
# ---------------------------------------------------------------------------
SUPPORTED_LANGUAGES: tuple[str, ...] = ("English", "Spanish", "French")


# ---------------------------------------------------------------------------
# Seating sections — used by the fan-facing gate lookup assistant
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class SectionInfo:
    """Maps a seating section to its nearest primary and backup gate."""

    section: str
    primary_gate: str
    alternate_gate: str


SECTIONS: tuple[SectionInfo, ...] = (
    SectionInfo(section="100-114 (East Lower)", primary_gate="Gate A", alternate_gate="Gate E"),
    SectionInfo(section="115-129 (South Lower)", primary_gate="Gate D", alternate_gate="Gate B"),
    SectionInfo(section="130-144 (West Lower)", primary_gate="Gate B", alternate_gate="Gate D"),
    SectionInfo(section="145-160 (North Lower)", primary_gate="Gate C", alternate_gate="Gate A"),
    SectionInfo(section="200s (Club Level)", primary_gate="Gate E", alternate_gate="Gate A"),
    SectionInfo(section="300s (Upper Level)", primary_gate="Gate C", alternate_gate="Gate D"),
    SectionInfo(section="VIP / Suites", primary_gate="VIP Gate", alternate_gate="Gate E"),
)
