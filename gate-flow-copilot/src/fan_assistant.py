"""Fan-facing gate lookup assistant.

Given a fan's seating section, recommends the best entry gate using a
rule-based nearest-gate check against live congestion. This is
deliberately rule-based rather than GenAI-driven: a seat-to-gate
lookup doesn't need open-ended reasoning, so keeping it rule-based
makes it instant, free of API cost, and trivially testable — GenAI is
reserved for the volunteer co-pilot's stadium-wide reasoning in
recommender.py, where the extra flexibility actually earns its cost.
"""

from __future__ import annotations

from src.config import SECTIONS, SectionInfo
from src.crowd_simulator import GateStatus


def _wait_estimate(density_pct: float) -> str:
    """Translate a gate's density percentage into a plain-language wait time.

    Args:
        density_pct: Current gate density (0-100).

    Returns:
        A short human-readable wait-time estimate.
    """
    if density_pct > 70.0:
        return "10-15 min wait"
    if density_pct > 40.0:
        return "3-5 min wait"
    return "No significant wait"


def find_section(section_name: str) -> SectionInfo | None:
    """Look up section metadata by its display name.

    Args:
        section_name: The section identifier as shown in the UI.

    Returns:
        The matching SectionInfo, or None if not recognized.
    """
    for section in SECTIONS:
        if section.section == section_name:
            return section
    return None


def recommend_gate_for_section(section_name: str, gate_statuses: list[GateStatus]) -> dict:
    """Recommend the best entry gate for a fan in a given seating section.

    Checks the section's primary (nearest) gate first. If that gate is
    congested and the alternate gate is not, recommends the alternate
    instead — a short extra walk in exchange for a much shorter wait.

    Args:
        section_name: The fan's seating section, as returned by
            ``find_section``-compatible display names.
        gate_statuses: Current density snapshot for every gate.

    Returns:
        A dict with the recommended gate, zone, density, status, a
        plain-language wait estimate, and the reasoning behind the
        choice. Contains an ``"error"`` key instead if the section or
        its configured gates are not recognized.
    """
    section = find_section(section_name)
    if section is None:
        return {"error": f"Unknown section: {section_name}"}

    by_name = {status.gate.name: status for status in gate_statuses}
    primary = by_name.get(section.primary_gate)
    alternate = by_name.get(section.alternate_gate)

    if primary is None:
        return {"error": f"No live data for configured gate: {section.primary_gate}"}

    chosen: GateStatus = primary
    reason: str = (
        f"{primary.gate.name} is your nearest gate and is currently "
        f"{primary.label.lower()} ({primary.density_pct:.0f}%)."
    )

    if primary.label == "High" and alternate is not None and alternate.label != "High":
        chosen = alternate
        reason = (
            f"{primary.gate.name} (your nearest gate) is congested at "
            f"{primary.density_pct:.0f}%. {alternate.gate.name} is a short walk "
            f"further and currently {alternate.label.lower()} "
            f"({alternate.density_pct:.0f}%)."
        )

    return {
        "section": section_name,
        "gate": chosen.gate.name,
        "zone": chosen.gate.zone,
        "density": chosen.density_pct,
        "status": chosen.label,
        "wait_estimate": _wait_estimate(chosen.density_pct),
        "reason": reason,
    }
